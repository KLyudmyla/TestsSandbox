"""RAGAS evaluation framework configuration."""

import os
from dotenv import load_dotenv

load_dotenv()


class RAGASConfig:
    LLM_MODEL = os.getenv("RAGAS_LLM_MODEL", "gpt-4o-mini")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    EVAL_INPUT_COST_PER_MILLION_USD = float(
        os.getenv("RAGAS_EVAL_INPUT_COST_PER_MILLION_USD", "0.15")
    )
    EVAL_OUTPUT_COST_PER_MILLION_USD = float(
        os.getenv("RAGAS_EVAL_OUTPUT_COST_PER_MILLION_USD", "0.60")
    )

    EMBEDDINGS_MODEL = os.getenv("RAGAS_EMBEDDINGS_MODEL", "text-embedding-3-small")
    TEMPERATURE = float(os.getenv("RAGAS_TEMPERATURE", "0"))

    # RAGAS runtime configuration
    RUN_TIMEOUT = int(os.getenv("RAGAS_RUN_TIMEOUT", "120"))
    RUN_MAX_RETRIES = int(os.getenv("RAGAS_RUN_MAX_RETRIES", "3"))
    RUN_MAX_WORKERS = int(os.getenv("RAGAS_RUN_MAX_WORKERS", "4"))

    METRICS = {
        "faithfulness": True,
        "answer_relevancy": True,
        "context_precision": True,
        "context_recall": True,
    }

    FAITHFULNESS_MIN_THRESHOLD = 0.70
    ANSWER_RELEVANCY_MIN_THRESHOLD = 0.65
    CONTEXT_PRECISION_MIN_THRESHOLD = 0.70
    CONTEXT_RECALL_MIN_THRESHOLD = 0.50

    OUTPUT_DIR = "results"

    @classmethod
    def active_metric_names(cls) -> tuple[str, ...]:
        """Returns enabled metric names directly from configuration."""
        return tuple(name for name, enabled in cls.METRICS.items() if enabled)

    @classmethod
    def validate(cls, require_api_key: bool = True) -> bool:
        if require_api_key and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables!")
        return True
