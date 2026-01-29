# Knowledge Graph DVP Generation System

A complete end-to-end API system for automatically generating Design Verification Plans (DVP) from standards documents using knowledge graphs. Built with FastAPI, NetworkX, and modern web technologies.

---

## Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Web Interfaces](#-web-interfaces)
- [API Endpoints](#-api-endpoints)
- [Complete Workflow](#-complete-workflow)
- [Configuration](#-configuration)
- [Local LLM Setup](#-local-llm-setup-optional)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)

---

## Features

- **Knowledge Graph Construction**: Build multi-layer graphs from standards documents (1,290+ nodes, 3,000+ edges)
- **Interactive Query UI**: Web-based interface for querying and exploring the knowledge graph
- **Keyword-Based Search**: Fast requirement retrieval with relevance scoring
- **DVP Excel Generation**: Automated generation of Design Verification Plans
- **Interactive Visualization**: D3.js-powered graph visualization
- **Local LLM Support**: Compatible with LM Studio and other OpenAI-compatible APIs
- **Full Traceability**: Complete requirement-to-test mapping

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Knowledge Graph DVP System                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────┐│
│   │  Ingest  │───▶│  Build   │───▶│  Query   │───▶│   LLM    │───▶│  DVP  ││
│   │   Data   │    │  Graph   │    │  Graph   │    │ Generate │    │ Excel ││
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘    └───────┘│
│        │               │               │               │              │     │
│   547 JSON        1,290 Nodes     Keyword         Test Cases      Excel    │
│   Documents       3,007 Edges     Matching        Generated       Output   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

| Step | Endpoint | Description |
|------|----------|-------------|
| 1 | `POST /api/v1/ingest/local` | Load standards from `./data` directory |
| 2 | `POST /api/v1/graph/build` | Build knowledge graph with nodes & edges |
| 3 | `POST /api/v1/retrieval/query` | Query for relevant requirements |
| 4 | `POST /api/v1/llm/generate` | Generate test procedures (optional) |
| 5 | `POST /api/v1/dvp/generate` | Create Excel DVP document |
| 6 | `GET /api/v1/dvp/download/{id}` | Download generated DVP |

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Required |
| RAM | 8GB+ | Recommended for graph operations |
| Disk Space | 2GB+ | For data and generated files |
| LLM (Optional) | - | OpenAI API or Local LLM (LM Studio) |

---

## Quick Start

### Step 1: Clone/Navigate to Project

```bash
cd "C:\Users\Bramha.nimbalkar\Desktop\knowledge graph"
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Start the Server

```bash
# Option 1: Using uvicorn (recommended)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# Option 2: Using main.py directly
python -m app.main
```

### Step 5: Verify Server is Running

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status": "healthy", "version": "1.0.0", "timestamp": "..."}
```

### Step 6: Build the Knowledge Graph

```bash
# 1. Ingest data
curl -X POST http://localhost:8080/api/v1/ingest/local

# 2. Wait for completion (check status)
curl http://localhost:8080/api/v1/ingest/status/{job_id}

# 3. Build graph (use job_id from step 1)
curl -X POST http://localhost:8080/api/v1/graph/build \
  -H "Content-Type: application/json" \
  -d '{"ingestion_job_id": "{job_id}", "enable_structural_links": true, "enable_semantic_links": false, "enable_reference_links": true}'
```

### Step 7: Open the Query UI

Open in browser: **http://localhost:8080/api/v1/visualization/query-ui**

---

## Web Interfaces

| Interface | URL | Description |
|-----------|-----|-------------|
| **Query UI** | http://localhost:8080/api/v1/visualization/query-ui | Search and explore the knowledge graph |
| **Interactive Graph** | http://localhost:8080/api/v1/visualization/interactive | D3.js graph visualization |
| **Statistics Dashboard** | http://localhost:8080/api/v1/visualization/statistics-visual | Graph statistics with charts |
| **Swagger API Docs** | http://localhost:8080/docs | Interactive API documentation |
| **ReDoc** | http://localhost:8080/redoc | Alternative API documentation |

### Query UI Features

The Query UI (`/api/v1/visualization/query-ui`) provides:

- **Query Parameters Panel**: Set component name, type, application, test level
- **Test Category Selection**: Thermal, Mechanical, Environmental, Electrical, EMC, Durability
- **Confidence Filter**: Slider to filter by minimum relevance score
- **Three Tabs**:
  - **Query Results**: View matching requirements with relevance scores
  - **All Nodes**: Browse all 1,290 nodes with search & filter
  - **Graph View**: Mini D3.js visualization of results
- **Export to Excel**: Generate DVP Excel from query results

---

## API Endpoints

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| GET | `/docs` | Swagger API documentation |

### Data Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ingest/local` | Ingest from local `./data` directory |
| POST | `/api/v1/ingest/external` | Ingest from external API |
| POST | `/api/v1/ingest/upload` | Upload files directly |
| GET | `/api/v1/ingest/status/{job_id}` | Check ingestion status |

### Knowledge Graph

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/graph/build` | Build knowledge graph |
| GET | `/api/v1/graph/status/{job_id}` | Check build status |

### Retrieval

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/retrieval/query` | Query for requirements |
| GET | `/api/v1/retrieval/explain/{query_id}` | Explain retrieval results |

### LLM Generation (Requires LLM)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/llm/generate` | Generate test procedures |
| POST | `/api/v1/llm/generate-simple` | Simple single procedure generation |
| GET | `/api/v1/llm/status/{job_id}` | Check generation status |

### DVP Document

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/dvp/generate` | Generate DVP Excel |
| GET | `/api/v1/dvp/download/{dvp_id}` | Download DVP file |
| GET | `/api/v1/dvp/list` | List all generated DVPs |
| DELETE | `/api/v1/dvp/delete/{dvp_id}` | Delete a DVP |

### Visualization

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/visualization/query-ui` | Interactive Query Interface |
| GET | `/api/v1/visualization/interactive` | D3.js Graph Visualization |
| GET | `/api/v1/visualization/graph-data` | Get graph data as JSON |
| GET | `/api/v1/visualization/statistics-visual` | Statistics Dashboard |

---

## Complete Workflow

### Using cURL Commands

```bash
# Step 1: Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# Step 2: Ingest data
curl -X POST http://localhost:8080/api/v1/ingest/local
# Response: {"job_id": "abc-123", "status": "pending", ...}

# Step 3: Wait for ingestion (poll status)
curl http://localhost:8080/api/v1/ingest/status/abc-123
# Wait until status is "completed"

# Step 4: Build knowledge graph
curl -X POST http://localhost:8080/api/v1/graph/build \
  -H "Content-Type: application/json" \
  -d '{
    "ingestion_job_id": "abc-123",
    "enable_structural_links": true,
    "enable_semantic_links": false,
    "enable_reference_links": true
  }'

# Step 5: Wait for graph build
curl http://localhost:8080/api/v1/graph/status/{graph_job_id}
# Wait until status is "completed"

# Step 6: Query the graph
curl -X POST http://localhost:8080/api/v1/retrieval/query \
  -H "Content-Type: application/json" \
  -d '{
    "component_profile": {
      "name": "LED Module",
      "type": "LED Module",
      "application": "automotive lighting",
      "variants": ["High", "Low"],
      "test_level": "PCB level",
      "applicable_standards": ["ISO 16750"],
      "test_categories": ["thermal", "electrical"],
      "quantity_per_test": {"Sample": 5}
    },
    "retrieval_method": "hybrid",
    "max_results": 20,
    "min_confidence": 0.2
  }'

# Step 7: Generate DVP Excel (with test cases from query)
curl -X POST http://localhost:8080/api/v1/dvp/generate \
  -H "Content-Type: application/json" \
  -d '{
    "component_profile": {...},
    "test_cases": [...],
    "output_format": "xlsx",
    "include_traceability_sheet": true
  }'

# Step 8: Download DVP
curl http://localhost:8080/api/v1/dvp/download/{dvp_id} --output DVP_Output.xlsx
```

### Using the Query UI (Recommended)

1. Open **http://localhost:8080/api/v1/visualization/query-ui**
2. Fill in component details (name, type, application)
3. Select test categories (thermal, mechanical, electrical, etc.)
4. Adjust max results and confidence threshold
5. Click **"Query Knowledge Graph"**
6. Review results in the table
7. Click **"Export to Excel"** to generate DVP

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# API Settings
APP_NAME=Knowledge Graph API
HOST=0.0.0.0
PORT=8080
DEBUG=true

# Data Paths
DATA_DIR=./data
GRAPH_STORAGE_PATH=./graph_data
VECTOR_DB_PATH=./chroma_db
OUTPUT_DIR=./output

# LLM Configuration (Optional - for test procedure generation)
OPENAI_API_KEY=not-needed
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_MODEL=qwen/qwen3-vl-4b
OPENAI_TEMPERATURE=0.2
OPENAI_MAX_TOKENS=4096

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### Config File Location

Configuration is managed in `app/config.py`:

```python
class Settings(BaseSettings):
    openai_api_key: Optional[str] = "not-needed"
    openai_api_base: str = "http://172.21.224.1:1234/v1"
    openai_model: str = "qwen/qwen3-vl-4b"
    # ... other settings
```

---

## Local LLM Setup (Optional)

The system supports local LLMs via OpenAI-compatible APIs (e.g., LM Studio).

### Using LM Studio

1. **Install LM Studio**: Download from https://lmstudio.ai/
2. **Load a Model**: Download and load a model (e.g., `qwen/qwen3-vl-4b`)
3. **Start Local Server**:
   - Go to "Local Server" tab
   - Set host to `0.0.0.0` (for network access)
   - Start server on port `1234`
4. **Update Config**: Set `openai_api_base` in `app/config.py`:
   ```python
   openai_api_base: str = "http://localhost:1234/v1"
   ```

### Verify LLM Connection

```bash
curl http://localhost:1234/v1/models
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `Port 8080 already in use` | Kill existing process: `netstat -ano \| findstr :8080` then `taskkill //F //PID {pid}` |
| `Knowledge graph not built` | Run ingestion and graph build before querying |
| `No results found` | Lower the `min_confidence` threshold (try 0.1 or 0.2) |
| `LLM connection failed` | Check LM Studio is running and accessible |
| `ModuleNotFoundError` | Ensure virtual environment is activated |

### Check Server Status

```bash
# Health check
curl http://localhost:8080/health

# Check if graph is built
curl http://localhost:8080/api/v1/visualization/graph-data?max_nodes=5
```

### View Server Logs

Server logs are output to the console. Check for errors during startup.

### Clear and Restart

```bash
# Stop all Python processes
taskkill //F //IM python.exe

# Clear cache (optional)
rmdir /s /q __pycache__
rmdir /s /q app\__pycache__

# Restart server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## Project Structure

```
knowledge graph/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration management
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── ingest.py          # Data ingestion endpoints
│   │       ├── graph.py           # Graph building endpoints
│   │       ├── retrieval.py       # Query/search endpoints
│   │       ├── llm.py             # LLM generation endpoints
│   │       ├── dvp.py             # DVP generation endpoints
│   │       └── visualization.py   # Visualization & Query UI
│   ├── core/
│   │   ├── __init__.py
│   │   ├── graph_builder.py       # Knowledge graph construction
│   │   └── semantic_search.py     # Search engine
│   ├── models/
│   │   ├── __init__.py
│   │   └── api_models.py          # Pydantic data models
│   └── utils/
│       └── __init__.py
├── data/                          # Standards documents (547 JSON files)
│   ├── BS_EN_50174_3_2013/
│   ├── IEC_61076_8_103_2023/
│   └── IS17017_Part2_Sec2_2020/
├── graph_data/                    # Serialized graph storage
├── chroma_db/                     # Vector database (if used)
├── output/                        # Generated DVP Excel files
├── temp/                          # Temporary ingestion files
├── logs/                          # Application logs
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables
└── README.md                      # This file
```

---

## Graph Statistics

After building the knowledge graph:

| Metric | Value |
|--------|-------|
| Total Nodes | 1,290 |
| Total Edges | 3,007 |
| Standards | 3 |
| Clauses | 547 |
| Requirements | 558 |

### Node Types

| Type | Color | Description |
|------|-------|-------------|
| Standard | Red | Top-level standard documents |
| Clause | Teal | Sections within standards |
| Requirement | Blue | Individual requirements (shall/should) |
| External Standard | Orange | Referenced external standards |

### Edge Types

| Type | Description |
|------|-------------|
| CONTAINS_CLAUSE | Standard → Clause relationship |
| CONTAINS_REQUIREMENT | Clause → Requirement relationship |
| SIBLING_OF | Clauses at same level |
| REFERENCES | Cross-references between documents |

---

## Test Categories

The system supports the following test categories for querying:

| Category | Keywords Searched |
|----------|-------------------|
| `thermal` | temperature, heat, thermal, cold, hot, celsius, °c |
| `mechanical` | vibration, shock, mechanical, force, stress |
| `environmental` | humidity, water, dust, environment, climate, moisture |
| `electrical` | voltage, current, electrical, power, resistance, insulation |
| `emc` | emc, electromagnetic, interference, emission, immunity |
| `durability` | durability, life, cycle, endurance, aging |

---

## Generated DVP Structure

The Excel DVP contains 4 sheets:

1. **Annex B - Electronics DVP**: Main test matrix
   - Sl.No., Test Standard, Test Description, Test Procedure
   - Acceptance Criteria, Test Responsibility, Test Stage
   - Qty, Test Days, Start/End Date, Test Inference, Remarks

2. **EMC & ENV TEST SEQUENCE**: Test sequence grouping

3. **Traceability Matrix**: Requirement → Test mapping
   - Test ID, Test Description, Requirement ID
   - Source Clause, Source Standard, Confidence Score

4. **Source References**: List of all referenced standards and clauses

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review server logs for error messages
3. Ensure all prerequisites are installed
4. Verify the knowledge graph is built before querying

---

**Knowledge Graph DVP Generation System v1.0.0**
