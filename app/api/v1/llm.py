"""
Endpoint 4: LLM Generation Service
Synthesizes test procedures and acceptance criteria using LLM
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import uuid
from datetime import datetime
import json

from app.models.api_models import (
    LLMGenerationRequest,
    LLMGenerationResponse,
    JobStatus,
    JobStatusResponse
)
from app.config import settings
from loguru import logger

router = APIRouter()

# In-memory job storage
llm_jobs = {}

# LLM Client (will initialize when needed)
llm_client = None

def get_llm_client():
    """Get or create LLM client - supports local models via OpenAI-compatible API"""
    global llm_client
    if llm_client is None:
        from openai import OpenAI
        # Use local LLM server (OpenAI-compatible API)
        llm_client = OpenAI(
            api_key=settings.openai_api_key or "not-needed",
            base_url=settings.openai_api_base  # Local model endpoint
        )
        logger.info(f"LLM client initialized with base_url: {settings.openai_api_base}, model: {settings.openai_model}")
    return llm_client

def generate_test_procedure_prompt(requirement: Dict[str, Any],
                                   component_profile: Dict[str, Any]) -> str:
    """
    Generate prompt for test procedure creation
    """
    prompt = f"""You are a test engineer creating a Design Verification Plan (DVP) for automotive components.

Component Under Test:
- Name: {component_profile.get('name', 'Component')}
- Type: {component_profile.get('type', 'Unknown')}
- Application: {component_profile.get('application', 'Unknown')}
- Test Level: {component_profile.get('test_level', 'Unknown')}

Requirement Information:
{json.dumps(requirement, indent=2)}

Based on this requirement, generate a detailed test procedure in the following JSON format:
{{
    "test_name": "Brief descriptive name (e.g., Operation at Low Temperature)",
    "test_description": "1-2 sentence description",
    "test_standard": "Source standard (e.g., ISO 16750-4)",
    "detailed_procedure": "Step-by-step test procedure with specific parameters. Include temperature, duration, operating mode, etc.",
    "test_parameters": {{
        "temperature": "value if applicable",
        "duration": "value if applicable",
        "cycles": "value if applicable"
    }},
    "operating_mode": "Operating mode description if applicable",
    "acceptance_criteria": "Clear pass/fail criteria based on requirement",
    "estimated_days": 5,
    "traceability": {{
        "requirement_id": "{requirement.get('requirement_id', '')}",
        "source_clause": "{requirement.get('clause_id', '')}",
        "source_standard": "{requirement.get('document_id', '')}"
    }}
}}

Generate a realistic and detailed test procedure that follows automotive industry standards."""

    return prompt

async def process_llm_generation(job_id: str, request: LLMGenerationRequest):
    """
    Background task for LLM generation
    """
    try:
        llm_jobs[job_id]['status'] = JobStatus.PROCESSING
        llm_jobs[job_id]['current_step'] = 'Initializing LLM client'

        client = get_llm_client()

        test_procedures = []
        acceptance_criteria = []
        total_tokens = 0

        # Process top results
        results_to_process = request.retrieved_context[:10]  # Limit for cost control

        llm_jobs[job_id]['current_step'] = f'Generating test procedures (0/{len(results_to_process)})'

        for idx, result in enumerate(results_to_process):
            try:
                # Generate prompt
                prompt = generate_test_procedure_prompt(
                    result,
                    request.component_profile.model_dump()
                )

                # Call LLM (local model - may not support response_format)
                response = client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": "You are an expert automotive test engineer. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=settings.openai_temperature,
                    max_tokens=settings.openai_max_tokens
                )

                # Parse response - handle potential non-JSON content from local models
                content = response.choices[0].message.content
                # Try to extract JSON from the response
                try:
                    procedure_data = json.loads(content)
                except json.JSONDecodeError:
                    # Try to find JSON in the response
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        procedure_data = json.loads(json_match.group())
                    else:
                        logger.warning(f"Could not parse JSON from LLM response: {content[:200]}")
                        continue

                # Add source information
                procedure_data['source_requirement'] = result.get('requirement_id', result.get('node_id', ''))
                procedure_data['confidence_score'] = result.get('relevance_score', 0.0)

                test_procedures.append(procedure_data)

                # Extract acceptance criteria
                if 'acceptance_criteria' in procedure_data:
                    acceptance_criteria.append({
                        'criteria_id': f"AC_{idx+1}",
                        'test_id': f"B{idx+1}",
                        'criteria_text': procedure_data['acceptance_criteria'],
                        'source_requirement': procedure_data['source_requirement']
                    })

                # Count tokens
                total_tokens += response.usage.total_tokens

                # Update progress
                llm_jobs[job_id]['current_step'] = f'Generating test procedures ({idx+1}/{len(results_to_process)})'
                llm_jobs[job_id]['progress_percent'] = 20.0 + (70.0 * (idx+1) / len(results_to_process))

                logger.info(f"Generated test procedure {idx+1}/{len(results_to_process)}")

            except Exception as e:
                logger.error(f"Failed to generate procedure for result {idx}: {e}")
                continue

        # Update job status
        llm_jobs[job_id]['status'] = JobStatus.COMPLETED
        llm_jobs[job_id]['current_step'] = 'Completed'
        llm_jobs[job_id]['progress_percent'] = 100.0
        llm_jobs[job_id]['result'] = {
            'test_procedures': test_procedures,
            'acceptance_criteria': acceptance_criteria,
            'tokens_used': total_tokens,
            'procedures_generated': len(test_procedures)
        }

        logger.info(f"LLM generation job {job_id} completed: {len(test_procedures)} procedures")

    except Exception as e:
        logger.exception(f"LLM generation job {job_id} failed: {e}")
        llm_jobs[job_id]['status'] = JobStatus.FAILED
        llm_jobs[job_id]['error'] = str(e)

# ==================== ENDPOINTS ====================

@router.post("/generate", response_model=LLMGenerationResponse)
async def generate_test_procedures(
    request: LLMGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    **Endpoint 4: Generate Test Procedures with LLM**

    Uses OpenAI GPT to synthesize detailed test procedures from requirements.

    **Process:**
    1. Take retrieved requirements/clauses
    2. Generate detailed test procedure for each
    3. Extract test parameters (temperature, duration, etc.)
    4. Generate acceptance criteria
    5. Map to component specifications
    6. Maintain traceability chain

    **LLM Configuration:**
    - Model: GPT-4-turbo (configurable)
    - Temperature: 0.2 (for consistency)
    - Output: Structured JSON

    **Cost Estimation:**
    - ~1000 tokens per test procedure
    - 10 procedures = ~$0.20 (GPT-4-turbo pricing)

    **Example:**
    ```json
    {
        "retrieved_context": [...],
        "component_profile": {...},
        "generation_mode": "detailed",
        "include_traceability": true
    }
    ```

    **Returns:**
    - Test procedures with detailed steps
    - Acceptance criteria
    - Token usage and cost
    """
    # Local model configured - no API key needed
    if not settings.openai_api_base:
        raise HTTPException(
            status_code=500,
            detail="LLM API base URL not configured. Set openai_api_base in config."
        )

    job_id = str(uuid.uuid4())

    # Create job entry
    llm_jobs[job_id] = {
        'job_id': job_id,
        'status': JobStatus.PENDING,
        'current_step': 'Initializing',
        'progress_percent': 0.0,
        'created_at': datetime.utcnow()
    }

    # Start background processing
    background_tasks.add_task(
        process_llm_generation,
        job_id,
        request
    )

    return LLMGenerationResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        test_procedures=[],
        acceptance_criteria=[],
        tokens_used=0,
        generation_time_seconds=0.0,
        timestamp=datetime.utcnow()
    )

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_llm_generation_status(job_id: str):
    """
    **Check LLM generation job status**

    **Parameters:**
    - job_id: Job ID from /generate endpoint

    **Returns:**
    - Current status and progress
    - Result when completed (test procedures, tokens used)
    """
    if job_id not in llm_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = llm_jobs[job_id]

    return JobStatusResponse(
        job_id=job_id,
        status=job['status'],
        progress_percent=job.get('progress_percent', 0.0),
        current_step=job.get('current_step', 'Unknown'),
        message=f"LLM generation: {job.get('current_step', 'Processing')}",
        result=job.get('result') if job['status'] == JobStatus.COMPLETED else None,
        error=job.get('error')
    )

@router.post("/generate-simple")
async def generate_simple_test_procedure(
    requirement_text: str,
    component_type: str,
    test_category: str
):
    """
    **Simple test procedure generation (synchronous)**

    Quick endpoint for generating a single test procedure.
    Useful for testing or interactive use.

    **Parameters:**
    - requirement_text: The requirement text
    - component_type: Type of component
    - test_category: Test category (thermal, mechanical, etc.)

    **Returns:**
    - Generated test procedure (immediate response)
    """
    # Local model configured - no API key needed
    if not settings.openai_api_base:
        raise HTTPException(
            status_code=500,
            detail="LLM API base URL not configured"
        )

    try:
        client = get_llm_client()

        prompt = f"""Generate a test procedure for:

Component: {component_type}
Test Category: {test_category}
Requirement: {requirement_text}

Provide a JSON response with:
- test_name
- test_description
- detailed_procedure
- acceptance_criteria"""

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an automotive test engineer. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )

        content = response.choices[0].message.content
        # Try to extract JSON from the response
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON from response: {content[:200]}")

        return {
            "test_procedure": result,
            "tokens_used": response.usage.total_tokens,
            "model": settings.openai_model
        }

    except Exception as e:
        logger.exception(f"Simple generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
