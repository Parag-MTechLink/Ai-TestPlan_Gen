# Quick Start Guide

Get the Knowledge Graph DVP System running in 5 minutes!

---

## 1. Start the Server

```bash
cd "C:\Users\Bramha.nimbalkar\Desktop\knowledge graph"
venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## 2. Build the Knowledge Graph

Open a new terminal and run:

```bash
# Ingest data
curl -X POST http://localhost:8080/api/v1/ingest/local

# Get the job_id from response, then build graph:
curl -X POST http://localhost:8080/api/v1/graph/build -H "Content-Type: application/json" -d "{\"ingestion_job_id\": \"YOUR_JOB_ID\", \"enable_structural_links\": true, \"enable_semantic_links\": false, \"enable_reference_links\": true}"
```

Wait ~30 seconds for graph to build.

---

## 3. Open the Query UI

Open in your browser:

**http://localhost:8080/api/v1/visualization/query-ui**

---

## 4. Query and Export

1. Enter component details (e.g., "LED Module", "automotive")
2. Select test categories (thermal, electrical, etc.)
3. Click **"Query Knowledge Graph"**
4. Review results
5. Click **"Export to Excel"** to generate DVP

---

## Other Useful URLs

| URL | Description |
|-----|-------------|
| http://localhost:8080/api/v1/visualization/query-ui | Query Interface |
| http://localhost:8080/api/v1/visualization/interactive | Graph Visualization |
| http://localhost:8080/docs | API Documentation |
| http://localhost:8080/health | Health Check |

---

## Troubleshooting

**Port in use?**
```bash
netstat -ano | findstr :8080
taskkill //F //PID {pid}
```

**No results?**
- Lower the confidence threshold to 0.1 or 0.2
- Make sure the graph is built first

**Server not starting?**
- Activate the virtual environment first
- Check for Python errors in console

---

For full documentation, see [README.md](README.md)
