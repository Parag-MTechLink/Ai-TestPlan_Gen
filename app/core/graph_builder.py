"""
Knowledge Graph Builder
Constructs multi-layer knowledge graph from JSON documents with full traceability
"""
import json
import hashlib
import networkx as nx
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
from loguru import logger

class KnowledgeGraphBuilder:
    """
    Builds a traceable knowledge graph from standards documents
    """

    def __init__(self, seed: int = 42):
        self.graph = nx.MultiDiGraph()
        self.seed = seed
        self.node_count = 0
        self.edge_count = 0
        self.provenance = []

    def build_from_directory(self, data_path: str,
                            enable_structural: bool = True,
                            enable_reference: bool = True) -> Dict[str, Any]:
        """
        Build knowledge graph from JSON files in directory
        """
        logger.info(f"Building knowledge graph from: {data_path}")

        data_dir = Path(data_path)
        if not data_dir.exists():
            raise FileNotFoundError(f"Directory not found: {data_path}")

        # Load all JSON files (sorted for determinism)
        json_files = sorted(list(data_dir.rglob("*.json")))
        logger.info(f"Found {len(json_files)} JSON files")

        documents = []
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_source_file'] = str(json_file.relative_to(data_dir))
                    documents.append(data)
            except Exception as e:
                logger.warning(f"Failed to load {json_file}: {e}")
                continue

        logger.info(f"Loaded {len(documents)} documents successfully")

        # Phase 1: Create nodes
        logger.info("Phase 1: Creating nodes...")
        self._create_nodes(documents)

        # Phase 2: Create structural links
        if enable_structural:
            logger.info("Phase 2: Creating structural links...")
            self._create_structural_links()

        # Phase 3: Create reference links
        if enable_reference:
            logger.info("Phase 3: Creating reference links...")
            self._create_reference_links()

        # Compute graph statistics
        stats = self._compute_statistics()

        logger.info(f"Graph built: {stats['nodes']} nodes, {stats['edges']} edges")

        return {
            'nodes_created': stats['nodes'],
            'edges_created': stats['edges'],
            'standards': stats['standards'],
            'clauses': stats['clauses'],
            'requirements': stats['requirements'],
            'graph_checksum': self._compute_checksum()
        }

    def _create_nodes(self, documents: List[Dict[str, Any]]):
        """
        Create nodes for all entities in documents
        """
        # Track standards
        standards = {}

        for doc in documents:
            chunk_id = doc.get('chunk_id', '')
            document_id = doc.get('document_id', '')

            if not chunk_id or not document_id:
                continue

            # Create standard node if not exists
            if document_id not in standards:
                standards[document_id] = {
                    'node_type': 'Standard',
                    'document_id': document_id,
                    'title': document_id,
                    'created_at': datetime.utcnow().isoformat()
                }
                self.graph.add_node(document_id, **standards[document_id])
                self.node_count += 1

            # Create clause node
            clause_node = {
                'node_type': 'Clause',
                'chunk_id': chunk_id,
                'document_id': document_id,
                'clause_id': doc.get('clause_id', ''),
                'title': doc.get('title', ''),
                'parent_id': doc.get('parent_id'),
                'children_ids': doc.get('children_ids', []),
                'content': doc.get('content', []),
                'tables': doc.get('tables', []),
                'figures': doc.get('figures', []),
                'references': doc.get('references', {}),
                'source_file': doc.get('_source_file', ''),
                'created_at': datetime.utcnow().isoformat()
            }

            # Calculate depth from clause_id
            clause_id = doc.get('clause_id', '')
            if clause_id and clause_id != 'misc':
                parts = clause_id.replace('Annex ', '').split('.')
                clause_node['depth'] = len(parts)
            else:
                clause_node['depth'] = 0

            self.graph.add_node(chunk_id, **clause_node)
            self.node_count += 1

            # Add edge: Standard -> Clause
            self.graph.add_edge(
                document_id,
                chunk_id,
                edge_type='CONTAINS_CLAUSE',
                linking_method='structural',
                confidence=1.0,
                created_at=datetime.utcnow().isoformat()
            )
            self.edge_count += 1

            # Create requirement nodes
            requirements = doc.get('requirements', [])
            for idx, req in enumerate(requirements):
                req_id = f"{chunk_id}::req_{idx}"

                req_node = {
                    'node_type': 'Requirement',
                    'requirement_id': req_id,
                    'parent_clause': chunk_id,
                    'requirement_type': req.get('type', 'unknown'),
                    'keyword': req.get('keyword', ''),
                    'text': req.get('text', ''),
                    'created_at': datetime.utcnow().isoformat()
                }

                self.graph.add_node(req_id, **req_node)
                self.node_count += 1

                # Add edge: Clause -> Requirement
                self.graph.add_edge(
                    chunk_id,
                    req_id,
                    edge_type='CONTAINS_REQUIREMENT',
                    linking_method='structural',
                    confidence=1.0,
                    created_at=datetime.utcnow().isoformat()
                )
                self.edge_count += 1

    def _create_structural_links(self):
        """
        Create parent-child hierarchical links
        """
        # Build lookup by clause_id
        clause_lookup = {}
        for node_id, data in self.graph.nodes(data=True):
            if data.get('node_type') == 'Clause':
                clause_id = data.get('clause_id')
                if clause_id:
                    clause_lookup[clause_id] = node_id

        # Create parent-child edges
        for node_id, data in self.graph.nodes(data=True):
            if data.get('node_type') != 'Clause':
                continue

            parent_id = data.get('parent_id')
            if parent_id and parent_id in clause_lookup:
                parent_node_id = clause_lookup[parent_id]

                # Add parent-child edges
                self.graph.add_edge(
                    parent_node_id,
                    node_id,
                    edge_type='PARENT_OF',
                    linking_method='structural',
                    confidence=1.0,
                    created_at=datetime.utcnow().isoformat()
                )
                self.edge_count += 1

            # Add sibling relationships
            if parent_id and parent_id in clause_lookup:
                parent_node_id = clause_lookup[parent_id]
                parent_data = self.graph.nodes[parent_node_id]
                children = parent_data.get('children_ids', [])

                clause_id = data.get('clause_id')
                if clause_id in children:
                    for sibling_id in children:
                        if sibling_id != clause_id and sibling_id in clause_lookup:
                            sibling_node_id = clause_lookup[sibling_id]

                            # Check if edge already exists
                            if not self.graph.has_edge(node_id, sibling_node_id, key=0):
                                self.graph.add_edge(
                                    node_id,
                                    sibling_node_id,
                                    edge_type='SIBLING_OF',
                                    linking_method='structural',
                                    confidence=1.0,
                                    created_at=datetime.utcnow().isoformat()
                                )
                                self.edge_count += 1

    def _create_reference_links(self):
        """
        Create reference-based links from internal_resolved and standards
        """
        # Build lookup by clause_id
        clause_lookup = {}
        for node_id, data in self.graph.nodes(data=True):
            if data.get('node_type') == 'Clause':
                clause_id = data.get('clause_id')
                if clause_id:
                    clause_lookup[clause_id] = node_id

        # Create reference edges
        # First, collect all nodes to avoid dictionary changed size during iteration
        nodes_list = list(self.graph.nodes(data=True))

        for node_id, data in nodes_list:
            if data.get('node_type') != 'Clause':
                continue

            references = data.get('references', {})

            # Internal references
            internal_refs = references.get('internal_resolved', [])
            for ref_clause_id in internal_refs:
                if ref_clause_id in clause_lookup:
                    ref_node_id = clause_lookup[ref_clause_id]

                    self.graph.add_edge(
                        node_id,
                        ref_node_id,
                        edge_type='REFERENCES',
                        linking_method='reference',
                        confidence=1.0,
                        created_at=datetime.utcnow().isoformat()
                    )
                    self.edge_count += 1

            # Cross-standard references
            std_refs = references.get('standards', [])
            for std_ref in std_refs:
                # Create external standard node if needed
                std_node_id = f"EXT::{std_ref}"
                if not self.graph.has_node(std_node_id):
                    self.graph.add_node(
                        std_node_id,
                        node_type='ExternalStandard',
                        standard_name=std_ref,
                        created_at=datetime.utcnow().isoformat()
                    )
                    self.node_count += 1

                self.graph.add_edge(
                    node_id,
                    std_node_id,
                    edge_type='CITES_STANDARD',
                    linking_method='reference',
                    confidence=1.0,
                    created_at=datetime.utcnow().isoformat()
                )
                self.edge_count += 1

    def _compute_statistics(self) -> Dict[str, Any]:
        """
        Compute graph statistics
        """
        stats = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'standards': 0,
            'clauses': 0,
            'requirements': 0,
            'external_standards': 0
        }

        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('node_type', '')
            if node_type == 'Standard':
                stats['standards'] += 1
            elif node_type == 'Clause':
                stats['clauses'] += 1
            elif node_type == 'Requirement':
                stats['requirements'] += 1
            elif node_type == 'ExternalStandard':
                stats['external_standards'] += 1

        return stats

    def _compute_checksum(self) -> str:
        """
        Compute deterministic checksum of graph
        """
        nodes = sorted(self.graph.nodes(data=True), key=lambda x: x[0])
        edges = sorted(self.graph.edges(data=True, keys=True),
                      key=lambda x: (x[0], x[1], x[2]))

        graph_repr = {
            'nodes': len(nodes),
            'edges': len(edges),
            'node_ids': [n[0] for n in nodes[:10]]  # Sample
        }

        canonical = json.dumps(graph_repr, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def save_graph(self, output_path: str):
        """
        Save graph to file
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save as pickle for fast loading
        import pickle
        with open(output_path, 'wb') as f:
            pickle.dump(self.graph, f)

        logger.info(f"Graph saved to: {output_path}")

    def load_graph(self, input_path: str):
        """
        Load graph from file
        """
        import pickle
        with open(input_path, 'rb') as f:
            self.graph = pickle.load(f)

        self.node_count = self.graph.number_of_nodes()
        self.edge_count = self.graph.number_of_edges()

        logger.info(f"Graph loaded: {self.node_count} nodes, {self.edge_count} edges")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive graph statistics
        """
        return self._compute_statistics()

    def export_json(self, output_path: str):
        """
        Export graph as JSON for external analysis
        """
        graph_data = {
            'nodes': [
                {'id': n, **self.graph.nodes[n]}
                for n in self.graph.nodes()
            ],
            'edges': [
                {'source': u, 'target': v, 'key': k, **data}
                for u, v, k, data in self.graph.edges(data=True, keys=True)
            ],
            'metadata': {
                'created_at': datetime.utcnow().isoformat(),
                'statistics': self._compute_statistics(),
                'checksum': self._compute_checksum()
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2)

        logger.info(f"Graph exported to JSON: {output_path}")
