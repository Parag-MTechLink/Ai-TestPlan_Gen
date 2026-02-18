"""
Main FastAPI application for Knowledge Graph DVP Generation System
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

from src.config import settings
from src.api.v1 import ingest, graph, retrieval, llm, dvp, visualization
from loguru import logger
import sys
import os

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level
)
logger.add(
    settings.log_file,
    rotation="500 MB",
    retention="10 days",
    level=settings.log_level
)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Knowledge Graph API...")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info(f"Graph storage: {settings.graph_storage_path}")

    # Initialize services
    # Initialize services
    # Run startup automation (Build Graph & Index)
    from src.utils.startup import run_startup_automation
    import src.api.v1.graph as graph_api
    
    builder, engine = run_startup_automation()
    
    if builder:
        # Inject into graph API module
        graph_api.graph_builder = builder
        if engine:
            graph_api.search_engine = engine
        logger.info("Graph API initialized with startup graph.")
    else:
        logger.warning("Startup automation failed or skipped. Graph API will need manual build.")


    yield

    # Cleanup
    logger.info("Shutting down Knowledge Graph API...")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Knowledge Graph API for DVP (Design Verification Plan) Generation

    ## Features
    - Ingest standards documents from external APIs
    - Build multi-layer knowledge graph with traceability
    - Hybrid retrieval (semantic + graph traversal)
    - LLM-powered test procedure generation
    - Automated DVP document generation

    ## Workflow
    1. **Ingest**: Fetch standards from external source
    2. **Build**: Create knowledge graph with links
    3. **Retrieve**: Query relevant requirements
    4. **Generate**: LLM synthesizes test procedures
    5. **Export**: Generate Excel DVP document
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    ingest.router,
    prefix="/api/v1/ingest",
    tags=["Data Ingestion"]
)
app.include_router(
    graph.router,
    prefix="/api/v1/graph",
    tags=["Knowledge Graph"]
)
app.include_router(
    retrieval.router,
    prefix="/api/v1/retrieval",
    tags=["Context Retrieval"]
)
app.include_router(
    llm.router,
    prefix="/api/v1/llm",
    tags=["LLM Generation"]
)
app.include_router(
    dvp.router,
    prefix="/api/v1/dvp",
    tags=["DVP Generation"]
)
app.include_router(
    visualization.router,
    prefix="/api/v1/visualization",
    tags=["Visualization"]
)

# Mount static files
app.mount("/static/output", StaticFiles(directory=settings.output_dir), name="output")
if os.path.exists(settings.input_images_dir):
    app.mount("/static/images", StaticFiles(directory=settings.input_images_dir), name="images")

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Knowledge Graph API for DVP Generation",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )

# Run application
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
