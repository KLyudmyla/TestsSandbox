import os
from dotenv import load_dotenv

load_dotenv()


class RAGASConfig:
    """Configuration for RAGAS evaluation."""

    # LLM Configuration for RAGAS
    LLM_MODEL = os.getenv("RAGAS_LLM_MODEL", "gpt-4o-mini")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Embeddings Configuration
    EMBEDDINGS_MODEL = os.getenv("RAGAS_EMBEDDINGS_MODEL", "text-embedding-3-small")

    # Evaluation Metrics to use
    METRICS = {
        "faithfulness": True,  # Is answer faithful to retrieved context?
        "answer_relevancy": True,  # Is answer relevant to question?
        "context_precision": True,  # Fraction of context that's relevant?
        "context_recall": True,  # Fraction of relevant context retrieved?
        "context_relevancy": True,  # Is context relevant to the question?
    }

    # Output Configuration
    OUTPUT_DIR = "results"
    RESULTS_FILE = "ragas_results.json"


    @staticmethod
    def validate() -> bool:
        """Validate required configuration."""
        if not RAGASConfig.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables!")
        return True


class RAGASMetricsDescriptions:
    """Descriptions of RAGAS metrics."""

    DESCRIPTIONS = {
        "faithfulness": (
            "Measures if the generated answer is factually consistent with "
            "the retrieved context. Range: [0, 1]. Higher is better."
        ),
        "answer_relevancy": (
            "Measures if the generated answer addresses the question asked. "
            "Range: [0, 1]. Higher is better."
        ),
        "context_precision": (
            "Fraction of retrieved context that is relevant to answer the question. "
            "Range: [0, 1]. Higher is better."
        ),
        "context_recall": (
            "Fraction of relevant context in the corpus that was retrieved. "
            "Range: [0, 1]. Higher is better."
        ),
        "context_relevancy": (
            "Measures if all the retrieved context is relevant to the question. "
            "Range: [0, 1]. Higher is better."
        ),
    }