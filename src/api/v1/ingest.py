"""
Endpoint 1: Data Ingestion from External Sources
Fetches standards documents from external API or local files
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from typing import List, Optional
import httpx
import json
import os
from pathlib import Path
import uuid
from datetime import datetime

from src.models.api_models import (
    ExternalDataSourceRequest,
    IngestionResponse,
    JobStatus,
    JobStatusResponse
)
from src.config import settings
from loguru import logger

router = APIRouter()

# In-memory job storage (replace with Redis/DB in production)
ingestion_jobs = {}

# ==================== HELPER FUNCTIONS ====================

async def fetch_from_external_api(source_url: str, api_key: Optional[str], filters: dict) -> List[dict]:
    """
    Fetch standards documents from external API
    """
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.get(
                str(source_url),
                headers=headers,
                params=filters
            )
            response.raise_for_status()
            data = response.json()

            # Assume API returns list of documents
            if isinstance(data, dict) and 'documents' in data:
                return data['documents']
            elif isinstance(data, list):
                return data
            else:
                return [data]

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching from external API: {e}")
            raise HTTPException(status_code=502, detail=f"External API error: {str(e)}")

def load_from_local_directory(data_dir: str) -> List[dict]:
    """
    Load JSON files from local data directory
    """
    documents = []
    data_path = Path(data_dir)

    if not data_path.exists():
        raise HTTPException(status_code=404, detail=f"Data directory not found: {data_dir}")

    # Recursively find all JSON files
    json_files = list(data_path.rglob("*.json"))

    logger.info(f"Found {len(json_files)} JSON files in {data_dir}")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_source_file'] = str(json_file)
                documents.append(data)
        except Exception as e:
            logger.warning(f"Failed to load {json_file}: {e}")
            continue

    return documents

async def process_ingestion_job(job_id: str, source_url: Optional[str], api_key: Optional[str],
                                filters: dict, use_local: bool):
    """
    Background task to process ingestion
    """
    try:
        ingestion_jobs[job_id]['status'] = JobStatus.PROCESSING
        ingestion_jobs[job_id]['current_step'] = 'Fetching documents'

        if use_local:
            # Load from local data directory
            # Prefer input_json_dir if it exists
            source_dir = settings.input_json_dir if Path(settings.input_json_dir).exists() else settings.data_dir
            documents = load_from_local_directory(source_dir)
        else:
            # Fetch from external API
            documents = await fetch_from_external_api(source_url, api_key, filters)

        # Save documents to temp directory
        temp_dir = Path(settings.temp_dir) / job_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        for idx, doc in enumerate(documents):
            doc_id = doc.get('chunk_id', f'doc_{idx}')
            file_path = temp_dir / f"{doc_id.replace('/', '_').replace('::', '_')}.json"

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2)

        # Update job status
        ingestion_jobs[job_id]['status'] = JobStatus.COMPLETED
        ingestion_jobs[job_id]['current_step'] = 'Completed'
        ingestion_jobs[job_id]['files_fetched'] = len(documents)
        ingestion_jobs[job_id]['temp_path'] = str(temp_dir)
        ingestion_jobs[job_id]['progress_percent'] = 100.0

        logger.info(f"Ingestion job {job_id} completed: {len(documents)} documents")

    except Exception as e:
        logger.exception(f"Ingestion job {job_id} failed: {e}")
        ingestion_jobs[job_id]['status'] = JobStatus.FAILED
        ingestion_jobs[job_id]['error'] = str(e)

# ==================== ENDPOINTS ====================

@router.post("/fetch", response_model=IngestionResponse)
async def fetch_external_data(
    request: ExternalDataSourceRequest,
    background_tasks: BackgroundTasks
):
    """
    **Endpoint 1: Fetch standards documents from external API**

    Fetches JSON documents from an external data source and prepares them for knowledge graph construction.

    **Parameters:**
    - source_url: URL of the external API
    - api_key: Optional API key for authentication
    - filters: Optional filters to apply (e.g., document type, year)

    **Returns:**
    - job_id: Unique identifier for tracking this ingestion job
    - status: Current job status (pending, processing, completed, failed)
    - files_fetched: Number of documents retrieved

    **Example:**
    ```json
    {
        "source_url": "https://api.example.com/standards",
        "api_key": "your_key",
        "filters": {"year": 2023}
    }
    ```
    """
    job_id = str(uuid.uuid4())

    # Create job entry
    ingestion_jobs[job_id] = {
        'job_id': job_id,
        'status': JobStatus.PENDING,
        'current_step': 'Initializing',
        'progress_percent': 0.0,
        'files_fetched': 0,
        'created_at': datetime.utcnow()
    }

    # Start background ingestion
    background_tasks.add_task(
        process_ingestion_job,
        job_id,
        request.source_url,
        request.api_key,
        request.filters,
        use_local=False
    )

    return IngestionResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Ingestion job started. Use /ingest/status/{job_id} to check progress.",
        files_fetched=0,
        estimated_time_seconds=30
    )

@router.post("/local", response_model=IngestionResponse)
async def ingest_local_data(background_tasks: BackgroundTasks):
    """
    **Endpoint 1b: Ingest standards documents from local data directory**

    Loads JSON documents from the configured local data directory (./data).
    This is useful for testing and when documents are already available locally.

    **Returns:**
    - job_id: Unique identifier for tracking this ingestion job
    - status: Current job status

    **Note:** Uses the data directory configured in settings (default: ./data)
    """
    job_id = str(uuid.uuid4())

    # Create job entry
    ingestion_jobs[job_id] = {
        'job_id': job_id,
        'status': JobStatus.PENDING,
        'current_step': 'Initializing',
        'progress_percent': 0.0,
        'files_fetched': 0,
        'created_at': datetime.utcnow()
    }

    # Start background ingestion
    background_tasks.add_task(
        process_ingestion_job,
        job_id,
        None,
        None,
        {},
        use_local=True
    )

    return IngestionResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message=f"Ingesting from local directory: {settings.input_json_dir if Path(settings.input_json_dir).exists() else settings.data_dir}",
        files_fetched=0,
        estimated_time_seconds=10
    )

@router.post("/upload", response_model=IngestionResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    **Endpoint 1c: Upload standards documents directly**

    Upload JSON files directly via multipart/form-data.
    Useful for ad-hoc document ingestion.

    **Parameters:**
    - files: List of JSON files to upload

    **Returns:**
    - job_id: Unique identifier for this upload batch
    - files_fetched: Number of files uploaded
    """
    job_id = str(uuid.uuid4())

    temp_dir = Path(settings.temp_dir) / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    uploaded_count = 0

    for file in files:
        if not file.filename.endswith('.json'):
            logger.warning(f"Skipping non-JSON file: {file.filename}")
            continue

        file_path = temp_dir / file.filename

        try:
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)
            uploaded_count += 1
        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {e}")
            continue

    # Create job entry
    ingestion_jobs[job_id] = {
        'job_id': job_id,
        'status': JobStatus.COMPLETED,
        'current_step': 'Completed',
        'progress_percent': 100.0,
        'files_fetched': uploaded_count,
        'temp_path': str(temp_dir),
        'created_at': datetime.utcnow()
    }

    return IngestionResponse(
        job_id=job_id,
        status=JobStatus.COMPLETED,
        message=f"Uploaded {uploaded_count} files successfully",
        files_fetched=uploaded_count
    )

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_ingestion_status(job_id: str):
    """
    **Check status of an ingestion job**

    **Parameters:**
    - job_id: The job ID returned from /fetch, /local, or /upload

    **Returns:**
    - Current job status and progress
    """
    if job_id not in ingestion_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = ingestion_jobs[job_id]

    return JobStatusResponse(
        job_id=job_id,
        status=job['status'],
        progress_percent=job.get('progress_percent', 0.0),
        current_step=job.get('current_step', 'Unknown'),
        message=f"Fetched {job.get('files_fetched', 0)} documents",
        result={
            'files_fetched': job.get('files_fetched', 0),
            'temp_path': job.get('temp_path', '')
        } if job['status'] == JobStatus.COMPLETED else None,
        error=job.get('error')
    )

@router.get("/list")
async def list_ingestion_jobs():
    """
    **List all ingestion jobs**

    Returns a list of all ingestion jobs with their current status.
    """
    return {
        "total_jobs": len(ingestion_jobs),
        "jobs": [
            {
                "job_id": job_id,
                "status": job['status'],
                "files_fetched": job.get('files_fetched', 0),
                "created_at": job['created_at'].isoformat()
            }
            for job_id, job in ingestion_jobs.items()
        ]
    }
