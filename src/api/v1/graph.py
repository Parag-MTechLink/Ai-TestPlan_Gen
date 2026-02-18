"""
Endpoint 2: Knowledge Graph Construction
Builds multi-layer knowledge graph from ingested documents
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime
from pathlib import Path

from src.models.api_models import (
    GraphBuildResponse,
    JobStatus,
    JobStatusResponse
)
from src.config import settings
from src.core.graph_builder import KnowledgeGraphBuilder
from src.core.semantic_search import SemanticSearchEngine
from loguru import logger

router = APIRouter()

# In-memory job storage
graph_jobs = {}

# Global graph builder and search engine
graph_builder = None
search_engine = None

class GraphBuildRequest(BaseModel):
    """Request to build knowledge graph"""
    ingestion_job_id: str = Field(..., description="Job ID from ingestion")
    enable_structural_links: bool = Field(default=True)
    enable_semantic_links: bool = Field(default=True)
    enable_reference_links: bool = Field(default=True)
    semantic_threshold: float = Field(default=0.75, ge=0.0, le=1.0)

async def process_graph_building(job_id: str, request: GraphBuildRequest):
    """
    Background task to build knowledge graph
    """
    global graph_builder, search_engine

    try:
        graph_jobs[job_id]['status'] = JobStatus.PROCESSING
        graph_jobs[job_id]['current_step'] = 'Initializing graph builder'
        graph_jobs[job_id]['progress_percent'] = 10.0

        # Initialize graph builder
        graph_builder = KnowledgeGraphBuilder(seed=42)

        # Determine data path
        # Try to use ingestion temp path first, fallback to default data dir
        from src.api.v1.ingest import ingestion_jobs

        if request.ingestion_job_id in ingestion_jobs:
            ingest_job = ingestion_jobs[request.ingestion_job_id]
            data_path = ingest_job.get('temp_path', settings.data_dir)
        else:
            data_path = settings.data_dir

        logger.info(f"Building graph from: {data_path}")

        # Phase 1: Build graph structure
        graph_jobs[job_id]['current_step'] = 'Building graph structure'
        graph_jobs[job_id]['progress_percent'] = 20.0

        result = graph_builder.build_from_directory(
            data_path=data_path,
            enable_structural=request.enable_structural_links,
            enable_reference=request.enable_reference_links
        )

        graph_jobs[job_id]['progress_percent'] = 60.0

        # Phase 2: Build semantic index (if enabled)
        if request.enable_semantic_links:
            graph_jobs[job_id]['current_step'] = 'Building semantic index'
            graph_jobs[job_id]['progress_percent'] = 70.0

            search_engine = SemanticSearchEngine(
                model_name=settings.embedding_model,
                vector_db_path=settings.vector_db_path,
                seed=42
            )

            search_engine.index_graph(graph_builder.graph)

            graph_jobs[job_id]['progress_percent'] = 90.0

        # Save graph
        graph_jobs[job_id]['current_step'] = 'Saving graph'
        graph_path = Path(settings.graph_storage_path) / f"{job_id}.pkl"
        graph_builder.save_graph(str(graph_path))

        # Also export as JSON
        json_path = Path(settings.graph_storage_path) / f"{job_id}.json"
        graph_builder.export_json(str(json_path))

        # Update job status
        graph_jobs[job_id]['status'] = JobStatus.COMPLETED
        graph_jobs[job_id]['current_step'] = 'Completed'
        graph_jobs[job_id]['progress_percent'] = 100.0
        graph_jobs[job_id]['result'] = {
            **result,
            'graph_path': str(graph_path),
            'json_path': str(json_path)
        }

        logger.info(f"Graph building job {job_id} completed successfully")

    except Exception as e:
        logger.exception(f"Graph building job {job_id} failed: {e}")
        graph_jobs[job_id]['status'] = JobStatus.FAILED
        graph_jobs[job_id]['error'] = str(e)

# ==================== ENDPOINTS ====================

@router.post("/build", response_model=GraphBuildResponse)
async def build_knowledge_graph(
    request: GraphBuildRequest,
    background_tasks: BackgroundTasks
):
    """
    **Endpoint 2: Build Knowledge Graph**

    Constructs a multi-layer knowledge graph from ingested documents.

    **Process:**
    1. Load JSON documents from ingestion job
    2. Extract nodes (standards, clauses, requirements)
    3. Create structural links (parent-child hierarchy)
    4. Create reference links (citations)
    5. Build semantic index for similarity search
    6. Save graph for querying

    **Parameters:**
    - ingestion_job_id: Job ID from /ingest endpoint
    - enable_structural_links: Build hierarchical relationships
    - enable_semantic_links: Build semantic search index
    - enable_reference_links: Build citation network
    - semantic_threshold: Similarity threshold (0.0-1.0)

    **Returns:**
    - job_id: Track graph building progress
    - Estimated time: 30-60 seconds for 547 documents

    **Example:**
    ```json
    {
        "ingestion_job_id": "abc-123",
        "enable_structural_links": true,
        "enable_semantic_links": true,
        "enable_reference_links": true,
        "semantic_threshold": 0.75
    }
    ```
    """
    job_id = str(uuid.uuid4())

    # Create job entry
    graph_jobs[job_id] = {
        'job_id': job_id,
        'status': JobStatus.PENDING,
        'current_step': 'Initializing',
        'progress_percent': 0.0,
        'created_at': datetime.utcnow()
    }

    # Start background processing
    background_tasks.add_task(
        process_graph_building,
        job_id,
        request
    )

    return GraphBuildResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Graph building started. Use /graph/status/{job_id} to check progress.",
        nodes_created=0,
        edges_created=0,
        graph_checksum="",
        timestamp=datetime.utcnow()
    )

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_graph_status(job_id: str):
    """
    **Check graph building job status**

    **Parameters:**
    - job_id: Job ID from /build endpoint

    **Returns:**
    - Current status and progress
    - Result when completed (nodes, edges, checksum)
    """
    if job_id not in graph_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = graph_jobs[job_id]

    return JobStatusResponse(
        job_id=job_id,
        status=job['status'],
        progress_percent=job.get('progress_percent', 0.0),
        current_step=job.get('current_step', 'Unknown'),
        message=f"Graph building: {job.get('current_step', 'Processing')}",
        result=job.get('result') if job['status'] == JobStatus.COMPLETED else None,
        error=job.get('error')
    )

@router.get("/statistics")
async def get_graph_statistics():
    """
    **Get knowledge graph statistics**

    Returns comprehensive statistics about the current graph:
    - Node counts by type
    - Edge counts by linking method
    - Standards coverage
    - Requirements breakdown

    **Note:** Requires graph to be built first
    """
    global graph_builder

    if not graph_builder:
        raise HTTPException(
            status_code=404,
            detail="No graph has been built yet. Please call /build first."
        )

    stats = graph_builder.get_statistics()

    return {
        "statistics": stats,
        "graph_checksum": graph_builder._compute_checksum(),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/export/{job_id}")
async def export_graph(job_id: str, format: str = "json"):
    """
    **Export knowledge graph in various formats**

    **Parameters:**
    - job_id: Graph building job ID
    - format: Export format (json, graphml, gexf)

    **Returns:**
    - File download
    """
    if job_id not in graph_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = graph_jobs[job_id]
    if job['status'] != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Graph building not completed")

    result = job.get('result', {})
    export_path = result.get('json_path', '')

    if not export_path or not Path(export_path).exists():
        raise HTTPException(status_code=404, detail="Export file not found")

    from fastapi.responses import FileResponse
    return FileResponse(
        path=export_path,
        filename=f"knowledge_graph_{job_id}.json",
        media_type="application/json"
    )

@router.get("/list")
async def list_graph_jobs():
    """
    **List all graph building jobs**

    Returns a list of all graph construction jobs with their status.
    """
    return {
        "total_jobs": len(graph_jobs),
        "jobs": [
            {
                "job_id": job_id,
                "status": job['status'],
                "progress_percent": job.get('progress_percent', 0.0),
                "created_at": job['created_at'].isoformat()
            }
            for job_id, job in graph_jobs.items()
        ]
    }

@router.post("/load/{job_id}")
async def load_existing_graph(job_id: str):
    """
    **Load a previously built graph**

    Loads a saved graph and semantic index into memory for querying.

    **Parameters:**
    - job_id: Previously completed graph building job ID

    **Returns:**
    - Success status and statistics
    """
    global graph_builder, search_engine

    graph_path = Path(settings.graph_storage_path) / f"{job_id}.pkl"

    if not graph_path.exists():
        raise HTTPException(status_code=404, detail=f"Graph file not found for job {job_id}")

    try:
        # Load graph
        graph_builder = KnowledgeGraphBuilder()
        graph_builder.load_graph(str(graph_path))

        # Load semantic search
        search_engine = SemanticSearchEngine(
            model_name=settings.embedding_model,
            vector_db_path=settings.vector_db_path,
            seed=42
        )

        stats = graph_builder.get_statistics()

        return {
            "message": "Graph loaded successfully",
            "job_id": job_id,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.exception(f"Failed to load graph {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load graph: {str(e)}")
