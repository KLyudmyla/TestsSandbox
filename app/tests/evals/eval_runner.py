"""RAGAS-compatible evaluation runner for the sandbox project.

This module bridges the repository's existing evaluation dataset format with
RAGAS objects so the same records can be reused for local experiments and
future production-style evaluation runs.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ragas import evaluate
from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness

from tests.evals import RAGASConfig

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    question: str
    context: List[str]


@dataclass
class GenerationResult:
    answer: str
    raw_output: Optional[str] = None


@dataclass
class EvaluationResult:
    metrics: Dict[str, float]
    summary: Optional[str] = None


def build_evaluation_dataset(records: List[Dict[str, Any]]) -> EvaluationDataset:
    """Map repository-style records to RAGAS SingleTurnSample objects."""
    samples: List[SingleTurnSample] = []
    for record in records:
        samples.append(
            SingleTurnSample(
                user_input=record.get("question"),
                retrieved_contexts=record.get("contexts") or [],
                response=record.get("answer") or "",
                reference=record.get("ground_truth"),
                rubric=record.get("metadata") or {},
            )
        )
    return EvaluationDataset(samples=samples)


def build_metric_instances(config: type[RAGASConfig] | None = None) -> List[Any]:
    """Create RAGAS metric instances based on the config flags."""
    cfg = config or RAGASConfig
    if not getattr(cfg, "validate", None):
        raise ValueError("RAGASConfig must expose a validate() method")
    cfg.validate()

    metrics: List[Any] = []
    if cfg.METRICS.get("faithfulness"):
        metrics.append(Faithfulness())
    if cfg.METRICS.get("answer_relevancy"):
        metrics.append(AnswerRelevancy())
    if cfg.METRICS.get("context_precision"):
        metrics.append(ContextPrecision())
    if cfg.METRICS.get("context_recall"):
        metrics.append(ContextRecall())
    return metrics


def generate_answer(retrieval_result: RetrievalResult) -> GenerationResult:
    """Create a placeholder generation result for the current example."""
    logger.debug("Generating answer for question: %s", retrieval_result.question)
    answer = retrieval_result.context[0] if retrieval_result.context else ""
    return GenerationResult(answer=answer, raw_output=answer)


def run_evaluation(
    question: str,
    contexts: List[str],
    reference_answer: str,
    config: type[RAGASConfig] | None = None,
) -> EvaluationResult:
    """Run a single-example evaluation flow using a RAGAS-compatible shape."""
    retrieval_result = RetrievalResult(question=question, context=contexts)
    generation_result = generate_answer(retrieval_result)

    sample = SingleTurnSample(
        user_input=question,
        retrieved_contexts=contexts,
        response=generation_result.answer,
        reference=reference_answer,
    )

    metrics = build_metric_instances(config)
    dataset = EvaluationDataset(samples=[sample])

    if not metrics:
        return EvaluationResult(metrics={}, summary="No enabled metrics were configured.")

    result = evaluate(dataset=dataset, metrics=metrics, show_progress=False)
    score_map: Dict[str, float] = {}
    if hasattr(result, "to_pandas"):
        frame = result.to_pandas()
        if not frame.empty:
            for column in frame.columns:
                if column.startswith("faithfulness") or column.startswith("answer_relevancy") or column.startswith("context"):
                    score_map[column] = float(frame[column].iloc[0])
    return EvaluationResult(metrics=score_map, summary=json.dumps(score_map, indent=2))
