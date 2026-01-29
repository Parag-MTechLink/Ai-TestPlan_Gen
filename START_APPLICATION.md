# How to Start the Knowledge Graph Application

## Quick Start

### Option 1: Start the Server (if not running)

```bash
cd "C:\Users\Bramha.nimbalkar\Desktop\knowledge graph"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Run in Background

```bash
cd "C:\Users\Bramha.nimbalkar\Desktop\knowledge graph"
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

### Option 3: Use the main.py directly

```bash
cd "C:\Users\Bramha.nimbalkar\Desktop\knowledge graph"
python app/main.py
```

## Check if Server is Running

```bash
# Method 1: Check health endpoint
curl http://localhost:8000/health

# Method 2: Check with browser
# Open: http://localhost:8000/health
```

## Access the Application

Once the server is running, you can access:

### 1. Interactive API Documentation (Swagger UI)
**URL:** http://localhost:8000/docs

Features:
- Try out all API endpoints
- See request/response schemas
- Test queries directly in browser

### 2. Alternative API Documentation (ReDoc)
**URL:** http://localhost:8000/redoc

Features:
- Clean documentation interface
- Detailed schema descriptions
- Example requests/responses

### 3. Knowledge Graph Visualization
**URL:** http://localhost:8000/api/v1/visualization/interactive

Features:
- Interactive D3.js graph
- Filter by node type
- Search functionality
- Click nodes for details

### 4. Health Check
**URL:** http://localhost:8000/health

Returns:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-23T16:00:00.000000"
}
```

### 5. Root Endpoint
**URL:** http://localhost:8000/

Returns API information and links.

## Common Commands

### Check Server Status
```bash
curl http://localhost:8000/health | python -m json.tool
```

### Test Retrieval
```bash
curl -X POST http://localhost:8000/api/v1/retrieval/query \
  -H "Content-Type: application/json" \
  -d '{
    "component_profile": {
      "name": "Test Component",
      "type": "Cable System",
      "application": "underground cable installation",
      "variants": ["Standard"],
      "test_level": "System level",
      "applicable_standards": ["BS_EN_50174_3_2013"],
      "test_categories": ["mechanical"],
      "quantity_per_test": {"Standard": 5}
    },
    "retrieval_method": "hybrid",
    "max_results": 10
  }' | python -m json.tool
```

### Run Complete Workflow Test
```bash
cd "C:\Users\Bramha.nimbalkar\Desktop\knowledge graph"
python tests/test_complete_workflow.py
```

### Run Accuracy Evaluation
```bash
cd "C:\Users\Bramha.nimbalkar\Desktop\knowledge graph"
python accuracy_evaluation.py
```

## Stopping the Server

### If running in foreground (terminal):
Press `Ctrl+C`

### If running in background:
```bash
# Find the process
ps aux | grep uvicorn

# Kill the process (replace PID with actual process ID)
kill <PID>

# Or force kill
kill -9 <PID>
```

### On Windows:
```bash
# Find the process
tasklist | findstr python

# Kill the process
taskkill /PID <PID> /F
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add:

```env
# API Settings
APP_NAME="Knowledge Graph API"
APP_VERSION="1.0.0"
HOST="0.0.0.0"
PORT=8000
DEBUG=true

# LLM Configuration (optional - for test generation)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Paths
DATA_DIR=./data
GRAPH_STORAGE_PATH=./graph_data
VECTOR_DB_PATH=./chroma_db

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

## Troubleshooting

### Port Already in Use

**Error:** `Address already in use`

**Solution 1:** Use a different port
```bash
python -m uvicorn app.main:app --port 8001
```

**Solution 2:** Kill the existing process
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill <PID>
```

### Module Not Found

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:** Make sure you're in the project root directory
```bash
cd "C:\Users\Bramha.nimbalkar\Desktop\knowledge graph"
python -m uvicorn app.main:app --reload
```

### Knowledge Graph Not Built

**Error:** `Knowledge graph not built. Please call /graph/build first.`

**Solution:** Build the graph first
```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/ingest/local
# Wait for ingestion to complete, then:
curl -X POST http://localhost:8000/api/v1/graph/build \
  -H "Content-Type: application/json" \
  -d '{"ingestion_job_id": "<job_id_from_ingestion>"}'

# Or use the test script
python tests/test_complete_workflow.py
```

### OpenAI API Error

**Error:** `OpenAI API key not configured`

**Solution:** This is optional. If you don't need LLM-generated test procedures:
- System will use mock test cases
- DVP generation still works

If you want LLM features:
1. Get API key from https://platform.openai.com/
2. Add to `.env` file: `OPENAI_API_KEY=sk-...`
3. Restart server

## Performance Tips

### 1. Increase Workers (Production)
```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### 2. Use Production ASGI Server (Gunicorn)
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 3. Enable Production Mode
Edit `.env`:
```env
DEBUG=false
```

## Monitoring

### View Logs
```bash
# Real-time log monitoring
tail -f logs/app.log

# Last 50 lines
tail -n 50 logs/app.log

# Search logs
grep "ERROR" logs/app.log
```

### Check System Resources
```bash
# CPU and memory usage
top -p $(pgrep -f uvicorn)

# On Windows
tasklist | findstr python
```

## Development Mode vs Production Mode

### Development Mode (current)
```bash
python -m uvicorn app.main:app --reload
```
- Auto-reloads on code changes
- Debug mode enabled
- Detailed error messages
- Single worker

### Production Mode
```bash
uvicorn app.main:app --workers 4 --no-access-log
```
- No auto-reload
- Debug mode disabled
- Minimal error details
- Multiple workers
- Better performance

## Quick Reference

| Task | Command |
|------|---------|
| Start server | `python -m uvicorn app.main:app --reload` |
| Check health | `curl http://localhost:8000/health` |
| View API docs | Open http://localhost:8000/docs |
| Run tests | `python tests/test_complete_workflow.py` |
| Check accuracy | `python accuracy_evaluation.py` |
| View logs | `tail -f logs/app.log` |
| Stop server | `Ctrl+C` (if foreground) |

## Current Status

**Server:** ✅ Running on http://localhost:8000
**Knowledge Graph:** ✅ Loaded (1,290 nodes, 3,007 edges)
**All Endpoints:** ✅ Operational

You can access the application now at any of the URLs listed above!

---

**Last Updated:** 2026-01-23
**Server Status:** Running (Process b6826ec)
