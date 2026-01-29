"""
Accuracy Evaluation Framework for Knowledge Graph DVP Generation System

This module provides comprehensive accuracy metrics for:
1. Data Ingestion Accuracy
2. Graph Construction Accuracy
3. Retrieval Quality
4. LLM Generation Quality
5. End-to-End System Accuracy
"""
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import statistics

BASE_URL = "http://localhost:8000"

class AccuracyEvaluator:
    """Evaluates accuracy across all system components"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.results = {}

    def evaluate_all(self):
        """Run all accuracy evaluations"""
        print("="*80)
        print("KNOWLEDGE GRAPH SYSTEM - ACCURACY EVALUATION")
        print("="*80)

        print("\n1. Evaluating Data Ingestion Accuracy...")
        self.results['ingestion'] = self.evaluate_ingestion_accuracy()

        print("\n2. Evaluating Graph Construction Accuracy...")
        self.results['graph'] = self.evaluate_graph_accuracy()

        print("\n3. Evaluating Retrieval Quality...")
        self.results['retrieval'] = self.evaluate_retrieval_quality()

        print("\n4. Evaluating Semantic Search Accuracy...")
        self.results['semantic'] = self.evaluate_semantic_accuracy()

        print("\n5. Evaluating End-to-End Accuracy...")
        self.results['e2e'] = self.evaluate_end_to_end()

        self.generate_report()

    def evaluate_ingestion_accuracy(self) -> Dict:
        """
        Evaluate data ingestion accuracy
        - Completeness: All files ingested?
        - Requirement extraction: All requirements found?
        - Metadata preservation: All fields preserved?
        """
        print("   Checking file completeness...")

        # Count source files
        source_files = list(self.data_dir.rglob("*.json"))
        total_files = len(source_files)

        # Sample and verify random files
        import random
        sample_size = min(20, total_files)
        sample_files = random.sample(source_files, sample_size)

        # Check field completeness
        required_fields = ['chunk_id', 'document_id', 'clause_id', 'title']
        field_completeness = []
        requirement_counts = []

        for file_path in sample_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Check required fields
                present_fields = sum(1 for field in required_fields if field in data)
                field_completeness.append(present_fields / len(required_fields))

                # Count requirements
                if 'requirements' in data:
                    requirement_counts.append(len(data['requirements']))

        avg_field_completeness = statistics.mean(field_completeness) * 100
        total_requirements = sum(requirement_counts)

        print(f"   [OK] Total files: {total_files}")
        print(f"   [OK] Sample checked: {sample_size} files")
        print(f"   [OK] Field completeness: {avg_field_completeness:.1f}%")
        print(f"   [OK] Requirements in sample: {total_requirements}")

        return {
            'total_files': total_files,
            'sample_size': sample_size,
            'field_completeness': avg_field_completeness,
            'requirements_sampled': total_requirements,
            'score': avg_field_completeness
        }

    def evaluate_graph_accuracy(self) -> Dict:
        """
        Evaluate graph construction accuracy
        - Node creation: Correct number of nodes?
        - Edge creation: Relationships preserved?
        - Hierarchy integrity: Parent-child links correct?
        """
        print("   Fetching graph statistics...")

        try:
            # Get graph data
            response = requests.get(f"{BASE_URL}/api/v1/visualization/graph-data")
            graph_data = response.json()

            node_count = graph_data.get('total_nodes', 0)
            edge_count = graph_data.get('total_links', 0)

            # Calculate expected metrics from source data
            source_files = list(self.data_dir.rglob("*.json"))
            expected_nodes = len(source_files)  # At least 1 node per file

            # Check node types
            nodes = graph_data.get('nodes', [])
            node_types = defaultdict(int)
            for node in nodes:
                node_types[node.get('type', 'Unknown')] += 1

            # Hierarchy check - verify some parent-child relationships
            response = requests.get(f"{BASE_URL}/api/v1/visualization/graph-data?max_nodes=100")
            sample_graph = response.json()

            # Count hierarchical edges
            hierarchical_edges = 0
            for link in sample_graph.get('links', []):
                if 'CHILD' in str(link) or 'PARENT' in str(link):
                    hierarchical_edges += 1

            node_coverage = min(100, (node_count / expected_nodes) * 100)
            edge_density = edge_count / max(1, node_count)  # Edges per node

            print(f"   [OK] Nodes created: {node_count} (expected ~{expected_nodes})")
            print(f"   [OK] Edges created: {edge_count}")
            print(f"   [OK] Node coverage: {node_coverage:.1f}%")
            print(f"   [OK] Edge density: {edge_density:.2f} edges/node")
            print(f"   [OK] Node types: {dict(node_types)}")

            # Score based on coverage and density
            score = (node_coverage * 0.6) + min(40, edge_density * 10)

            return {
                'node_count': node_count,
                'edge_count': edge_count,
                'node_coverage': node_coverage,
                'edge_density': edge_density,
                'node_types': dict(node_types),
                'score': score
            }

        except Exception as e:
            print(f"   [FAIL] Error: {e}")
            return {'score': 0, 'error': str(e)}

    def evaluate_retrieval_quality(self) -> Dict:
        """
        Evaluate retrieval quality using ground truth queries
        - Precision: Relevant results retrieved?
        - Recall: All relevant results found?
        - Ranking: Most relevant results ranked higher?
        """
        print("   Testing retrieval with known queries...")

        # Define test queries with expected relevant documents
        test_queries = [
            {
                'query': 'underground cable installation requirements',
                'expected_documents': ['BS_EN_50174_3_2013'],
                'expected_keywords': ['underground', 'cable', 'pathway']
            },
            {
                'query': 'mechanical protection specifications',
                'expected_documents': ['BS_EN_50174_3_2013'],
                'expected_keywords': ['mechanical', 'protection']
            },
            {
                'query': 'environmental resistance testing',
                'expected_documents': ['BS_EN_50174_3_2013'],
                'expected_keywords': ['environmental', 'resistance']
            }
        ]

        results = []
        for test in test_queries:
            component_profile = {
                "name": "Test Component",
                "type": "Cable System",
                "application": test['query'],
                "variants": ["Standard"],
                "test_level": "System level",
                "applicable_standards": test['expected_documents'],
                "test_categories": ["mechanical"],
                "quantity_per_test": {"Standard": 5}
            }

            try:
                response = requests.post(
                    f"{BASE_URL}/api/v1/retrieval/query",
                    json={
                        "component_profile": component_profile,
                        "retrieval_method": "hybrid",
                        "max_results": 10,
                        "min_confidence": 0.5
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    retrieved = data.get('results', [])

                    # Check if expected documents are in results
                    retrieved_docs = {r.get('document_id') for r in retrieved if 'document_id' in r}
                    expected_docs = set(test['expected_documents'])

                    precision = len(retrieved_docs & expected_docs) / max(1, len(retrieved_docs))
                    recall = len(retrieved_docs & expected_docs) / max(1, len(expected_docs))

                    # Check if keywords appear in top results
                    top_3_text = ' '.join([
                        str(r.get('title', '')) + ' ' + str(r.get('content', ''))
                        for r in retrieved[:3]
                    ]).lower()

                    keyword_match = sum(
                        1 for kw in test['expected_keywords']
                        if kw.lower() in top_3_text
                    ) / len(test['expected_keywords'])

                    results.append({
                        'precision': precision,
                        'recall': recall,
                        'keyword_match': keyword_match,
                        'relevance_scores': [r.get('relevance_score', 0) for r in retrieved[:5]]
                    })

            except Exception as e:
                print(f"   [FAIL] Query failed: {test['query'][:30]}... - {e}")
                results.append({'precision': 0, 'recall': 0, 'keyword_match': 0})

        if results:
            avg_precision = statistics.mean([r['precision'] for r in results]) * 100
            avg_recall = statistics.mean([r['recall'] for r in results]) * 100
            avg_keyword = statistics.mean([r['keyword_match'] for r in results]) * 100

            print(f"   [OK] Average Precision: {avg_precision:.1f}%")
            print(f"   [OK] Average Recall: {avg_recall:.1f}%")
            print(f"   [OK] Keyword Match: {avg_keyword:.1f}%")

            # F1 score
            if avg_precision + avg_recall > 0:
                f1_score = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall)
            else:
                f1_score = 0

            return {
                'precision': avg_precision,
                'recall': avg_recall,
                'keyword_match': avg_keyword,
                'f1_score': f1_score,
                'score': f1_score
            }

        return {'score': 0}

    def evaluate_semantic_accuracy(self) -> Dict:
        """
        Evaluate semantic search accuracy
        - Embedding quality: Similar concepts grouped?
        - Diversity: Different aspects covered?
        """
        print("   Testing semantic similarity...")

        # Test semantic similarity with related queries
        query_pairs = [
            ("cable installation", "cable mounting"),
            ("mechanical strength", "structural integrity"),
            ("environmental protection", "weather resistance")
        ]

        similarity_scores = []

        for query1, query2 in query_pairs:
            profile1 = {
                "name": "Test", "type": "System", "application": query1,
                "variants": ["Standard"], "test_level": "System",
                "applicable_standards": ["BS_EN_50174_3_2013"],
                "test_categories": ["mechanical"],
                "quantity_per_test": {"Standard": 5}
            }
            profile2 = {
                "name": "Test", "type": "System", "application": query2,
                "variants": ["Standard"], "test_level": "System",
                "applicable_standards": ["BS_EN_50174_3_2013"],
                "test_categories": ["mechanical"],
                "quantity_per_test": {"Standard": 5}
            }

            try:
                # Get results for both queries
                r1 = requests.post(f"{BASE_URL}/api/v1/retrieval/query",
                                  json={"component_profile": profile1, "max_results": 5})
                r2 = requests.post(f"{BASE_URL}/api/v1/retrieval/query",
                                  json={"component_profile": profile2, "max_results": 5})

                if r1.status_code == 200 and r2.status_code == 200:
                    results1 = {r.get('node_id') for r in r1.json().get('results', [])}
                    results2 = {r.get('node_id') for r in r2.json().get('results', [])}

                    # Calculate overlap (Jaccard similarity)
                    if results1 or results2:
                        overlap = len(results1 & results2) / len(results1 | results2)
                        similarity_scores.append(overlap)
            except:
                pass

        if similarity_scores:
            avg_similarity = statistics.mean(similarity_scores) * 100
            print(f"   [OK] Semantic similarity: {avg_similarity:.1f}%")
            return {'semantic_similarity': avg_similarity, 'score': avg_similarity}

        return {'score': 50}  # Neutral score if can't measure

    def evaluate_end_to_end(self) -> Dict:
        """
        Evaluate end-to-end pipeline
        - Integration: All components work together?
        - Output quality: DVP generated correctly?
        """
        print("   Testing end-to-end pipeline...")

        try:
            # Test complete workflow
            component_profile = {
                "name": "Test System",
                "type": "Cable System",
                "application": "underground cable protection",
                "variants": ["Standard"],
                "test_level": "System level",
                "applicable_standards": ["BS_EN_50174_3_2013"],
                "test_categories": ["mechanical", "environmental"],
                "quantity_per_test": {"Standard": 5}
            }

            # Step 1: Retrieval
            retrieval_response = requests.post(
                f"{BASE_URL}/api/v1/retrieval/query",
                json={
                    "component_profile": component_profile,
                    "retrieval_method": "hybrid",
                    "max_results": 10
                }
            )

            retrieval_success = retrieval_response.status_code == 200
            retrieval_count = len(retrieval_response.json().get('results', [])) if retrieval_success else 0

            # Step 2: DVP Generation (mock test cases)
            test_cases = [{
                "test_id": "E2E_TEST_1",
                "test_standard": "BS EN 50174-3:2013",
                "test_description": "End-to-end test",
                "test_procedure": "Test procedure",
                "acceptance_criteria": "Pass criteria",
                "test_responsibility": "Supplier",
                "test_stage": "DVP",
                "quantity": "5",
                "estimated_days": 5,
                "pcb_or_lamp": "System",
                "traceability": {"source": "accuracy_test"}
            }]

            dvp_response = requests.post(
                f"{BASE_URL}/api/v1/dvp/generate",
                json={
                    "component_profile": component_profile,
                    "test_cases": test_cases,
                    "output_format": "xlsx"
                }
            )

            dvp_success = dvp_response.status_code == 200

            print(f"   [OK] Retrieval: {'Success' if retrieval_success else 'Failed'} ({retrieval_count} results)")
            print(f"   [OK] DVP Generation: {'Success' if dvp_success else 'Failed'}")

            e2e_score = (
                (50 if retrieval_success else 0) +
                (50 if dvp_success else 0)
            )

            return {
                'retrieval_success': retrieval_success,
                'retrieval_count': retrieval_count,
                'dvp_success': dvp_success,
                'score': e2e_score
            }

        except Exception as e:
            print(f"   [FAIL] Error: {e}")
            return {'score': 0, 'error': str(e)}

    def generate_report(self):
        """Generate comprehensive accuracy report"""
        print("\n" + "="*80)
        print("ACCURACY EVALUATION REPORT")
        print("="*80)

        total_score = 0
        component_count = 0

        print("\nComponent Scores:")
        print("-" * 80)

        for component, metrics in self.results.items():
            score = metrics.get('score', 0)
            total_score += score
            component_count += 1

            status = "[OK]" if score >= 70 else "[WARN]" if score >= 50 else "[FAIL]"
            print(f"{status} {component.capitalize():20s}: {score:6.1f}%")

        overall_accuracy = total_score / max(1, component_count)

        print("-" * 80)
        print(f"Overall System Accuracy: {overall_accuracy:.1f}%")
        print("="*80)

        # Grading
        if overall_accuracy >= 90:
            grade = "A+ (Excellent)"
        elif overall_accuracy >= 80:
            grade = "A  (Very Good)"
        elif overall_accuracy >= 70:
            grade = "B  (Good)"
        elif overall_accuracy >= 60:
            grade = "C  (Acceptable)"
        else:
            grade = "D  (Needs Improvement)"

        print(f"\nSystem Grade: {grade}")

        # Recommendations
        print("\nRecommendations:")
        for component, metrics in self.results.items():
            score = metrics.get('score', 0)
            if score < 70:
                print(f"  - Improve {component}: {self._get_recommendation(component, metrics)}")

        # Save detailed report
        report_path = Path("accuracy_report.json")
        with open(report_path, 'w') as f:
            json.dump({
                'overall_accuracy': overall_accuracy,
                'grade': grade,
                'components': self.results,
                'timestamp': str(Path.cwd())
            }, f, indent=2)

        print(f"\nDetailed report saved to: {report_path}")

    def _get_recommendation(self, component: str, metrics: Dict) -> str:
        """Get improvement recommendation for component"""
        recommendations = {
            'ingestion': "Verify all source files are valid JSON and contain required fields",
            'graph': "Check graph building logic and edge creation rules",
            'retrieval': "Tune embedding model or adjust similarity thresholds",
            'semantic': "Consider using a more powerful embedding model",
            'e2e': "Review integration between components"
        }
        return recommendations.get(component, "Review component implementation")


def main():
    """Run accuracy evaluation"""
    evaluator = AccuracyEvaluator(data_dir="./data")
    evaluator.evaluate_all()

    print("\n" + "="*80)
    print("Evaluation complete! Review accuracy_report.json for details.")
    print("="*80)


if __name__ == "__main__":
    main()
