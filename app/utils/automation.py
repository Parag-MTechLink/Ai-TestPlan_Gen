import requests
import time
import sys
from loguru import logger

def run_ingestion_workflow(base_url="http://127.0.0.1:8080"):
    """
    Runs the ingestion and graph build workflow.
    1. Wait for server to be ready.
    2. Trigger ingestion.
    3. Poll for completion.
    4. Trigger graph build.
    """
    api_url = f"{base_url}/api/v1"
    
    # 0. Wait for server to be ready
    logger.info(f"Waiting for server at {base_url} to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("Server is ready.")
                break
            else:
                logger.warning(f"Server returned status {response.status_code}. Retrying ({i+1}/{max_retries})...")
        except requests.exceptions.RequestException as e:
            logger.debug(f"Connection attempt {i+1} failed: {e}")
            pass
        time.sleep(2)
    else:
        logger.error("Server did not become ready in time.")
        return

    # 1. Ingest data
    logger.info("Triggering data ingestion...")
    try:
        response = requests.post(f"{api_url}/ingest/local")
        response.raise_for_status()
        data = response.json()
        job_id = data.get("job_id")
        if not job_id:
             # Fallback if job_id is not widely available in the response (adapt based on actual API response)
             # Assuming the API returns job_id. If not, we might need to fetch it differently.
             # But prompt said "take job_id, from 1st command output".
             logger.error(f"Job ID not found in ingestion response: {data}")
             return
        logger.info(f"Ingestion started. Job ID: {job_id}")
    except Exception as e:
        logger.error(f"Failed to trigger ingestion: {e}")
        return

    # 2. Wait for completion
    logger.info(f"Waiting for ingestion job {job_id} to complete...")
    while True:
        try:
            response = requests.get(f"{api_url}/ingest/status/{job_id}")
            response.raise_for_status()
            status_data = response.json()
            status = status_data.get("status")
            
            if status == "completed":
                logger.info("Ingestion completed successfully.")
                break
            elif status == "failed":
                logger.error(f"Ingestion failed: {status_data.get('error')}")
                return
            
            logger.info(f"Current status: {status}. Waiting...")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            time.sleep(2)

    # 3. Build graph
    logger.info("Triggering graph build...")
    payload = {
        "ingestion_job_id": job_id,
        "enable_structural_links": True,
        "enable_semantic_links": False,
        "enable_reference_links": True
    }
    try:
        response = requests.post(
            f"{api_url}/graph/build",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info(f"Graph build triggered successfully. Response: {response.json()}")
    except Exception as e:
        logger.error(f"Failed to trigger graph build: {e}")
        return

    # 4. Wait for graph build completion
    graph_job_id = response.json().get("job_id")
    if not graph_job_id:
        logger.error("Graph build job ID not found.")
        return

    logger.info(f"Waiting for graph build job {graph_job_id} to complete...")
    while True:
        try:
            response = requests.get(f"{api_url}/graph/status/{graph_job_id}")
            response.raise_for_status()
            status_data = response.json()
            status = status_data.get("status")

            if status == "completed":
                logger.info(f"Graph build completed successfully.")
                logger.info(f"Nodes created: {status_data.get('nodes_created')}")
                logger.info(f"Edges created: {status_data.get('edges_created')}")
                break
            elif status == "failed":
                logger.error(f"Graph build failed: {status_data.get('error')}")
                return

            logger.info(f"Graph build status: {status}. Waiting...")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error checking graph build status: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run_ingestion_workflow()
