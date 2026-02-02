"""
Visualization Endpoints for Knowledge Graph
Interactive graph visualization and exploration
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Optional, List
import json
import networkx as nx
from loguru import logger

router = APIRouter()

@router.get("/graph-data")
async def get_graph_data(
    max_nodes: int = 100,
    node_type: Optional[str] = None,
    document_id: Optional[str] = None
):
    """
    **Get graph data in format suitable for visualization**

    Returns nodes and edges in D3.js compatible format.

    **Parameters:**
    - max_nodes: Maximum number of nodes to return (default: 100)
    - node_type: Filter by node type (Clause, Requirement, Standard)
    - document_id: Filter by specific document

    **Returns:**
    - nodes: List of nodes with id, label, type, etc.
    - links: List of edges with source, target, type
    """
    from app.api.v1.graph import graph_builder

    if not graph_builder:
        raise HTTPException(
            status_code=400,
            detail="Knowledge graph not built. Please call /graph/build first."
        )

    graph = graph_builder.graph

    # Filter nodes
    nodes_data = []
    node_ids = []

    for node_id, data in graph.nodes(data=True):
        # Apply filters
        if node_type and data.get('node_type') != node_type:
            continue

        if document_id and data.get('document_id') != document_id:
            continue

        # Build node data
        node_info = {
            'id': node_id,
            'label': data.get('title', node_id)[:50],
            'type': data.get('node_type', 'Unknown'),
            'document_id': data.get('document_id', ''),
            'clause_id': data.get('clause_id', ''),
            'size': 10 + (data.get('depth', 0) * 2)
        }

        # Color by type
        color_map = {
            'Standard': '#FF6B6B',
            'Clause': '#4ECDC4',
            'Requirement': '#45B7D1',
            'ExternalStandard': '#FFA07A'
        }
        node_info['color'] = color_map.get(data.get('node_type'), '#999999')

        nodes_data.append(node_info)
        node_ids.append(node_id)

        if len(nodes_data) >= max_nodes:
            break

    # Get edges between selected nodes
    edges_data = []
    node_id_set = set(node_ids)

    for u, v, key, data in graph.edges(data=True, keys=True):
        if u in node_id_set and v in node_id_set:
            edge_info = {
                'source': u,
                'target': v,
                'type': data.get('edge_type', 'unknown'),
                'method': data.get('linking_method', ''),
                'confidence': data.get('confidence', 1.0)
            }

            # Color by edge type
            edge_color_map = {
                'PARENT_OF': '#2C3E50',
                'REFERENCES': '#E74C3C',
                'CONTAINS_REQUIREMENT': '#9B59B6',
                'CITES_STANDARD': '#F39C12',
                'SIBLING_OF': '#27AE60'
            }
            edge_info['color'] = edge_color_map.get(data.get('edge_type'), '#BDC3C7')

            edges_data.append(edge_info)

    return {
        'nodes': nodes_data,
        'links': edges_data,
        'total_nodes': len(nodes_data),
        'total_links': len(edges_data),
        'metadata': {
            'max_nodes': max_nodes,
            'filtered_by_type': node_type,
            'filtered_by_document': document_id
        }
    }

@router.get("/interactive", response_class=HTMLResponse)
async def interactive_visualization():
    """
    **Interactive Knowledge Graph Visualization**

    Opens an interactive D3.js-based visualization in the browser.

    Features:
    - Zoom and pan
    - Drag nodes
    - Click nodes to see details
    - Filter by type and document
    - Search nodes
    """

    html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Knowledge Graph Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #1a1a1a;
            color: #fff;
        }

        #controls {
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.8);
            padding: 20px;
            border-radius: 8px;
            z-index: 1000;
            max-width: 300px;
        }

        #info {
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            padding: 20px;
            border-radius: 8px;
            z-index: 1000;
            max-width: 400px;
            max-height: 80vh;
            overflow-y: auto;
        }

        .control-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #4ECDC4;
        }

        select, input, button {
            width: 100%;
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #4ECDC4;
            background: #2a2a2a;
            color: #fff;
            font-size: 14px;
        }

        button {
            background: #4ECDC4;
            color: #1a1a1a;
            cursor: pointer;
            font-weight: bold;
            margin-top: 10px;
        }

        button:hover {
            background: #45B7D1;
        }

        #graph-container {
            width: 100vw;
            height: 100vh;
        }

        .node {
            cursor: pointer;
            stroke: #fff;
            stroke-width: 1.5px;
        }

        .node:hover {
            stroke: #FFD700;
            stroke-width: 3px;
        }

        .link {
            stroke-opacity: 0.6;
            stroke-width: 1.5px;
        }

        .node-label {
            font-size: 10px;
            fill: #fff;
            pointer-events: none;
            text-anchor: middle;
        }

        .legend {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 8px;
        }

        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }

        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
        }

        .stats {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 8px;
            font-size: 14px;
        }

        .stat-item {
            margin-bottom: 5px;
        }

        h2 {
            margin-top: 0;
            color: #4ECDC4;
        }

        h3 {
            color: #45B7D1;
            margin-top: 15px;
            margin-bottom: 5px;
        }

        .detail-item {
            margin-bottom: 8px;
            font-size: 13px;
        }

        .detail-label {
            color: #888;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div id="controls">
        <h2>Knowledge Graph Explorer</h2>

        <div class="control-group">
            <label>Max Nodes:</label>
            <input type="number" id="maxNodes" value="100" min="10" max="500">
        </div>

        <div class="control-group">
            <label>Node Type:</label>
            <select id="nodeType">
                <option value="">All Types</option>
                <option value="Standard">Standards</option>
                <option value="Clause">Clauses</option>
                <option value="Requirement">Requirements</option>
                <option value="ExternalStandard">External Standards</option>
            </select>
        </div>

        <div class="control-group">
            <label>Document:</label>
            <select id="documentId">
                <option value="">All Documents</option>
                <option value="BS_EN_50174_3_2013">BS_EN_50174_3_2013</option>
                <option value="IEC_61076_8_103_2023">IEC_61076_8_103_2023</option>
                <option value="IS17017_Part2_Sec2_2020">IS17017_Part2_Sec2_2020</option>
            </select>
        </div>

        <button onclick="loadGraph()">Refresh Graph</button>
        <button onclick="resetZoom()">Reset View</button>
    </div>

    <div id="info">
        <h2>Node Details</h2>
        <p style="color: #888;">Click on a node to see details</p>
        <div id="nodeDetails"></div>
    </div>

    <div class="legend">
        <h3 style="margin-top: 0;">Node Types</h3>
        <div class="legend-item">
            <div class="legend-color" style="background: #FF6B6B;"></div>
            <span>Standard</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #4ECDC4;"></div>
            <span>Clause</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #45B7D1;"></div>
            <span>Requirement</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #FFA07A;"></div>
            <span>External Standard</span>
        </div>
    </div>

    <div class="stats">
        <h3 style="margin-top: 0;">Statistics</h3>
        <div class="stat-item">Nodes: <span id="nodeCount">0</span></div>
        <div class="stat-item">Edges: <span id="edgeCount">0</span></div>
    </div>

    <div id="graph-container"></div>

    <script>
        let simulation;
        let svg;
        let g;

        const width = window.innerWidth;
        const height = window.innerHeight;

        function initVisualization() {
            svg = d3.select("#graph-container")
                .append("svg")
                .attr("width", width)
                .attr("height", height);

            // Add zoom
            const zoom = d3.zoom()
                .scaleExtent([0.1, 10])
                .on("zoom", (event) => {
                    g.attr("transform", event.transform);
                });

            svg.call(zoom);

            g = svg.append("g");
        }

        function loadGraph() {
            const maxNodes = document.getElementById('maxNodes').value;
            const nodeType = document.getElementById('nodeType').value;
            const documentId = document.getElementById('documentId').value;

            let url = `/api/v1/visualization/graph-data?max_nodes=${maxNodes}`;
            if (nodeType) url += `&node_type=${nodeType}`;
            if (documentId) url += `&document_id=${documentId}`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    renderGraph(data);
                    updateStats(data);
                })
                .catch(error => {
                    console.error('Error loading graph:', error);
                    alert('Error loading graph. Make sure the graph has been built first.');
                });
        }

        function renderGraph(data) {
            // Clear existing
            g.selectAll("*").remove();

            // Create simulation
            simulation = d3.forceSimulation(data.nodes)
                .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide().radius(30));

            // Draw links
            const link = g.append("g")
                .selectAll("line")
                .data(data.links)
                .enter()
                .append("line")
                .attr("class", "link")
                .attr("stroke", d => d.color);

            // Draw nodes
            const node = g.append("g")
                .selectAll("circle")
                .data(data.nodes)
                .enter()
                .append("circle")
                .attr("class", "node")
                .attr("r", d => d.size)
                .attr("fill", d => d.color)
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended))
                .on("click", showNodeDetails);

            // Add labels
            const label = g.append("g")
                .selectAll("text")
                .data(data.nodes)
                .enter()
                .append("text")
                .attr("class", "node-label")
                .text(d => d.label);

            // Update positions
            simulation.on("tick", () => {
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);

                label
                    .attr("x", d => d.x)
                    .attr("y", d => d.y - 15);
            });
        }

        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        function showNodeDetails(event, d) {
            const detailsHtml = `
                <div class="detail-item">
                    <span class="detail-label">ID:</span> ${d.id}
                </div>
                <div class="detail-item">
                    <span class="detail-label">Type:</span> ${d.type}
                </div>
                <div class="detail-item">
                    <span class="detail-label">Label:</span> ${d.label}
                </div>
                <div class="detail-item">
                    <span class="detail-label">Document:</span> ${d.document_id || 'N/A'}
                </div>
                <div class="detail-item">
                    <span class="detail-label">Clause:</span> ${d.clause_id || 'N/A'}
                </div>
            `;

            document.getElementById('nodeDetails').innerHTML = detailsHtml;
        }

        function updateStats(data) {
            document.getElementById('nodeCount').textContent = data.total_nodes;
            document.getElementById('edgeCount').textContent = data.total_links;
        }

        function resetZoom() {
            svg.transition().duration(750).call(
                d3.zoom().transform,
                d3.zoomIdentity
            );
        }

        // Initialize on load
        initVisualization();
        loadGraph();
    </script>
</body>
</html>
    """

    return HTMLResponse(content=html_content)

@router.get("/query-ui", response_class=HTMLResponse)
async def query_interface():
    """
    **Interactive Query Interface for Knowledge Graph**

    A user-friendly interface to:
    - Query the knowledge graph
    - View all nodes and their details
    - Filter by component profile
    - Export results to Excel
    """

    html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Knowledge Graph Query Interface</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid #4ECDC4;
            margin-bottom: 30px;
        }

        h1 {
            color: #4ECDC4;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #888;
            font-size: 1.1em;
        }

        .main-content {
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 30px;
        }

        .sidebar {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            padding: 25px;
            height: fit-content;
            position: sticky;
            top: 20px;
        }

        .section-title {
            color: #4ECDC4;
            font-size: 1.3em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #333;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            color: #45B7D1;
            margin-bottom: 8px;
            font-weight: 600;
        }

        input, select, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #333;
            border-radius: 8px;
            background: #1a1a2e;
            color: #fff;
            font-size: 14px;
            transition: border-color 0.3s;
        }

        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #4ECDC4;
        }

        textarea {
            min-height: 80px;
            resize: vertical;
        }

        .checkbox-group {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .checkbox-item {
            display: flex;
            align-items: center;
            background: #1a1a2e;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.3s;
        }

        .checkbox-item:hover {
            background: #2a2a4e;
        }

        .checkbox-item input {
            width: auto;
            margin-right: 8px;
        }

        .btn {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 10px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #4ECDC4 0%, #45B7D1 100%);
            color: #1a1a2e;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(78, 205, 196, 0.4);
        }

        .btn-secondary {
            background: #333;
            color: #fff;
        }

        .btn-secondary:hover {
            background: #444;
        }

        .btn-success {
            background: linear-gradient(135deg, #27AE60 0%, #2ECC71 100%);
            color: #fff;
        }

        .results-panel {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            padding: 25px;
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #333;
            padding-bottom: 15px;
        }

        .tab {
            padding: 10px 20px;
            background: #1a1a2e;
            border: 2px solid #333;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            color: #888;
        }

        .tab.active {
            background: #4ECDC4;
            color: #1a1a2e;
            border-color: #4ECDC4;
        }

        .tab:hover:not(.active) {
            border-color: #4ECDC4;
            color: #4ECDC4;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .stats-bar {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #2a2a4e 100%);
            padding: 15px 25px;
            border-radius: 8px;
            border-left: 4px solid #4ECDC4;
        }

        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #4ECDC4;
        }

        .stat-label {
            color: #888;
            font-size: 0.9em;
        }

        .results-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        .results-table th {
            background: #4ECDC4;
            color: #1a1a2e;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }

        .results-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #333;
            vertical-align: top;
        }

        .results-table tr:hover {
            background: rgba(78, 205, 196, 0.1);
        }

        .node-type {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .node-type.Standard { background: #FF6B6B; color: #fff; }
        .node-type.Clause { background: #4ECDC4; color: #1a1a2e; }
        .node-type.Requirement { background: #45B7D1; color: #1a1a2e; }
        .node-type.ExternalStandard { background: #FFA07A; color: #1a1a2e; }

        .requirement-text {
            max-width: 400px;
            font-size: 13px;
            line-height: 1.5;
        }

        .confidence-bar {
            width: 100px;
            height: 8px;
            background: #333;
            border-radius: 4px;
            overflow: hidden;
        }

        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #FF6B6B, #FFD93D, #6BCB77);
            border-radius: 4px;
        }

        .loading {
            text-align: center;
            padding: 50px;
            color: #888;
        }

        .loading-spinner {
            border: 4px solid #333;
            border-top: 4px solid #4ECDC4;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .node-details-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .modal-content {
            background: #1a1a2e;
            padding: 30px;
            border-radius: 12px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            border: 2px solid #4ECDC4;
        }

        .modal-close {
            float: right;
            font-size: 24px;
            cursor: pointer;
            color: #888;
        }

        .modal-close:hover {
            color: #FF6B6B;
        }

        .graph-mini {
            height: 300px;
            background: #0a0a1e;
            border-radius: 8px;
            margin-top: 20px;
        }

        .export-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }

        .export-buttons .btn {
            flex: 1;
        }

        .search-box {
            position: relative;
        }

        .search-box input {
            padding-left: 40px;
        }

        .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #888;
        }

        .all-nodes-container {
            max-height: 600px;
            overflow-y: auto;
        }

        .filter-row {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }

        .filter-row .form-group {
            flex: 1;
            margin-bottom: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Knowledge Graph Query Interface</h1>
            <p class="subtitle">Query, explore, and export knowledge graph data</p>
        </header>

        <div class="main-content">
            <div class="sidebar">
                <h2 class="section-title">Query Parameters</h2>

                <div class="form-group">
                    <label>Component Name</label>
                    <input type="text" id="componentName" placeholder="e.g., LED Module" value="Automotive LED Module">
                </div>

                <div class="form-group">
                    <label>Component Type</label>
                    <input type="text" id="componentType" placeholder="e.g., Electronic Module" value="LED Module">
                </div>

                <div class="form-group">
                    <label>Application</label>
                    <input type="text" id="application" placeholder="e.g., automotive lighting" value="automotive lighting">
                </div>

                <div class="form-group">
                    <label>Test Level</label>
                    <select id="testLevel">
                        <option value="PCB level">PCB Level</option>
                        <option value="System level">System Level</option>
                        <option value="Component level">Component Level</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Test Categories</label>
                    <div class="checkbox-group">
                        <label class="checkbox-item">
                            <input type="checkbox" value="thermal" checked> Thermal
                        </label>
                        <label class="checkbox-item">
                            <input type="checkbox" value="mechanical" checked> Mechanical
                        </label>
                        <label class="checkbox-item">
                            <input type="checkbox" value="environmental" checked> Environmental
                        </label>
                        <label class="checkbox-item">
                            <input type="checkbox" value="electrical" checked> Electrical
                        </label>
                        <label class="checkbox-item">
                            <input type="checkbox" value="emc"> EMC
                        </label>
                        <label class="checkbox-item">
                            <input type="checkbox" value="durability"> Durability
                        </label>
                    </div>
                </div>

                <div class="form-group">
                    <label>Max Results</label>
                    <input type="number" id="maxResults" value="50" min="1" max="200">
                </div>

                <div class="form-group">
                    <label>Min Confidence</label>
                    <input type="range" id="minConfidence" min="0" max="1" step="0.1" value="0.2">
                    <span id="confidenceValue">0.2</span>
                </div>

                <button class="btn btn-primary" onclick="queryGraph()">
                    🔍 Query Knowledge Graph
                </button>

                <button class="btn btn-secondary" onclick="loadAllNodes()">
                    📊 Load All Nodes
                </button>

                <button class="btn btn-success" onclick="exportToExcel('xlsx')">
                    📥 Export to Excel
                </button>

                <button class="btn btn-primary" onclick="exportToExcel('docx')" style="margin-top: 10px; background: linear-gradient(135deg, #2C3E50 0%, #4CA1AF 100%);">
                    📄 Export to Word
                </button>
            </div>

            <div class="results-panel">
                <div class="tabs">
                    <div class="tab active" onclick="switchTab('query')">Query Results</div>
                    <div class="tab" onclick="switchTab('nodes')">All Nodes</div>
                    <div class="tab" onclick="switchTab('graph')">Graph View</div>
                </div>

                <div id="queryTab" class="tab-content active">
                    <div class="stats-bar">
                        <div class="stat-card">
                            <div class="stat-value" id="totalResults">0</div>
                            <div class="stat-label">Results Found</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="avgConfidence">0%</div>
                            <div class="stat-label">Avg Confidence</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="uniqueStandards">0</div>
                            <div class="stat-label">Standards Referenced</div>
                        </div>
                    </div>

                    <div id="queryResults">
                        <div class="loading" style="display: none;">
                            <div class="loading-spinner"></div>
                            <p>Querying knowledge graph...</p>
                        </div>
                        <p style="color: #888; text-align: center; padding: 50px;">
                            Enter query parameters and click "Query Knowledge Graph" to see results
                        </p>
                    </div>
                </div>

                <div id="nodesTab" class="tab-content">
                    <div class="filter-row">
                        <div class="form-group search-box">
                            <span class="search-icon">🔍</span>
                            <input type="text" id="nodeSearch" placeholder="Search nodes..." onkeyup="filterNodes()">
                        </div>
                        <div class="form-group">
                            <select id="nodeTypeFilter" onchange="filterNodes()">
                                <option value="">All Types</option>
                                <option value="Standard">Standards</option>
                                <option value="Clause">Clauses</option>
                                <option value="Requirement">Requirements</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <select id="documentFilter" onchange="filterNodes()">
                                <option value="">All Documents</option>
                            </select>
                        </div>
                    </div>

                    <div class="stats-bar">
                        <div class="stat-card">
                            <div class="stat-value" id="totalNodes">0</div>
                            <div class="stat-label">Total Nodes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="totalEdges">0</div>
                            <div class="stat-label">Total Edges</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="displayedNodes">0</div>
                            <div class="stat-label">Displayed</div>
                        </div>
                    </div>

                    <div id="allNodesResults" class="all-nodes-container">
                        <p style="color: #888; text-align: center; padding: 50px;">
                            Click "Load All Nodes" to view all nodes in the graph
                        </p>
                    </div>
                </div>

                <div id="graphTab" class="tab-content">
                    <div class="graph-mini" id="miniGraph"></div>
                    <p style="color: #888; text-align: center; margin-top: 15px;">
                        Interactive graph visualization. Click nodes for details.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <div class="node-details-modal" id="nodeModal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <h2 style="color: #4ECDC4; margin-bottom: 20px;">Node Details</h2>
            <div id="modalContent"></div>
        </div>
    </div>

    <script>
        let allNodesData = [];
        let queryResultsData = [];

        // Update confidence value display
        document.getElementById('minConfidence').addEventListener('input', function() {
            document.getElementById('confidenceValue').textContent = this.value;
        });

        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tab + 'Tab').classList.add('active');

            if (tab === 'graph' && queryResultsData.length > 0) {
                renderMiniGraph();
            }
        }

        function getSelectedCategories() {
            return Array.from(document.querySelectorAll('.checkbox-group input:checked'))
                .map(cb => cb.value);
        }

        async function queryGraph() {
            const queryContainer = document.getElementById('queryResults');
            queryContainer.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Querying knowledge graph...</p></div>';

            const categories = getSelectedCategories();

            const requestBody = {
                component_profile: {
                    name: document.getElementById('componentName').value,
                    type: document.getElementById('componentType').value,
                    application: document.getElementById('application').value,
                    variants: ["Standard"],
                    test_level: document.getElementById('testLevel').value,
                    applicable_standards: ["ISO 16750", "IEC 60068", "BS EN 50174"],
                    test_categories: categories,
                    quantity_per_test: {"Sample": 5}
                },
                retrieval_method: "hybrid",
                max_results: parseInt(document.getElementById('maxResults').value),
                min_confidence: parseFloat(document.getElementById('minConfidence').value)
            };

            try {
                const response = await fetch('/api/v1/retrieval/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody)
                });

                const data = await response.json();
                queryResultsData = data.results || [];
                displayQueryResults(data);
            } catch (error) {
                queryContainer.innerHTML = `<p style="color: #FF6B6B; text-align: center;">Error: ${error.message}</p>`;
            }
        }

        function displayQueryResults(data) {
            const container = document.getElementById('queryResults');
            const results = data.results || [];

            // Update stats
            document.getElementById('totalResults').textContent = results.length;

            if (results.length > 0) {
                const avgConf = results.reduce((sum, r) => sum + (r.relevance_score || 0), 0) / results.length;
                document.getElementById('avgConfidence').textContent = (avgConf * 100).toFixed(1) + '%';

                const standards = new Set(results.map(r => r.parent_clause?.split('::')[0] || ''));
                document.getElementById('uniqueStandards').textContent = standards.size;
            }

            if (results.length === 0) {
                container.innerHTML = '<p style="color: #888; text-align: center; padding: 50px;">No results found. Try adjusting your query parameters.</p>';
                return;
            }

            let html = `
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>ID</th>
                            <th>Requirement Text</th>
                            <th>Parent Clause</th>
                            <th>Confidence</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            results.forEach((result, idx) => {
                const confidence = (result.relevance_score * 100).toFixed(1);
                html += `
                    <tr>
                        <td><span class="node-type ${result.node_type || 'Requirement'}">${result.node_type || 'Requirement'}</span></td>
                        <td style="font-family: monospace; font-size: 12px;">${result.requirement_id || result.node_id}</td>
                        <td class="requirement-text">${result.text || 'N/A'}</td>
                        <td>${result.parent_clause || 'N/A'}</td>
                        <td>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div class="confidence-bar">
                                    <div class="confidence-fill" style="width: ${confidence}%"></div>
                                </div>
                                <span>${confidence}%</span>
                            </div>
                        </td>
                        <td>
                            <button class="btn btn-secondary" style="padding: 5px 10px; font-size: 12px;" onclick='showDetails(${JSON.stringify(result).replace(/'/g, "\\'")})'>View</button>
                        </td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
            container.innerHTML = html;
        }

        async function loadAllNodes() {
            const container = document.getElementById('allNodesResults');
            container.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Loading all nodes...</p></div>';

            try {
                const response = await fetch('/api/v1/visualization/graph-data?max_nodes=1500');
                const data = await response.json();

                allNodesData = data.nodes || [];

                // Update stats
                document.getElementById('totalNodes').textContent = data.total_nodes;
                document.getElementById('totalEdges').textContent = data.total_links;

                // Populate document filter
                const documents = [...new Set(allNodesData.map(n => n.document_id).filter(d => d))];
                const docFilter = document.getElementById('documentFilter');
                docFilter.innerHTML = '<option value="">All Documents</option>';
                documents.forEach(doc => {
                    docFilter.innerHTML += `<option value="${doc}">${doc}</option>`;
                });

                displayNodes(allNodesData);

                // Switch to nodes tab
                switchTab('nodes');
                document.querySelectorAll('.tab')[1].classList.add('active');
                document.querySelectorAll('.tab')[0].classList.remove('active');

            } catch (error) {
                container.innerHTML = `<p style="color: #FF6B6B; text-align: center;">Error: ${error.message}. Make sure the graph is built first.</p>`;
            }
        }

        function displayNodes(nodes) {
            const container = document.getElementById('allNodesResults');
            document.getElementById('displayedNodes').textContent = nodes.length;

            if (nodes.length === 0) {
                container.innerHTML = '<p style="color: #888; text-align: center; padding: 50px;">No nodes match your filters.</p>';
                return;
            }

            let html = `
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>Node ID</th>
                            <th>Label</th>
                            <th>Document</th>
                            <th>Clause ID</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            nodes.forEach(node => {
                html += `
                    <tr onclick='showNodeModal(${JSON.stringify(node).replace(/'/g, "\\'")})' style="cursor: pointer;">
                        <td><span class="node-type ${node.type}">${node.type}</span></td>
                        <td style="font-family: monospace; font-size: 12px;">${node.id}</td>
                        <td>${node.label}</td>
                        <td>${node.document_id || 'N/A'}</td>
                        <td>${node.clause_id || 'N/A'}</td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
            container.innerHTML = html;
        }

        function filterNodes() {
            const search = document.getElementById('nodeSearch').value.toLowerCase();
            const typeFilter = document.getElementById('nodeTypeFilter').value;
            const docFilter = document.getElementById('documentFilter').value;

            const filtered = allNodesData.filter(node => {
                const matchSearch = !search ||
                    node.id.toLowerCase().includes(search) ||
                    node.label.toLowerCase().includes(search);
                const matchType = !typeFilter || node.type === typeFilter;
                const matchDoc = !docFilter || node.document_id === docFilter;

                return matchSearch && matchType && matchDoc;
            });

            displayNodes(filtered);
        }

        function showDetails(result) {
            const modal = document.getElementById('nodeModal');
            const content = document.getElementById('modalContent');

            content.innerHTML = `
                <p><strong>Node ID:</strong> ${result.node_id || result.requirement_id}</p>
                <p><strong>Type:</strong> <span class="node-type ${result.node_type || 'Requirement'}">${result.node_type || 'Requirement'}</span></p>
                <p><strong>Requirement Type:</strong> ${result.requirement_type || 'N/A'}</p>
                <p><strong>Text:</strong></p>
                <p style="background: #0a0a1e; padding: 15px; border-radius: 8px; line-height: 1.6;">${result.text || 'N/A'}</p>
                <p><strong>Keyword:</strong> ${result.keyword || 'N/A'}</p>
                <p><strong>Parent Clause:</strong> ${result.parent_clause || 'N/A'}</p>
                <p><strong>Relevance Score:</strong> ${((result.relevance_score || 0) * 100).toFixed(2)}%</p>
                <p><strong>Retrieval Method:</strong> ${result.retrieval_method || 'N/A'}</p>
            `;

            modal.style.display = 'flex';
        }

        function showNodeModal(node) {
            const modal = document.getElementById('nodeModal');
            const content = document.getElementById('modalContent');

            content.innerHTML = `
                <p><strong>Node ID:</strong> ${node.id}</p>
                <p><strong>Type:</strong> <span class="node-type ${node.type}">${node.type}</span></p>
                <p><strong>Label:</strong> ${node.label}</p>
                <p><strong>Document:</strong> ${node.document_id || 'N/A'}</p>
                <p><strong>Clause ID:</strong> ${node.clause_id || 'N/A'}</p>
            `;

            modal.style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('nodeModal').style.display = 'none';
        }

        async function exportToExcel(format = 'xlsx') {
            if (queryResultsData.length === 0 && allNodesData.length === 0) {
                alert('Please query the graph or load nodes first before exporting.');
                return;
            }

            const dataToExport = queryResultsData.length > 0 ? queryResultsData : allNodesData;

            // Create test cases from query results
            const testCases = queryResultsData.map((result, idx) => ({
                test_id: `B${idx + 1}`,
                test_standard: result.parent_clause?.split('::')[0] || 'N/A',
                test_description: result.text?.substring(0, 100) || 'Test procedure',
                test_procedure: result.text || 'Verify requirement compliance',
                acceptance_criteria: 'Meets specification requirements',
                test_responsibility: 'Supplier',
                test_stage: 'DVP',
                quantity: 'Sample: 5',
                estimated_days: 5,
                pcb_or_lamp: document.getElementById('testLevel').value,
                remarks: '',
                traceability: {
                    requirement_id: result.requirement_id || result.node_id,
                    source_clause: result.parent_clause || '',
                    source_standard: result.parent_clause?.split('::')[0] || '',
                    requirement_type: result.requirement_type || 'mandatory',
                    confidence_score: result.relevance_score || 0
                }
            }));

            if (testCases.length === 0) {
                alert('No query results to export. Please run a query first.');
                return;
            }

            const requestBody = {
                component_profile: {
                    name: document.getElementById('componentName').value,
                    type: document.getElementById('componentType').value,
                    application: document.getElementById('application').value,
                    variants: ["Standard"],
                    test_level: document.getElementById('testLevel').value,
                    applicable_standards: ["ISO 16750", "IEC 60068"],
                    test_categories: getSelectedCategories(),
                    quantity_per_test: {"Sample": 5}
                },
                test_cases: testCases,
                output_format: format,
                include_traceability_sheet: true,
                include_visualization: false
            };

            try {
                const response = await fetch('/api/v1/dvp/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody)
                });

                const data = await response.json();

                if (data.job_id) {
                    const formatName = format === 'docx' ? 'Word' : 'Excel';
                    alert(formatName + ' generation started! Job ID: ' + data.job_id + '\\n\\nCheck /api/v1/dvp/list for download link.');

                    // Poll for completion
                    setTimeout(async () => {
                        const statusResp = await fetch('/api/v1/dvp/status/' + data.job_id);
                        const status = await statusResp.json();

                        if (status.status === 'completed' && status.result) {
                            window.open('/api/v1/dvp/download/' + status.result.dvp_id, '_blank');
                        }
                    }, 2000);
                }
            } catch (error) {
                alert('Error exporting: ' + error.message);
            }
        }

        function renderMiniGraph() {
            const container = document.getElementById('miniGraph');
            container.innerHTML = '';

            if (queryResultsData.length === 0) {
                container.innerHTML = '<p style="color: #888; text-align: center; padding: 50px;">Run a query first to see the graph</p>';
                return;
            }

            // Create nodes and links from query results
            const nodes = queryResultsData.map((r, i) => ({
                id: r.node_id || r.requirement_id,
                label: (r.text || '').substring(0, 30) + '...',
                type: r.node_type || 'Requirement'
            }));

            const width = container.clientWidth;
            const height = 300;

            const svg = d3.select('#miniGraph')
                .append('svg')
                .attr('width', width)
                .attr('height', height);

            const simulation = d3.forceSimulation(nodes)
                .force('charge', d3.forceManyBody().strength(-100))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(30));

            const colorMap = {
                'Standard': '#FF6B6B',
                'Clause': '#4ECDC4',
                'Requirement': '#45B7D1'
            };

            const node = svg.append('g')
                .selectAll('circle')
                .data(nodes)
                .enter()
                .append('circle')
                .attr('r', 8)
                .attr('fill', d => colorMap[d.type] || '#999')
                .attr('stroke', '#fff')
                .attr('stroke-width', 2);

            simulation.on('tick', () => {
                node
                    .attr('cx', d => Math.max(10, Math.min(width - 10, d.x)))
                    .attr('cy', d => Math.max(10, Math.min(height - 10, d.y)));
            });
        }

        // Close modal on outside click
        window.onclick = function(event) {
            const modal = document.getElementById('nodeModal');
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        }
    </script>
</body>
</html>
    """

    return HTMLResponse(content=html_content)

@router.get("/statistics-visual", response_class=HTMLResponse)
async def statistics_visualization():
    """
    **Statistical Visualization Dashboard**

    Shows comprehensive statistics about the knowledge graph:
    - Node distribution by type
    - Edge distribution by linking method
    - Document coverage
    - Requirement breakdown
    """

    from app.api.v1.graph import graph_builder

    if not graph_builder:
        return HTMLResponse(content="<h1>Please build the graph first by calling /graph/build</h1>")

    stats = graph_builder.get_statistics()

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Knowledge Graph Statistics</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #1a1a1a;
            color: #fff;
        }}

        h1 {{
            text-align: center;
            color: #4ECDC4;
        }}

        .dashboard {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .chart {{
            background: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}
    </style>
</head>
<body>
    <h1>Knowledge Graph Statistics Dashboard</h1>

    <div class="dashboard">
        <div class="chart">
            <div id="nodesPie"></div>
        </div>

        <div class="chart">
            <div id="edgesBar"></div>
        </div>

        <div class="chart full-width">
            <div id="overview"></div>
        </div>
    </div>

    <script>
        const stats = {json.dumps(stats)};

        // Nodes distribution pie chart
        const nodeData = [{{
            values: [
                stats.standards,
                stats.clauses,
                stats.requirements,
                stats.external_standards || 0
            ],
            labels: ['Standards', 'Clauses', 'Requirements', 'External Standards'],
            type: 'pie',
            marker: {{
                colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
            }}
        }}];

        const nodeLayout = {{
            title: 'Node Distribution by Type',
            paper_bgcolor: '#2a2a2a',
            plot_bgcolor: '#2a2a2a',
            font: {{ color: '#fff' }}
        }};

        Plotly.newPlot('nodesPie', nodeData, nodeLayout);

        // Overview table
        const overviewData = [{{
            type: 'table',
            header: {{
                values: ['Metric', 'Count'],
                align: 'left',
                fill: {{ color: '#4ECDC4' }},
                font: {{ color: '#1a1a1a', size: 14, family: 'Arial' }}
            }},
            cells: {{
                values: [
                    ['Total Nodes', 'Total Edges', 'Standards', 'Clauses', 'Requirements', 'External Standards'],
                    [stats.nodes, stats.edges, stats.standards, stats.clauses, stats.requirements, stats.external_standards || 0]
                ],
                align: 'left',
                fill: {{ color: '#2a2a2a' }},
                font: {{ color: '#fff', size: 12 }}
            }}
        }}];

        const overviewLayout = {{
            title: 'Graph Overview',
            paper_bgcolor: '#2a2a2a',
            plot_bgcolor: '#2a2a2a',
            font: {{ color: '#fff' }}
        }};

        Plotly.newPlot('overview', overviewData, overviewLayout);
    </script>
</body>
</html>
    """

    return HTMLResponse(content=html_content)
