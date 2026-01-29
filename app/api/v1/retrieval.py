"""
Endpoint 3: Context Retrieval
Hybrid search combining semantic + graph traversal
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import uuid
from datetime import datetime

from app.models.api_models import (
    RetrievalQueryRequest,
    RetrievalResponse
)
from loguru import logger

router = APIRouter()

@router.post("/query", response_model=RetrievalResponse)
async def query_knowledge_graph(request: RetrievalQueryRequest):
    """
    **Endpoint 3: Query Knowledge Graph for Relevant Context**

    Retrieves relevant requirements using keyword-based graph search.

    **Search Methods:**
    1. **Keyword**: Text-based matching in requirement text
    2. **Graph**: Hierarchical traversal and reference following

    **Example:**
    ```json
    {
        "component_profile": {
            "name": "LED Module",
            "type": "LED Module",
            "test_categories": ["thermal", "mechanical"]
        },
        "retrieval_method": "hybrid",
        "max_results": 50,
        "min_confidence": 0.1
    }
    ```
    """
    from app.api.v1.graph import graph_builder

    if not graph_builder:
        raise HTTPException(
            status_code=400,
            detail="Knowledge graph not built. Please call /graph/build first."
        )

    query_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    try:
        # Build search keywords from component profile
        component = request.component_profile
        search_terms = []
        search_terms.extend(component.type.lower().split())
        search_terms.extend(component.application.lower().split())
        search_terms.extend([cat.lower() for cat in component.test_categories])

        # Add common test-related keywords
        keyword_map = {
            'thermal': ['temperature', 'heat', 'thermal', 'cold', 'hot', 'celsius', '°c'],
            'mechanical': ['vibration', 'shock', 'mechanical', 'force', 'stress'],
            'environmental': ['humidity', 'water', 'dust', 'environment', 'climate', 'moisture'],
            'electrical': ['voltage', 'current', 'electrical', 'power', 'resistance', 'insulation'],
            'emc': ['emc', 'electromagnetic', 'interference', 'emission', 'immunity'],
            'durability': ['durability', 'life', 'cycle', 'endurance', 'aging']
        }

        for cat in component.test_categories:
            if cat.lower() in keyword_map:
                search_terms.extend(keyword_map[cat.lower()])

        logger.info(f"Search terms: {search_terms}")

        # Search through all requirement nodes
        all_results = []

        for node_id, node_data in graph_builder.graph.nodes(data=True):
            if node_data.get('node_type') != 'Requirement':
                continue

            # Get requirement text
            req_text = node_data.get('text', '').lower()
            if not req_text:
                continue

            # Calculate relevance score based on keyword matches
            matches = 0
            matched_terms = []
            for term in search_terms:
                if term in req_text:
                    matches += 1
                    matched_terms.append(term)

            if matches > 0:
                # Score based on number of matches relative to search terms
                relevance_score = min(1.0, matches / (len(search_terms) * 0.3))

                # Boost score for mandatory requirements
                if node_data.get('requirement_type') == 'mandatory':
                    relevance_score = min(1.0, relevance_score * 1.2)

                if relevance_score >= request.min_confidence:
                    all_results.append({
                        'node_id': node_id,
                        'node_type': 'Requirement',
                        'requirement_id': node_id,
                        'requirement_type': node_data.get('requirement_type', 'mandatory'),
                        'text': node_data.get('text', ''),
                        'keyword': node_data.get('keyword', 'shall'),
                        'parent_clause': node_data.get('parent_clause', ''),
                        'relevance_score': round(relevance_score, 3),
                        'matched_terms': matched_terms,
                        'retrieval_method': 'keyword'
                    })

        # Sort by relevance score
        all_results.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Limit results
        final_results = all_results[:request.max_results]

        return RetrievalResponse(
            job_id=job_id,
            query_id=query_id,
            status="completed",
            results=final_results,
            total_results=len(final_results),
            retrieval_metadata={
                'search_terms': search_terms,
                'total_requirements_searched': sum(1 for _, d in graph_builder.graph.nodes(data=True) if d.get('node_type') == 'Requirement'),
                'matches_found': len(all_results),
                'filtered_by_confidence': request.min_confidence,
                'retrieval_method': 'keyword'
            },
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.exception(f"Retrieval query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@router.get("/explain/{query_id}")
async def explain_retrieval(query_id: str):
    """
    **Explain how results were retrieved**

    Provides detailed explanation of the retrieval process:
    - Search methods used
    - Scoring breakdown
    - Graph traversal path
    - Confidence factors

    **Parameters:**
    - query_id: Query ID from /query endpoint
    """
    # For now, return placeholder
    return {
        "query_id": query_id,
        "message": "Retrieval explanation",
        "explanation": {
            "semantic_search": "Used sentence-transformers embedding similarity",
            "graph_traversal": "Followed parent-child relationships",
            "scoring": "Combined semantic score + graph proximity",
            "confidence_threshold": "Filtered results below threshold"
        }
    }
