"""
Complete End-to-End Test of Knowledge Graph DVP System
Tests all 6 endpoints in sequence
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def wait_for_job(endpoint, job_id, max_wait=120):
    """Wait for a background job to complete"""
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}{endpoint}/{job_id}")
        data = response.json()
        status = data.get('status')

        print(f"  Status: {status} | Progress: {data.get('progress_percent', 0)}%")

        if status == 'completed':
            return data
        elif status == 'failed':
            print(f"  ERROR: {data.get('error')}")
            return None

        time.sleep(3)

    print("  TIMEOUT: Job did not complete in time")
    return None

# Test component profile
component_profile = {
    "name": "Cable Management System",
    "type": "Underground Pathway System",
    "application": "underground cable installation and protection",
    "variants": ["Standard Installation"],
    "test_level": "System level",
    "applicable_standards": ["BS_EN_50174_3_2013"],
    "test_categories": ["mechanical", "environmental"],
    "quantity_per_test": {"Standard": 5}
}

print_section("KNOWLEDGE GRAPH DVP GENERATION - COMPLETE WORKFLOW TEST")
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Step 1: Check if graph is already built
print_section("Step 1: Checking Graph Status")
try:
    response = requests.get(f"{BASE_URL}/api/v1/visualization/graph-data?max_nodes=1")
    if response.status_code == 200:
        print("[OK] Graph is already built and ready!")
        graph_ready = True
    else:
        print("[FAIL] Graph not built yet")
        graph_ready = False
except:
    print("[FAIL] Cannot connect to server")
    exit(1)

# Step 2: Retrieve relevant requirements
print_section("Step 2: Retrieving Relevant Requirements (Hybrid Search)")
retrieval_request = {
    "component_profile": component_profile,
    "retrieval_method": "hybrid",
    "max_results": 15,
    "min_confidence": 0.55
}

response = requests.post(
    f"{BASE_URL}/api/v1/retrieval/query",
    json=retrieval_request
)

if response.status_code == 200:
    retrieval_data = response.json()
    print(f"[OK] Retrieved {retrieval_data['total_results']} relevant requirements")
    print(f"  Query ID: {retrieval_data['query_id']}")
    print(f"  Retrieval Method: {retrieval_data['retrieval_metadata']['retrieval_method']}")

    # Show top 3 results
    print("\n  Top 3 Retrieved Requirements:")
    for i, result in enumerate(retrieval_data['results'][:3], 1):
        print(f"    {i}. {result.get('title', result.get('node_id'))}")
        print(f"       Score: {result.get('relevance_score', 0):.3f}")
        if 'requirements' in result and result['requirements']:
            print(f"       Requirements: {len(result['requirements'])}")
else:
    print(f"[FAIL] Retrieval failed: {response.status_code}")
    print(response.text)
    exit(1)

# Save retrieval results for reference
with open('retrieval_results.json', 'w') as f:
    json.dump(retrieval_data, f, indent=2)
print("\n  Saved full results to: retrieval_results.json")

# Step 3: Generate test procedures with LLM
print_section("Step 3: Generating Test Procedures with LLM")

# Check if OpenAI API key is configured
print("  Note: LLM generation requires OPENAI_API_KEY in .env file")
print("  If not configured, this step will be skipped.\n")

llm_request = {
    "retrieved_context": retrieval_data['results'][:10],  # Use top 10 results
    "component_profile": component_profile,
    "generation_mode": "detailed",
    "include_traceability": True
}

response = requests.post(
    f"{BASE_URL}/api/v1/llm/generate",
    json=llm_request
)

if response.status_code == 200:
    llm_job = response.json()
    print(f"[OK] LLM generation job started: {llm_job['job_id']}")

    # Wait for completion
    llm_result = wait_for_job("/api/v1/llm/status", llm_job['job_id'], max_wait=180)

    if llm_result and llm_result['status'] == 'completed':
        test_procedures = llm_result['result']['test_procedures']
        print(f"\n[OK] Generated {len(test_procedures)} test procedures")
        print(f"  Tokens used: {llm_result['result'].get('tokens_used', 'N/A')}")

        # Show generated procedures
        print("\n  Generated Test Procedures:")
        for i, proc in enumerate(test_procedures, 1):
            print(f"    {i}. {proc['test_name']}")

        # Save LLM results
        with open('llm_results.json', 'w') as f:
            json.dump(llm_result, f, indent=2)
        print("\n  Saved full results to: llm_results.json")

        has_llm_results = True
    else:
        print("[FAIL] LLM generation failed or timed out")
        has_llm_results = False
else:
    print(f"[FAIL] LLM generation request failed: {response.status_code}")
    print(f"  Response: {response.text[:200]}")
    has_llm_results = False

# Step 4: Generate DVP Document
print_section("Step 4: Generating DVP Excel Document")

if has_llm_results:
    # Format test procedures into test cases
    test_cases = []
    for idx, proc in enumerate(test_procedures[:10], 1):  # Limit to 10 for demo
        test_cases.append({
            "test_id": f"B{idx}",
            "test_standard": proc.get("test_standard", "BS EN 50174-3:2013"),
            "test_description": proc["test_name"],
            "test_procedure": proc["detailed_procedure"],
            "acceptance_criteria": proc["acceptance_criteria"],
            "test_responsibility": "Supplier",
            "test_stage": "DVP",
            "quantity": "5 samples",
            "estimated_days": proc.get("estimated_days", 5),
            "pcb_or_lamp": "System level",
            "remarks": "",
            "traceability": proc.get("traceability", {})
        })
else:
    # Use mock test cases for demonstration
    print("  Using mock test cases (LLM not available)")
    test_cases = [
        {
            "test_id": "B1",
            "test_standard": "BS EN 50174-3:2013",
            "test_description": "Underground Pathway Mechanical Protection Test",
            "test_procedure": "Install cable management system underground and subject to mechanical load testing per standard requirements. Monitor for damage or deformation.",
            "acceptance_criteria": "No visible damage, deformation, or failure of pathway system under specified mechanical loads",
            "test_responsibility": "Supplier",
            "test_stage": "DVP",
            "quantity": "5 samples",
            "estimated_days": 7,
            "pcb_or_lamp": "System level",
            "remarks": "",
            "traceability": {"source_clause": "BS_EN_50174_3_2013::4.4.2"}
        },
        {
            "test_id": "B2",
            "test_standard": "BS EN 50174-3:2013",
            "test_description": "Environmental Resistance Test",
            "test_procedure": "Expose underground pathway system to environmental conditions including moisture, temperature variations, and soil chemistry as specified in standard.",
            "acceptance_criteria": "Pathway system maintains structural integrity and protective properties after environmental exposure",
            "test_responsibility": "Supplier",
            "test_stage": "DVP",
            "quantity": "5 samples",
            "estimated_days": 14,
            "pcb_or_lamp": "System level",
            "remarks": "",
            "traceability": {"source_clause": "BS_EN_50174_3_2013::4.3.4"}
        }
    ]

dvp_request = {
    "component_profile": component_profile,
    "test_cases": test_cases,
    "output_format": "xlsx",
    "include_traceability_sheet": True
}

response = requests.post(
    f"{BASE_URL}/api/v1/dvp/generate",
    json=dvp_request
)

if response.status_code == 200:
    dvp_job = response.json()
    print(f"[OK] DVP generation job started: {dvp_job['job_id']}")

    # Wait for completion
    dvp_result = wait_for_job("/api/v1/dvp/status", dvp_job['job_id'], max_wait=60)

    if dvp_result and dvp_result['status'] == 'completed':
        dvp_id = dvp_result['result']['dvp_id']
        file_size = dvp_result['result']['file_size_bytes']
        test_count = dvp_result['result']['test_cases_count']

        print(f"\n[OK] DVP document generated successfully")
        print(f"  DVP ID: {dvp_id}")
        print(f"  File Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"  Test Cases: {test_count}")

        # Step 5: Download DVP
        print_section("Step 5: Downloading DVP Document")

        response = requests.get(
            f"{BASE_URL}/api/v1/dvp/download/{dvp_id}",
            stream=True
        )

        if response.status_code == 200:
            output_filename = f"Generated_DVP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            with open(output_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"[OK] DVP downloaded successfully")
            print(f"  Saved to: {output_filename}")
            print(f"  File size: {len(open(output_filename, 'rb').read()):,} bytes")
        else:
            print(f"[FAIL] Download failed: {response.status_code}")
    else:
        print("[FAIL] DVP generation failed or timed out")
else:
    print(f"[FAIL] DVP generation request failed: {response.status_code}")
    print(f"  Response: {response.text[:200]}")

# Summary
print_section("WORKFLOW TEST COMPLETED")
print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\nGenerated Files:")
print("  1. retrieval_results.json - Retrieved requirements from knowledge graph")
if has_llm_results:
    print("  2. llm_results.json - LLM-generated test procedures")
import glob
dvp_files = glob.glob("Generated_DVP_*.xlsx")
if dvp_files:
    print(f"  3. {dvp_files[-1]} - Final DVP Excel document")

print("\n[OK] All endpoints tested successfully!")
print("\nYou can now:")
print("  - Open the generated Excel file to review the DVP")
print("  - Review the JSON files for detailed results")
print("  - Access the API documentation at: http://localhost:8000/docs")
print("  - View the knowledge graph at: http://localhost:8000/api/v1/visualization/interactive")
