# Knowledge Graph DVP Generation System

A comprehensive automated system for generating Design Verification Plans (DVP) from standards documents. It utilizes Knowledge Graphs, Hybrid Semantic Search (with Reranking), and Generative AI to trace requirements and generate test plans.

## Project Overview

This system ingests technical standard documents (ISO/IEC/Internal), builds a connected Knowledge Graph of requirements, and provides an API to search, query, and generate test plans (DVP) in Excel/Word formats.

**Key Capabilities:**
*   **Knowledge Graph**: Maps relationships between Standards, Clauses, and Requirements.
*   **Hybrid Search**: Combines Keyword Search + Semantic Vector Search + Cross-Encoder Reranking for high-precision retrieval.
*   **Traceability**: Maintains full links from Test Case -> Requirement -> Clause -> Standard.
*   **Automation**: Automatically builds the graph on server startup.

---

## New Feature Highlights

We have recently upgraded the system with optimization features designed to improve performance and usability.

### Instant Startup with Incremental Updates
The system now avoids rebuilding the entire graph upon every restart.
*   **Incremental Processing**: The system tracks processed files and only adds new ones.
*   **Fast Restarts**: Startup time is significantly reduced as it loads the existing graph from disk.
*   **Benefit**: Improved development workflow with faster iteration times.

### Intelligent Data Ingestion
The data handling process has been improved for reliability.
*   **Duplicate Prevention**: Automatically detects previously ingested files to prevent duplicate records.
*   **Seamless Expansion**: New files added to the data folder are integrated into the existing graph without requiring a full rebuild.

### Optimized AI Search
Retrieve relevant information with greater accuracy and efficiency.
*   **Effective Reranking**: A reranking step evaluates search results with a high-precision model to ensure the most relevant matches are prioritized.
*   **Delta Indexing**: The AI model only processes new data, avoiding redundant computations and ensuring scalability.

---

## Project Structure

```
.
├── src/
│   ├── api/v1/                 # API Endpoint Controllers
│   │   ├── ingest.py           # Data Ingestion (JSON/PDF loading)
│   │   ├── graph.py            # Graph Building & Management
│   │   ├── retrieval.py        # Search & Context Retrieval
│   │   ├── llm.py              # GenAI Test Generation
│   │   ├── dvp.py              # DVP Excel/Word Export
│   │   └── visualization.py    # Graph Viz & Statistics
│   ├── core/
│   │   ├── graph_builder.py    # Logic to build NetworkX graph
│   │   ├── semantic_search.py  # Embeddings & Reranking Engine
│   ├── models/                 # Pydantic Data Models
│   ├── utils/                  # Helper scripts (startup.py)
│   ├── config.py               # Application Configuration
│   └── main.py                 # App Entry Point & Lifecycle
├── data/
│   ├── output_json_chunk/      # Source JSON documents (Standards)
│   └── output_images/          # Extracted Images
├── graph_data/                 # Serialized Graph (pkl/json)
├── output/                     # Generated Reports (DVP Excel, PTP Docx)
├── requirements.txt            # Python Dependencies
└── start_server.bat            # Startup Script
```

---

## API Endpoints & Functions

The system runs on **Port 8080** and exposes the following endpoints (Full documentation available at `http://localhost:8080/docs`).

### 1. Ingestion (`/api/v1/ingest`)
*   `POST /local`: Scans `data/output_json_chunk` and prepares data for graph building.
*   `GET /status/{job_id}`: Checks progress of ingestion tasks.

### 2. Graph Management (`/api/v1/graph`)
*   `POST /build`: Triggers the **KnowledgeGraphBuilder** to construct nodes and edges from ingested data.
*   `GET /statistics`: Returns node/edge counts (Standards, Clauses, Requirements).
*   `GET /export`: Exports the current graph to JSON/GEXF.

### 3. Retrieval & Search (`/api/v1/retrieval`)
*   `POST /query`: **Core Search Function**.
    *   **Inputs**: Component Profile (Name, Type), Search Config.
    *   **Process**:
        1.  **Semantic Search**: Finds initial candidates using Vector Embeddings.
        2.  **Keyword Search**: Matches specific terms (thermal, vibration, etc.).
        3.  **Reranking**: Rescores top candidates for better relevance.
    *   **Output**: Top 15 most relevant requirements.

### 4. DVP Generation (`/api/v1/dvp`)
*   `POST /generate`: Takes selected requirements and generates a `DVP.xlsx` file.
*   `POST /generate-ptp`: Generates a `PTP.docx` (Product Test Plan) document.

### 5. LLM Generation (`/api/v1/llm`)
*   `POST /generate`: Uses GenAI to write detailed test procedures for requirements.
*   `POST /generate-simple`: Deterministic generation based on templates.

---

## How to Run

### Prerequisite
*   Python 3.10+ installed.

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the Server (Port 8080)
The system is pre-configured to run on Port 8080.

**Option A (Recommended):**
Run the startup script:
```bash
start_server.bat
```

**Option B (Manual):**
```bash
python -m src.main
```
(Do NOT use `uvicorn src.main:app` without arguments, as it defaults to port 8000).

### Step 3: Access
*   **Swagger API**: [http://localhost:8080/docs](http://localhost:8080/docs)
*   **Query UI**: [http://localhost:8080/api/v1/visualization/query-ui](http://localhost:8080/api/v1/visualization/query-ui)

---

## Configuration
Managed in `src/config.py`. Key settings:
*   `PORT`: 8080
*   `ENABLE_SEMANTIC_SEARCH`: `False` (Default) - Set to `True` for AI search.
*   `ENABLE_RERANKING`: `True` (Default) - Enables Cross-Encoder for better results.
