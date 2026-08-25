"""Batch evaluation orchestration for the local RAG agent."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from app.tests.evals.ragas_config import RAGASConfig
from app.tests.evals.retrieval import expected_sources_are_retrieved, normalize_agent_result

REQUIRED_FIELDS = {"question", "ground_truth", "reference_contexts", "metadata"}


@dataclass
class EvaluationCaseResult:
    case_id: str
    question: str
    category: str
    difficulty: str
    answer: str = ""
    ground_truth: str = ""
    reference_contexts: list[str] = field(default_factory=list)
    contexts: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    metrics: dict[str, float | None] = field(default_factory=dict)
    checks: dict[str, bool] = field(default_factory=dict)
    status: str = "passed"
    error: str | None = None


def validate_record(record: dict[str, Any], index: int) -> None:
    missing = REQUIRED_FIELDS - record.keys()
    if missing:
        raise ValueError(f"Record {index} is missing fields: {', '.join(sorted(missing))}")
    if not isinstance(record["reference_contexts"], list):
        raise TypeError(f"Record {index} reference_contexts must be a list.")


def build_evaluation_dataset(records: list[dict[str, Any]], answers: list[str] | None = None) -> Any:
    """Map repository records to RAGAS samples, importing RAGAS on demand.
    
    Maps input records to RAGAS SingleTurnSample with proper field normalization:
    - reference_contexts (input) -> retrieved_contexts (RAGAS)
    - question (input) -> user_input (RAGAS)
    - answer (input) -> response (RAGAS)
    - ground_truth (input) -> reference (RAGAS)
    """
    from ragas.dataset_schema import EvaluationDataset, SingleTurnSample

    samples = []
    for index, record in enumerate(records):
        # Use provided answers or fall back to record answer
        answer = answers[index] if answers and index < len(answers) else record.get("answer", "")
        # Map reference_contexts from input to retrieved_contexts expected by RAGAS
        contexts = record.get("retrieved_contexts") or record.get("reference_contexts", [])
        samples.append(
            SingleTurnSample(
                user_input=record["question"],
                retrieved_contexts=contexts,
                response=answer,
                reference=record["ground_truth"],
            )
        )
    return EvaluationDataset(samples=samples)


def build_metric_instances(config: type[RAGASConfig] = RAGASConfig) -> list[Any]:
    """Create enabled RAGAS metrics using the installed RAGAS API."""
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import metrics as ragas_metrics
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.run_config import RunConfig

    run_config = RunConfig(timeout=120, max_retries=3, max_wait=30, max_workers=4, log_tenacity=True)
    judge_llm = LangchainLLMWrapper(
        ChatOpenAI(model=config.LLM_MODEL, temperature=config.TEMPERATURE, timeout=120, max_retries=3),
        run_config=run_config,
    )
    judge_embeddings = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(model=config.EMBEDDINGS_MODEL, timeout=120, max_retries=3),
        run_config=run_config,
    )
    metric_types = {
        "faithfulness": {"llm": judge_llm},
        "answer_relevancy": {"llm": judge_llm, "embeddings": judge_embeddings},
        "context_precision": {"llm": judge_llm},
        "context_recall": {"llm": judge_llm}
    }
    instances = []
    for name, enabled in config.METRICS.items():
        if not enabled:
            continue
        metric_type = getattr(ragas_metrics, "".join(part.title() for part in name.split("_")), None)
        if metric_type is None:
            raise ValueError(f"Enabled RAGAS metric is unavailable: {name}")
        instances.append(metric_type(**metric_types[name]))
    return instances


def _as_score(value: Any) -> float | None:
    """Convert a RAGAS metric value to a bounded float score in [0.0, 1.0].
    
    Returns:
        A float score bounded to [0.0, 1.0], or None if the value cannot be converted.
    """
    try:
        score = float(value)
        # Ensure score is finite (not inf, -inf, or nan)
        if not math.isfinite(score):
            return None
        # Clamp to [0.0, 1.0] range
        return max(0.0, min(1.0, score))
    except (TypeError, ValueError):
        return None


def _matches_expected_behavior(answer: str, record: dict[str, Any]) -> bool:
    tags = record.get("metadata", {}).get("evaluation_tags", [])
    refusal_tags = {"refusal_check", "prompt_injection", "out_of_scope", "domain_boundary"}
    if not refusal_tags.intersection(tags):
        return bool(answer.strip())
    refusal_markers = ("cannot", "can't", "do not have", "don't have", "only answer", "not enough information")
    normalized_answer = answer.casefold()
    has_refusal = any(marker in normalized_answer for marker in refusal_markers)
    forbidden_claims = [claim.casefold() for claim in record.get("forbidden_claims", [])]
    return has_refusal and not any(claim in normalized_answer for claim in forbidden_claims)


def run_ragas(records: list[dict[str, Any]], answers: list[str], config: type[RAGASConfig] = RAGASConfig) -> list[dict[str, float | None]]:
    """Run enabled RAGAS metrics and return one continuous-score map per record.
    
    Args:
        records: Input evaluation records with required fields.
        answers: Evaluated answers corresponding to each record.
        config: RAGAS configuration class.
        
    Returns:
        List of score maps (one per record) with metric names as keys and scores [0.0, 1.0] as values.
        Returns empty score maps if no metrics are enabled or evaluation fails.
    """
    config.validate(require_api_key=True)
    
    if not records or not answers:
        return [{} for _ in records] if records else []
    
    from ragas import evaluate

    try:
        metrics = build_metric_instances(config)
        if not metrics:
            return [{} for _ in records]

        dataset = build_evaluation_dataset(records, answers)
        result = evaluate(dataset=dataset, metrics=metrics, show_progress=False)
        frame = result.to_pandas()
        
        score_maps = []
        for _, row in frame.iterrows():
            score_map = {}
            for metric_name in config.METRICS.keys():
                if metric_name in frame.columns:
                    raw_value = row[metric_name]
                    score = _as_score(raw_value)
                    if score is not None:
                        score_map[metric_name] = score
            score_maps.append(score_map)
        
        return score_maps
    except Exception as exc:
        # Return empty score maps on evaluation failure
        print(f"Warning: RAGAS evaluation failed: {exc}")
        return [{} for _ in records]


def run_batch(
    records: list[dict[str, Any]],
    agent: Any | None = None,
    ragas_runner: Callable[[list[dict[str, Any]], list[str]], list[dict[str, float | None]]] | None = None,
) -> list[EvaluationCaseResult]:
    """Evaluate records with the production agent and local deterministic checks."""
    results: list[EvaluationCaseResult] = []
    answers: list[str] = []
    normalized_records: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        validate_record(record, index)
        metadata = record.get("metadata") or {}
        result = EvaluationCaseResult(
            case_id=record.get("id", f"case-{index + 1:03d}"),
            question=record["question"],
            category=metadata.get("category", "uncategorized"),
            difficulty=metadata.get("difficulty", "unspecified"),
            ground_truth=record["ground_truth"],
            reference_contexts=record["reference_contexts"],
        )
        try:
            agent_result = normalize_agent_result(agent.ask_with_context(record["question"])) if agent else {
                "answer": record.get("answer", ""),
                "contexts": record.get("retrieved_contexts", record["reference_contexts"]),
                "sources": [],
            }
            result.answer = agent_result["answer"]
            result.contexts = agent_result["contexts"]
            result.sources = agent_result["sources"]

            expected_sources = metadata.get("source_docs", [])
            result.checks["expected_sources_retrieved"] = expected_sources_are_retrieved(expected_sources, result.sources) if agent else True
            result.checks["answer_present"] = bool(result.answer.strip())
            result.checks["expected_behavior"] = _matches_expected_behavior(
                result.answer,
                record,
            )
        except Exception as exc:
            result.status = "error"
            result.error = str(exc)

        normalized_records.append({**record, "retrieved_contexts": result.contexts})
        answers.append(result.answer)
        results.append(result)

    if ragas_runner and results:
        try:
            score_maps = ragas_runner(normalized_records, answers)
            if len(score_maps) != len(results):
                raise ValueError("RAGAS returned an unexpected number of results.")
            for result, scores in zip(results, score_maps):
                result.metrics = scores
        except Exception as exc:
            for result in results:
                result.error = f"RAGAS evaluation failed: {exc}"

    for result in results:
        if result.status == "passed" and not all(result.checks.values()):
            result.status = "failed"
    return results


def results_as_dict(results: list[EvaluationCaseResult]) -> list[dict[str, Any]]:
    return [asdict(result) for result in results]


def results_as_json(results: list[EvaluationCaseResult]) -> str:
    return json.dumps(results_as_dict(results), indent=2)
