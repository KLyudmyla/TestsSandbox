"""RAGAS evaluation framework configuration."""

import os

from dotenv import load_dotenv

load_dotenv()


class RAGASConfig:
    """Configuration for RAGAS evaluation framework.
    
    All metrics are disabled by default in the boolean dict to allow 
    explicit control. Set desired metrics to True to enable them.
    """

    # LLM Configuration for RAGAS - judge model for evaluating responses
    LLM_MODEL = os.getenv("RAGAS_LLM_MODEL", "gpt-4o-mini")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Embeddings Configuration for semantic similarity scoring
    EMBEDDINGS_MODEL = os.getenv("RAGAS_EMBEDDINGS_MODEL", "text-embedding-3-small")
    TEMPERATURE = float(os.getenv("RAGAS_TEMPERATURE", "0"))
    
    # Dataset versioning for reproducibility
    DATASET_VERSION = os.getenv("RAGAS_DATASET_VERSION", "v1")
    CORPUS_VERSION = os.getenv("RAGAS_CORPUS_VERSION", "v1")

    # Evaluation Metrics Configuration
    # Set each to True to enable, False to disable during evaluation
    METRICS = {
        "faithfulness": True,  # Is answer factually consistent with retrieved context? [0.0, 1.0]
        "answer_relevancy": True,  # Is answer relevant to the question asked? [0.0, 1.0]
        "context_precision": True,  # What fraction of retrieved context is relevant? [0.0, 1.0]
        "context_recall": True,  # What fraction of relevant context was retrieved? [0.0, 1.0]
    }

    # Output Configuration
    OUTPUT_DIR = "results"
    RESULTS_FILE = "ragas_results.json"

    @staticmethod
    def validate(require_api_key: bool = True) -> bool:
        """Validate required configuration at runtime.
        
        Args:
            require_api_key: If True, raise error if OPENAI_API_KEY is not set.
            
        Returns:
            True if validation passes.
            
        Raises:
            ValueError: If required configuration is missing.
        """
        if require_api_key and not RAGASConfig.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables!")
        return True


class RAGASMetricsDescriptions:
    """Human-readable descriptions of all RAGAS evaluation metrics.
    
    Each description includes the metric name, what it measures, and the expected
    value range (all are [0.0, 1.0] with higher being better).
    """

    DESCRIPTIONS = {
        "faithfulness": (
            "Measures if the generated answer is factually consistent with "
            "the retrieved context. Range: [0.0, 1.0]. Higher is better."
        ),
        "answer_relevancy": (
            "Measures if the generated answer addresses the question asked. "
            "Range: [0.0, 1.0]. Higher is better."
        ),
        "context_precision": (
            "Fraction of retrieved context that is relevant to answer the question. "
            "Range: [0.0, 1.0]. Higher is better."
        ),
        "context_recall": (
            "Fraction of relevant context in the corpus that was retrieved. "
            "Range: [0.0, 1.0]. Higher is better."
        )
    }

