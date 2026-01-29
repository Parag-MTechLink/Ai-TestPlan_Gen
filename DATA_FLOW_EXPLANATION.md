# 📊 How Data Flows from Knowledge Graph to Excel

## Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 1: BUILD KNOWLEDGE GRAPH                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  JSON Files (547 standards documents)         │
        │  - BS_EN_50174_3_2013.json                   │
        │  - IEC_61076_8_103_2023.json                 │
        │  - ISO_16750_3.json                          │
        │  etc...                                       │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  Knowledge Graph Builder                      │
        │  (app/core/graph_builder.py)                 │
        │                                               │
        │  Creates:                                     │
        │  • 1,290+ NODES (standards, clauses, reqs)   │
        │  • 3,000+ EDGES (relationships)              │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  NetworkX Graph Structure                     │
        │                                               │
        │  Node Types:                                  │
        │  ├─ Standard (e.g., "ISO 16750-3")          │
        │  ├─ Clause (e.g., "4.3.2.1")                │
        │  ├─ Requirement (e.g., "SHALL test at...")  │
        │  └─ ExternalStandard                         │
        │                                               │
        │  Node Attributes:                             │
        │  ├─ node_id: "BS_EN_50174_3_2013::4.3.4.1"  │
        │  ├─ node_type: "Clause"                      │
        │  ├─ title: "Installation methods"            │
        │  ├─ content: ["text content..."]             │
        │  ├─ clause_id: "4.3.4.1"                     │
        │  ├─ document_id: "BS_EN_50174_3_2013"       │
        │  ├─ parent_id: "4.3.4"                       │
        │  └─ depth: 3                                 │
        │                                               │
        │  Edge Types:                                  │
        │  ├─ PARENT_OF (hierarchical)                 │
        │  ├─ CONTAINS_REQUIREMENT                     │
        │  ├─ REFERENCES                               │
        │  └─ CITES_STANDARD                           │
        └───────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│              STEP 2: QUERY FOR RELEVANT REQUIREMENTS                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  Component Profile (User Input)               │
        │  {                                            │
        │    "name": "W601 Tail Lamp LED Module",      │
        │    "type": "LED Module",                     │
        │    "application": "automotive tail lamp",    │
        │    "test_categories": ["thermal", "mech"],   │
        │    "applicable_standards": ["ISO 16750-3"]   │
        │  }                                            │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  Retrieval Engine (HYBRID SEARCH)            │
        │  (app/api/v1/retrieval.py)                   │
        │                                               │
        │  Phase 1: SEMANTIC SEARCH                    │
        │  ├─ Build query: "LED Module automotive..."  │
        │  ├─ Use embeddings (sentence-transformers)   │
        │  ├─ Search vector database (ChromaDB)        │
        │  └─ Get top 50 similar clauses               │
        │                                               │
        │  Phase 2: GRAPH TRAVERSAL                    │
        │  ├─ For each clause found:                   │
        │  │  ├─ Get parent clause (context)           │
        │  │  ├─ Get child requirements                │
        │  │  └─ Get referenced standards              │
        │  └─ Build hierarchical context               │
        │                                               │
        │  Phase 3: MERGE & RANK                       │
        │  ├─ Combine semantic + graph results         │
        │  ├─ Score by relevance (0.0 - 1.0)          │
        │  ├─ Filter by confidence threshold (0.7)     │
        │  └─ Return top results                       │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  Retrieved Results (JSON)                     │
        │  [                                            │
        │    {                                          │
        │      "node_id": "ISO_16750_3::4.2.1::req_0", │
        │      "document_id": "ISO_16750_3",           │
        │      "clause_id": "4.2.1",                   │
        │      "title": "Operation at low temp",       │
        │      "content": ["The device SHALL..."],     │
        │      "requirements": [                        │
        │        {                                      │
        │          "requirement_id": "req_0",          │
        │          "requirement_type": "mandatory",    │
        │          "text": "SHALL operate at -40°C",  │
        │          "keyword": "SHALL"                  │
        │        }                                      │
        │      ],                                       │
        │      "parent_context": {                     │
        │        "clause_id": "4.2",                   │
        │        "title": "Temperature tests"          │
        │      },                                       │
        │      "relevance_score": 0.92                 │
        │    },                                         │
        │    ... (45 more results)                     │
        │  ]                                            │
        └───────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│           STEP 3: GENERATE TEST PROCEDURES WITH LLM                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  LLM Generator (app/api/v1/llm.py)           │
        │                                               │
        │  Input:                                       │
        │  ├─ Retrieved requirements (from Step 2)     │
        │  ├─ Component profile                        │
        │  └─ Generation mode (detailed/summary)       │
        │                                               │
        │  Process:                                     │
        │  ├─ Build prompt with context                │
        │  ├─ Call OpenAI GPT-4                        │
        │  ├─ Parse LLM response                       │
        │  └─ Structure test procedures                │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  Test Cases (Structured JSON)                │
        │  [                                            │
        │    {                                          │
        │      "test_id": "B1",                        │
        │      "test_standard": "ISO 16750-3",         │
        │      "test_description": "Operation at Low   │
        │                           Temperature",       │
        │      "test_procedure": "1. Condition sample  │
        │                         at -40°C for 2h      │
        │                         2. Apply power       │
        │                         3. Verify operation  │
        │                         4. Record results",  │
        │      "acceptance_criteria": "Device SHALL    │
        │                              operate without │
        │                              failure",        │
        │      "test_responsibility": "Supplier",      │
        │      "test_stage": "DVP",                    │
        │      "quantity": "RH: 3, LH: 3",            │
        │      "estimated_days": 5,                    │
        │      "traceability": {                       │
        │        "requirement_id": "ISO_16750_3::...", │
        │        "source_clause": "4.2.1",             │
        │        "source_standard": "ISO 16750-3",     │
        │        "confidence_score": 0.92,             │
        │        "linking_method": "Hybrid"            │
        │      }                                        │
        │    },                                         │
        │    ... (24 more test cases)                  │
        │  ]                                            │
        └───────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│              STEP 4: GENERATE EXCEL DVP DOCUMENT                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  DVP Generator (app/api/v1/dvp.py)           │
        │  Class: DVPGenerator                          │
        │                                               │
        │  Uses: openpyxl library                       │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  SHEET 1: "Annex B-Electronics DVP"          │
        │  (Main Test Matrix)                           │
        │                                               │
        │  Method: _create_test_matrix_sheet()         │
        │                                               │
        │  Row 1-5: Header Info                        │
        │  ├─ Project Name: W601 Tail Lamp LED Module  │
        │  ├─ Component Type: LED Module               │
        │  ├─ Application: automotive tail lamp        │
        │  └─ Test Level: PCB level                    │
        │                                               │
        │  Row 6: Column Headers                       │
        │  ├─ Sl.No. | Test Standard | Test Desc |... │
        │  └─ (14 columns total)                       │
        │                                               │
        │  Row 7+: Test Data (from test_cases array)   │
        │  FOR EACH test_case IN test_cases:           │
        │    ├─ Col A: test_case['test_id']           │
        │    ├─ Col B: test_case['test_standard']     │
        │    ├─ Col C: test_case['test_description']  │
        │    ├─ Col D: test_case['test_procedure']    │
        │    ├─ Col E: test_case['acceptance_criteria']│
        │    ├─ Col F: test_case['test_responsibility']│
        │    ├─ Col G: test_case['test_stage']        │
        │    ├─ Col H: test_case['quantity']          │
        │    ├─ Col I: test_case['estimated_days']    │
        │    ├─ Col J-K: (empty - for dates)          │
        │    ├─ Col L: (empty - for inference)        │
        │    ├─ Col M: test_case['pcb_or_lamp']       │
        │    └─ Col N: test_case['remarks']           │
        │                                               │
        │  Formatting:                                  │
        │  ├─ Headers: Bold, white text, blue bg       │
        │  ├─ Wrap text in procedure/criteria cols     │
        │  ├─ Column widths optimized                  │
        │  └─ Row heights set to 60px                  │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  SHEET 2: "EMC & ENV TEST SEQUENCE"          │
        │  (Test Grouping and Sequence)                 │
        │                                               │
        │  Method: _create_test_sequence_sheet()       │
        │                                               │
        │  Groups tests by category:                    │
        │  ├─ Thermal Tests (Group 1)                  │
        │  │  ├─ B1: Operation at Low Temperature      │
        │  │  ├─ B2: Operation at High Temperature     │
        │  │  └─ B3: Temperature Cycling               │
        │  ├─ Mechanical Tests (Group 2)               │
        │  │  ├─ B4: Vibration Test                    │
        │  │  └─ B5: Shock Test                        │
        │  └─ Environmental Tests (Group 3)            │
        │     ├─ B6: Humidity Test                     │
        │     └─ B7: Salt Spray Test                   │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  SHEET 3: "Traceability Matrix"              │
        │  (Requirement-to-Test Mapping)                │
        │                                               │
        │  Method: _create_traceability_sheet()        │
        │                                               │
        │  FOR EACH test_case IN test_cases:           │
        │    Extract traceability data:                 │
        │    ├─ Test ID: test_case['test_id']         │
        │    ├─ Test Desc: test_case['test_description']│
        │    ├─ Req ID: traceability['requirement_id'] │
        │    ├─ Source Clause: traceability['source_clause']│
        │    ├─ Source Std: traceability['source_standard']│
        │    ├─ Req Type: traceability['requirement_type']│
        │    ├─ Confidence: traceability['confidence_score']│
        │    └─ Method: "Hybrid (Semantic + Graph)"    │
        │                                               │
        │  Example Row:                                 │
        │  B1 | Operation at Low Temp | ISO_16750_3::..│
        │  | 4.2.1 | ISO 16750-3 | mandatory | 0.92 |  │
        │  | Hybrid (Semantic + Graph)                 │
        │                                               │
        │  This shows EXACTLY which graph node was     │
        │  used to create each test!                   │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  SHEET 4: "Source References"                │
        │  (All Referenced Standards)                   │
        │                                               │
        │  Method: _create_references_sheet()          │
        │                                               │
        │  Lists all unique:                            │
        │  ├─ Standards referenced                     │
        │  ├─ Clauses used                             │
        │  └─ Document IDs                             │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  FINAL EXCEL FILE                            │
        │  "DVP_W601_20240123.xlsx"                    │
        │                                               │
        │  Saved to: ./output/                         │
        │  File size: ~1.2 MB                          │
        │  Contains: 4 sheets, 25 test cases           │
        │  Traceability: Complete (45 requirements)    │
        └───────────────────────────────────────────────┘
```

---

## 🔍 Detailed Code Flow

### 1. **Graph Node → Retrieval Result**

**Location:** `app/api/v1/retrieval.py` (lines 85-130)

```python
# For each node in the knowledge graph:
for result in semantic_results[:20]:
    node_id = result['node_id']  # e.g., "ISO_16750_3::4.2.1"
    
    # Get the actual node data from NetworkX graph
    if graph_builder.graph.has_node(node_id):
        node_data = graph_builder.graph.nodes[node_id]
        
        # Extract all attributes
        graph_results.append({
            'node_id': node_id,
            'document_id': node_data.get('document_id'),     # From graph node
            'clause_id': node_data.get('clause_id'),         # From graph node
            'title': node_data.get('title'),                 # From graph node
            'content': node_data.get('content'),             # From graph node
            'requirements': clause_requirements,              # From child nodes
            'parent_context': parent_context,                 # From parent node
            'relevance_score': result['relevance_score']
        })
```

**Key Point:** Every piece of data comes from the **graph node attributes** that were created during graph building.

---

### 2. **Retrieval Result → Test Case**

**Location:** `app/api/v1/llm.py` (LLM generation)

```python
# LLM takes the retrieved context and generates structured test cases
test_case = {
    "test_id": "B1",
    "test_standard": result['document_id'],           # From graph node
    "test_description": llm_generated_description,    # From LLM
    "test_procedure": llm_generated_procedure,        # From LLM
    "acceptance_criteria": llm_generated_criteria,    # From LLM
    "traceability": {
        "requirement_id": result['node_id'],          # From graph node
        "source_clause": result['clause_id'],         # From graph node
        "source_standard": result['document_id'],     # From graph node
        "confidence_score": result['relevance_score'] # From retrieval
    }
}
```

**Key Point:** The LLM generates the **procedure text**, but the **traceability data** comes directly from the graph nodes.

---

### 3. **Test Case → Excel Row**

**Location:** `app/api/v1/dvp.py` (lines 119-147)

```python
# For each test case, write to Excel
for row_idx, test_case in enumerate(test_cases, start=7):
    # Each column gets data from the test_case dictionary
    ws.cell(row=row_idx, column=1).value = test_case.get('test_id')
    ws.cell(row=row_idx, column=2).value = test_case.get('test_standard')
    ws.cell(row=row_idx, column=3).value = test_case.get('test_description')
    ws.cell(row=row_idx, column=4).value = test_case.get('test_procedure')
    ws.cell(row=row_idx, column=5).value = test_case.get('acceptance_criteria')
    # ... etc for all 14 columns
```

**Key Point:** Direct mapping from JSON dictionary to Excel cells using `openpyxl`.

---

### 4. **Traceability Sheet Creation**

**Location:** `app/api/v1/dvp.py` (lines 186-228)

```python
# For each test case, extract traceability
for test_case in test_cases:
    traceability = test_case.get('traceability', {})
    
    # Write traceability data to Excel
    ws.cell(row=row_idx, column=1).value = test_case.get('test_id')
    ws.cell(row=row_idx, column=3).value = traceability.get('requirement_id')
    ws.cell(row=row_idx, column=4).value = traceability.get('source_clause')
    ws.cell(row=row_idx, column=5).value = traceability.get('source_standard')
    ws.cell(row=row_idx, column=7).value = traceability.get('confidence_score')
```

**Key Point:** The `requirement_id` in the traceability sheet is the **exact node_id from the knowledge graph**!

---

## 📋 Example: Complete Data Journey

Let's trace a single requirement through the entire system:

### **Original JSON File:**
```json
// File: data/ISO_16750_3.json
{
  "document_id": "ISO_16750_3",
  "clauses": [
    {
      "clause_id": "4.2.1",
      "title": "Operation at low temperature",
      "content": ["The device SHALL operate at -40°C for 2 hours"],
      "requirements": [
        {
          "requirement_type": "mandatory",
          "keyword": "SHALL",
          "text": "operate at -40°C for 2 hours"
        }
      ]
    }
  ]
}
```

### **Graph Node Created:**
```python
# Node ID: "ISO_16750_3::4.2.1::req_0"
graph.nodes["ISO_16750_3::4.2.1::req_0"] = {
    'node_type': 'Requirement',
    'document_id': 'ISO_16750_3',
    'clause_id': '4.2.1',
    'parent_clause': '4.2',
    'requirement_type': 'mandatory',
    'keyword': 'SHALL',
    'text': 'operate at -40°C for 2 hours',
    'chunk_id': 'chunk_123'
}
```

### **Retrieved by Query:**
```python
# User queries for "LED Module thermal tests"
# Semantic search finds this node with score 0.92
retrieved_result = {
    'node_id': 'ISO_16750_3::4.2.1::req_0',
    'document_id': 'ISO_16750_3',
    'clause_id': '4.2.1',
    'text': 'operate at -40°C for 2 hours',
    'relevance_score': 0.92
}
```

### **LLM Generates Test:**
```python
test_case = {
    'test_id': 'B1',
    'test_standard': 'ISO 16750-3',
    'test_description': 'Operation at Low Temperature',
    'test_procedure': '1. Condition at -40°C for 2h\n2. Apply power\n3. Verify',
    'acceptance_criteria': 'Device SHALL operate without failure',
    'traceability': {
        'requirement_id': 'ISO_16750_3::4.2.1::req_0',  # ← Graph node ID!
        'source_clause': '4.2.1',
        'source_standard': 'ISO 16750-3',
        'confidence_score': 0.92
    }
}
```

### **Written to Excel:**

**Sheet 1 (Test Matrix):**
| Sl.No | Test Standard | Test Description | Test Procedure | Acceptance Criteria |
|-------|---------------|------------------|----------------|---------------------|
| B1 | ISO 16750-3 | Operation at Low Temperature | 1. Condition at -40°C... | Device SHALL operate... |

**Sheet 3 (Traceability):**
| Test ID | Requirement ID | Source Clause | Source Standard | Confidence |
|---------|----------------|---------------|-----------------|------------|
| B1 | ISO_16750_3::4.2.1::req_0 | 4.2.1 | ISO 16750-3 | 0.92 |

---

## 🎯 Summary

**The data flow is:**

1. **JSON → Graph Nodes** (with all attributes stored)
2. **Graph Nodes → Retrieval Results** (via semantic + graph search)
3. **Retrieval Results → Test Cases** (LLM generates procedures, keeps traceability)
4. **Test Cases → Excel Rows** (direct mapping with openpyxl)

**The traceability is maintained because:**
- Every graph node has a unique ID
- This ID is preserved through retrieval
- This ID is stored in the test case traceability
- This ID is written to the Excel traceability sheet

**You can trace ANY test in the Excel back to the EXACT graph node (and original JSON file) that created it!**

---

## 🔧 Code Files Involved

| Step | File | Key Function |
|------|------|--------------|
| Build Graph | `app/core/graph_builder.py` | `build_from_directory()` |
| Retrieve | `app/api/v1/retrieval.py` | `query_knowledge_graph()` |
| Generate Tests | `app/api/v1/llm.py` | `generate_test_procedures()` |
| Create Excel | `app/api/v1/dvp.py` | `DVPGenerator.generate_dvp()` |
| Test Matrix | `app/api/v1/dvp.py` | `_create_test_matrix_sheet()` |
| Traceability | `app/api/v1/dvp.py` | `_create_traceability_sheet()` |

---

**This complete traceability is what makes the system powerful - you can always trace back from the Excel to the source!** 🎉
