"""RAGAS evaluation framework configuration."""

import os

from dotenv import load_dotenv

load_dotenv()


class RAGASConfig:
    # LLM Configuration for RAGAS - judge model for evaluating responses
    LLM_MODEL = os.getenv("RAGAS_LLM_MODEL", "gpt-4o-mini")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    EVAL_INPUT_COST_PER_MILLION_USD = float(
        os.getenv("RAGAS_EVAL_INPUT_COST_PER_MILLION_USD", "0.15")
    )
    EVAL_OUTPUT_COST_PER_MILLION_USD = float(
        os.getenv("RAGAS_EVAL_OUTPUT_COST_PER_MILLION_USD", "0.60")
    )

    # Embeddings Configuration for semantic similarity scoring
    EMBEDDINGS_MODEL = os.getenv("RAGAS_EMBEDDINGS_MODEL", "text-embedding-3-small")
    TEMPERATURE = float(os.getenv("RAGAS_TEMPERATURE", "0"))
    
    # Evaluation Metrics Configuration
    # Set each to True to enable, False to disable during evaluation
    METRICS = {
        "faithfulness": True,  # Is answer factually consistent with retrieved context? [0.0, 1.0]
        "answer_relevancy": True,  # Is answer relevant to the question asked? [0.0, 1.0]
        "context_precision": True,  # What fraction of retrieved context is relevant? [0.0, 1.0]
        "context_recall": True,  # What fraction of relevant context was retrieved? [0.0, 1.0]
    }

    # Minimum Acceptable Thresholds for Metric Pass/Fail Criteria
    FAITHFULNESS_MIN_THRESHOLD = 0.70
    ANSWER_RELEVANCY_MIN_THRESHOLD = 0.65
    CONTEXT_PRECISION_MIN_THRESHOLD = 0.70
    CONTEXT_RECALL_MIN_THRESHOLD = 0.70

    # Output Configuration
    OUTPUT_DIR = "results"

    @staticmethod
    def validate(require_api_key: bool = True) -> bool:
        if require_api_key and not RAGASConfig.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables!")
        return True

