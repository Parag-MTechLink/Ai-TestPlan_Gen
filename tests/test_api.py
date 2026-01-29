"""
Quick test script for the Knowledge Graph API
Tests the complete end-to-end workflow
"""
import requests
import time
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_complete_workflow():
    """
    Test the complete DVP generation workflow
    """
    print("="*80)
    print("Knowledge Graph DVP Generation - End-to-End Test")
    print("="*80)

    # Step 1: Ingest local data
    print("\n[Step 1/6] Ingesting data from local directory...")
    response = requests.post(f"{BASE_URL}/api/v1/ingest/local")

    if response.status_code != 200:
        print(f"❌ Ingestion failed: {response.text}")
        return

    ingest_data = response.json()
    job_id = ingest_data['job_id']
    print(f"✓ Ingestion job created: {job_id}")

    # Poll for completion
    print("  Waiting for ingestion to complete...")
    max_attempts = 30
    for attempt in range(max_attempts):
        response = requests.get(f"{BASE_URL}/api/v1/ingest/status/{job_id}")
        status_data = response.json()

        if status_data['status'] == 'completed':
            print(f"✓ Ingestion completed: {status_data['result']['files_fetched']} files fetched")
            break
        elif status_data['status'] == 'failed':
            print(f"❌ Ingestion failed: {status_data.get('error')}")
            return

        time.sleep(2)
    else:
        print("❌ Ingestion timeout")
        return

    # Step 2: Build knowledge graph
    print("\n[Step 2/6] Building knowledge graph...")
    response = requests.post(
        f"{BASE_URL}/api/v1/graph/build",
        json={
            "ingestion_job_id": job_id,
            "enable_structural_links": True,
            "enable_semantic_links": True,
            "enable_reference_links": True,
            "semantic_threshold": 0.75
        }
    )

    if response.status_code != 200:
        print(f"❌ Graph building failed: {response.text}")
        return

    graph_data = response.json()
    graph_job_id = graph_data['job_id']
    print(f"✓ Graph building job created: {graph_job_id}")

    # Poll for completion
    print("  Waiting for graph construction...")
    for attempt in range(60):  # Up to 2 minutes
        response = requests.get(f"{BASE_URL}/api/v1/graph/status/{graph_job_id}")
        status_data = response.json()

        if status_data['status'] == 'completed':
            result = status_data['result']
            print(f"✓ Graph built: {result['nodes_created']} nodes, {result['edges_created']} edges")
            break
        elif status_data['status'] == 'failed':
            print(f"❌ Graph building failed: {status_data.get('error')}")
            return

        print(f"  Progress: {status_data['progress_percent']:.1f}% - {status_data['current_step']}")
        time.sleep(2)
    else:
        print("❌ Graph building timeout")
        return

    # Step 3: Query for relevant requirements
    print("\n[Step 3/6] Querying for relevant requirements...")

    component_profile = {
        "name": "W601 Tail Lamp LED Module",
        "type": "LED Module",
        "application": "automotive tail lamp",
        "variants": ["High+", "High"],
        "test_level": "PCB level",
        "applicable_standards": ["BS_EN_50174_3_2013"],
        "test_categories": ["thermal", "mechanical", "environmental"],
        "quantity_per_test": {"RH": 3, "LH": 3}
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/retrieval/query",
        json={
            "component_profile": component_profile,
            "retrieval_method": "hybrid",
            "max_results": 50,
            "min_confidence": 0.7
        }
    )

    if response.status_code != 200:
        print(f"❌ Retrieval failed: {response.text}")
        return

    retrieval_data = response.json()
    print(f"✓ Retrieved {retrieval_data['total_results']} relevant requirements")
    print(f"  Semantic results: {retrieval_data['retrieval_metadata']['semantic_results']}")
    print(f"  Graph results: {retrieval_data['retrieval_metadata']['graph_results']}")

    # Step 4: Generate test procedures with LLM
    print("\n[Step 4/6] Generating test procedures with LLM...")
    response = requests.post(
        f"{BASE_URL}/api/v1/llm/generate",
        json={
            "retrieved_context": retrieval_data['results'][:10],  # Use top 10
            "component_profile": component_profile,
            "generation_mode": "detailed",
            "include_traceability": True
        }
    )

    if response.status_code != 200:
        print(f"❌ LLM generation failed: {response.text}")
        return

    llm_data = response.json()
    print(f"✓ Generated {len(llm_data['test_procedures'])} test procedures")
    print(f"  Tokens used: {llm_data['tokens_used']}")
    print(f"  Generation time: {llm_data['generation_time_seconds']:.2f}s")

    # Step 5: Generate DVP document
    print("\n[Step 5/6] Generating DVP document...")

    test_cases = []
    for proc in llm_data['test_procedures']:
        test_cases.append({
            "test_id": f"B{len(test_cases)+1}",
            "test_standard": proc.get('test_standard', 'ISO 16750-4'),
            "test_description": proc['test_name'],
            "test_procedure": proc['detailed_procedure'],
            "acceptance_criteria": proc.get('acceptance_criteria', 'No damage shall occur'),
            "test_responsibility": "Supplier",
            "test_stage": "DVP",
            "quantity": "3 RH + 3 LH",
            "estimated_days": 5,
            "pcb_or_lamp": component_profile['test_level'],
            "remarks": "",
            "traceability": proc.get('traceability', {})
        })

    response = requests.post(
        f"{BASE_URL}/api/v1/dvp/generate",
        json={
            "component_profile": component_profile,
            "test_cases": test_cases,
            "output_format": "xlsx",
            "include_traceability_sheet": True,
            "include_visualization": False
        }
    )

    if response.status_code != 200:
        print(f"❌ DVP generation failed: {response.text}")
        return

    dvp_data = response.json()
    print(f"✓ DVP generated successfully")
    print(f"  DVP ID: {dvp_data['dvp_id']}")
    print(f"  Test cases: {dvp_data['test_cases_count']}")
    print(f"  Requirements covered: {dvp_data['requirements_covered']}")
    print(f"  File size: {dvp_data['file_size_bytes'] / 1024:.2f} KB")

    # Step 6: Download DVP
    print("\n[Step 6/6] Downloading generated DVP...")
    dvp_id = dvp_data['dvp_id']
    response = requests.get(f"{BASE_URL}/api/v1/dvp/download/{dvp_id}")

    if response.status_code != 200:
        print(f"❌ Download failed: {response.text}")
        return

    output_path = Path("output") / f"Test_{dvp_id}.xlsx"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'wb') as f:
        f.write(response.content)

    print(f"✓ DVP downloaded to: {output_path}")

    print("\n" + "="*80)
    print("✓ Complete workflow test PASSED")
    print("="*80)
    print(f"\nGenerated DVP: {output_path.absolute()}")
    print("You can now open this file in Excel to view the generated test plan.")

if __name__ == "__main__":
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Server is running at {BASE_URL}")
            test_complete_workflow()
        else:
            print(f"❌ Server returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("   Please start the server with: python -m app.main")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
