# 🔧 Fix Visualization Error

## ❌ The Problem

You're getting an error when trying to access the visualization because:

**The knowledge graph hasn't been built yet!**

The visualization needs the graph data to display, but the graph is currently empty.

---

## ✅ The Solution (Step-by-Step)

### **Step 1: Build the Knowledge Graph First** 🕸️

You need to complete these steps **in order** before the visualization will work:

#### 1.1 Open Swagger UI
Go to: **http://localhost:8000/docs**

#### 1.2 Ingest Data
1. Find the section: **"Data Ingestion"**
2. Click on: `POST /api/v1/ingest/local`
3. Click **"Try it out"**
4. Click **"Execute"**
5. **Copy the `job_id`** from the response (e.g., `"abc-123-def"`)

**Wait 10-30 seconds** for ingestion to complete.

#### 1.3 Check Ingestion Status
1. Find: `GET /api/v1/ingest/status/{job_id}`
2. Click **"Try it out"**
3. Paste your `job_id` from step 1.2
4. Click **"Execute"**
5. **Wait until status shows `"completed"`**

#### 1.4 Build the Graph
1. Find the section: **"Knowledge Graph"**
2. Click on: `POST /api/v1/graph/build`
3. Click **"Try it out"**
4. Replace the request body with this (use YOUR job_id from step 1.2):

```json
{
  "ingestion_job_id": "PUT_YOUR_JOB_ID_HERE",
  "enable_structural_links": true,
  "enable_semantic_links": true,
  "enable_reference_links": true,
  "semantic_threshold": 0.75
}
```

5. Click **"Execute"**
6. **Copy the new `job_id`** from the response

**This will take 30-60 seconds** to build the graph.

#### 1.5 Monitor Graph Building
1. Find: `GET /api/v1/graph/status/{job_id}`
2. Use the job_id from step 1.4
3. Keep clicking **"Execute"** until status is `"completed"`

You'll see progress:
- 10% - Initializing
- 20% - Building structure
- 60% - Structure complete
- 70% - Building semantic index
- 90% - Indexing complete
- 100% - ✅ **DONE!**

---

### **Step 2: Now Access the Visualization** 🎨

Once the graph is built (status = "completed"), you can access:

#### Interactive Visualization
**URL:** http://localhost:8000/api/v1/visualization/interactive

**Features:**
- 🔍 Zoom and pan
- 🖱️ Drag nodes around
- 👆 Click nodes to see details
- 🎛️ Filter by type and document
- 📊 Live statistics

#### Statistics Dashboard
**URL:** http://localhost:8000/api/v1/visualization/statistics-visual

**Shows:**
- Node distribution charts
- Edge statistics
- Graph overview table

---

## 🚀 Quick Automated Solution

I've created a test script for you! Just run:

```powershell
python test_graph_build.py
```

This script will:
1. ✅ Check server health
2. ✅ Start ingestion
3. ✅ Wait for completion
4. ✅ Build the graph
5. ✅ Monitor progress
6. ✅ Report when ready

**After the script completes successfully**, the visualization will work!

---

## 🔍 How to Check if Graph is Built

### Method 1: Check Graph Statistics
Go to: http://localhost:8000/docs

Find: `GET /api/v1/graph/statistics`

Click **"Try it out"** → **"Execute"**

**If you see statistics** (nodes, edges, etc.) → ✅ Graph is built!

**If you see an error** → ❌ Graph not built yet

### Method 2: Check Graph Jobs
Find: `GET /api/v1/graph/list`

This shows all graph building jobs and their status.

---

## 📊 What You'll See After Building

Once the graph is built, you'll have:

- **1,290+ nodes** (standards, clauses, requirements)
- **3,000+ edges** (relationships between nodes)
- **Full visualization** with interactive controls
- **Statistics dashboard** with charts

---

## ⚠️ Common Errors & Fixes

### Error: "Knowledge graph not built"
**Cause:** You're trying to visualize before building the graph

**Fix:** Follow Step 1 above to build the graph first

### Error: "Ingestion job not found"
**Cause:** Wrong job_id or ingestion failed

**Fix:** 
1. Check your job_id is correct
2. Run ingestion again: `POST /api/v1/ingest/local`

### Error: "No module named 'app'"
**Cause:** Running from wrong directory

**Fix:**
```powershell
cd "C:\Users\Bramha.nimbalkar\Desktop\knowledge graph"
python test_graph_build.py
```

### Visualization shows "0 nodes, 0 edges"
**Cause:** Graph building failed or not completed

**Fix:**
1. Check graph status: `GET /api/v1/graph/status/{job_id}`
2. Look for errors in the response
3. Check logs: `Get-Content logs\app.log -Tail 50`

---

## 🎯 Summary

**The visualization error happens because:**
1. The graph hasn't been built yet
2. The visualization needs graph data to display

**To fix it:**
1. ✅ Ingest data (`POST /api/v1/ingest/local`)
2. ✅ Build graph (`POST /api/v1/graph/build`)
3. ✅ Wait for completion
4. ✅ Then access visualization

**Quick way:**
```powershell
python test_graph_build.py
```

---

## 📞 Still Having Issues?

1. **Check the logs:**
   ```powershell
   Get-Content logs\app.log -Tail 50
   ```

2. **Verify server is running:**
   ```powershell
   Invoke-WebRequest -Uri http://localhost:8000/health
   ```

3. **Check data directory:**
   - Make sure `./data` folder exists
   - Should contain 547 JSON files

4. **Restart the server if needed:**
   - Press `Ctrl+C` in the terminal
   - Run: `python -m app.main`

---

**Once you complete Step 1, the visualization will work perfectly!** 🎉
