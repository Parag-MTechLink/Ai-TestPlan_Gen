from app.core.semantic_search import SemanticSearchEngine
from loguru import logger
import sys

# Configure logger to print to stderr
logger.remove()
logger.add(sys.stderr, level="INFO")

try:
    print("Initializing SemanticSearchEngine...")
    engine = SemanticSearchEngine(vector_db_path="./chroma_db")
    print("SemanticSearchEngine initialized.")
except Exception as e:
    print(f"Failed to initialize: {e}")
    sys.exit(1)
