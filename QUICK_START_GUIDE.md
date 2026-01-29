# 🚀 Quick Start Guide - Knowledge Graph DVP Generation System

## ✅ Application Status: RUNNING

Your application is **currently running** on: **http://localhost:8000**

---

## 📍 Access Points

### 1. **Interactive API Documentation (Swagger UI)** ⭐ RECOMMENDED
**URL:** http://localhost:8000/docs

This is the easiest way to interact with your API:
- ✅ Try all endpoints directly in your browser
- ✅ See request/response examples
- ✅ Test the complete workflow visually
- ✅ No coding required!

### 2. **Alternative Documentation (ReDoc)**
**URL:** http://localhost:8000/redoc
- Clean, readable documentation
- Detailed schema descriptions

### 3. **Health Check**
**URL:** http://localhost:8000/health
- Verify server is running
- Check version and timestamp

### 4. **Knowledge Graph Visualization**
**URL:** http://localhost:8000/api/v1/visualization/interactive
- Interactive D3.js graph visualization
- Filter and search nodes
- View relationships

---

## 🎯 Complete Workflow (Step-by-Step)

### **Step 1: Ingest Data** 📥

**Endpoint:** `POST /api/v1/ingest/local`

**How to do it:**
1. Go to http://localhost:8000/docs
2. Find "Data Ingestion" section
3. Click on `POST /api/v1/ingest/local`
4. Click "Try it out"
5. Click "Execute"

**What it does:**
- Loads all JSON files from the `./data` directory (547 files)
- Returns a `job_id` to track progress

**Example Response:**
```json
{
  "job_id": "abc-123-def",
  "status": "pending",
  "message": "Ingesting from local directory: ./data",
  "files_fetched": 0
}
```

**Save the `job_id`** - you'll need it for the next step!

---

### **Step 2: Check Ingestion Status** ⏳

**Endpoint:** `GET /api/v1/ingest/status/{job_id}`

**How to do it:**
1. In Swagger UI, find `GET /api/v1/ingest/status/{job_id}`
2. Click "Try it out"
3. Paste your `job_id` from Step 1
4. Click "Execute"

**Wait until status is "completed"**

**Example Response:**
```json
{
  "job_id": "abc-123-def",
  "status": "completed",
  "progress_percent": 100.0,
  "message": "Fetched 547 documents"
}
```

---

### **Step 3: Build Knowledge Graph** 🕸️

**Endpoint:** `POST /api/v1/graph/build`

**How to do it:**
1. Find `POST /api/v1/graph/build` in Swagger UI
2. Click "Try it out"
3. Use this request body:

```json
{
  "ingestion_job_id": "abc-123-def",
  "enable_structural_links": true,
  "enable_semantic_links": true,
  "enable_reference_links": true,
  "semantic_threshold": 0.75
}
```

4. Replace `abc-123-def` with your actual ingestion job_id
5. Click "Execute"

**What it does:**
- Creates knowledge graph with 1,290+ nodes
- Builds 3,000+ edges (relationships)
- Creates semantic index for smart searching
- Takes ~30-60 seconds

**Save the new `job_id`** from the response!

---

### **Step 4: Monitor Graph Building** 📊

**Endpoint:** `GET /api/v1/graph/status/{job_id}`

**How to do it:**
1. Find `GET /api/v1/graph/status/{job_id}`
2. Use the job_id from Step 3
3. Keep checking until status is "completed"

**Progress updates:**
- 10%: Initializing
- 20%: Building graph structure
- 60%: Structure complete
- 70%: Building semantic index
- 90%: Indexing complete
- 100%: Saved and ready!

---

### **Step 5: Query for Requirements** 🔍

**Endpoint:** `POST /api/v1/retrieval/query`

**How to do it:**
1. Find `POST /api/v1/retrieval/query`
2. Click "Try it out"
3. Use this example request:

```json
{
  "component_profile": {
    "name": "W601 Tail Lamp LED Module",
    "type": "LED Module",
    "application": "automotive tail lamp",
    "variants": ["High+", "High"],
    "test_level": "PCB level",
    "applicable_standards": ["ISO 16750-3", "ISO 16750-4"],
    "test_categories": ["thermal", "mechanical"],
    "quantity_per_test": {"RH": 3, "LH": 3}
  },
  "retrieval_method": "hybrid",
  "max_results": 50,
  "min_confidence": 0.7
}
```

4. Click "Execute"

**What it does:**
- Searches knowledge graph for relevant requirements
- Uses hybrid search (semantic + graph traversal)
- Returns ranked results with confidence scores

---

### **Step 6: Generate Test Procedures with LLM** 🤖

**Endpoint:** `POST /api/v1/llm/generate`

**Requirements:**
- ⚠️ Requires OpenAI API key in `.env` file
- If not configured, you'll get mock test cases

**How to do it:**
1. Find `POST /api/v1/llm/generate`
2. Use results from Step 5 as input
3. Click "Execute"

**What it does:**
- Uses GPT-4 to generate detailed test procedures
- Creates acceptance criteria
- Adds traceability information

---

### **Step 7: Generate DVP Document** 📄

**Endpoint:** `POST /api/v1/dvp/generate`

**How to do it:**
1. Find `POST /api/v1/dvp/generate`
2. Use test procedures from Step 6
3. Click "Execute"

**What it does:**
- Generates Excel DVP document
- Includes multiple sheets:
  - Main test matrix
  - Test sequence
  - Traceability matrix
  - Source references

**Response includes:**
```json
{
  "dvp_id": "DVP_W601_20240123",
  "download_url": "/api/v1/dvp/download/DVP_W601_20240123",
  "test_cases_count": 25,
  "requirements_covered": 45
}
```

---

### **Step 8: Download DVP** ⬇️

**Endpoint:** `GET /api/v1/dvp/download/{dvp_id}`

**How to do it:**
1. Find `GET /api/v1/dvp/download/{dvp_id}`
2. Use the `dvp_id` from Step 7
3. Click "Execute"
4. Click "Download file"

**Result:** Excel file with complete DVP!

---

## 🛠️ Common Issues & Solutions

### ❌ Error: "Knowledge graph not built"
**Solution:** Complete Steps 1-4 first to build the graph

### ❌ Error: "Ingestion job not found"
**Solution:** Make sure you're using the correct `job_id` from the ingestion step

### ❌ Error: "OpenAI API key not configured"
**Solution:** Either:
- Add `OPENAI_API_KEY=sk-...` to your `.env` file, OR
- Skip LLM generation and use mock test cases

### ❌ Error: "Port already in use"
**Solution:** You already have the server running! Just use it.

### ❌ Server not responding
**Solution:** 
```powershell
# Check if running
Invoke-WebRequest -Uri http://localhost:8000/health

# If not, start it
python -m app.main
```

---

## 📊 Current System Status

- **Data Files:** 547 JSON standards documents in `./data`
- **Server:** Running on http://localhost:8000
- **Mode:** Development (auto-reload enabled)
- **Version:** 1.0.0

---

## 🎓 Tips for Success

1. **Always use Swagger UI** (http://localhost:8000/docs) - it's the easiest way!
2. **Save job IDs** - you need them to track progress and chain operations
3. **Wait for completion** - Check status endpoints before moving to next step
4. **Start simple** - Try the example requests first, then customize
5. **Check logs** - If something fails, check `./logs/app.log`

---

## 🔗 Useful Links

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health
- **Visualization:** http://localhost:8000/api/v1/visualization/interactive

---

## 📞 Need Help?

1. Check the logs: `./logs/app.log`
2. Review the full README.md
3. Use the test script: `python test_graph_build.py`

---

**🎉 You're all set! Open http://localhost:8000/docs to get started!**
