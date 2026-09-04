"""Report writers for evaluation results."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.evaluation.evals_logic.eval_runner import EvaluationCaseResult, results_as_dict
from app.evaluation.evals_logic.ragas_config import RAGASConfig


def write_reports(results: list[EvaluationCaseResult], output_dir: Path, config: dict[str, Any]) -> Path:
    """Write streamlined JSON, CSV, and Markdown reports into a timestamped directory."""
    run_dir = output_dir / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir.mkdir(parents=True, exist_ok=True)

    rows = results_as_dict(results)
    cleaned_rows = [_clean_case_row(row) for row in rows]

    (run_dir / "results.json").write_text(
        json.dumps({"config": config, "results": cleaned_rows}, indent=2), encoding="utf-8"
    )
    _write_csv(cleaned_rows, run_dir / "results.csv")
    (run_dir / "summary.md").write_text(_summary_markdown(rows, config), encoding="utf-8")

    return run_dir


def _clean_case_row(row: dict[str, Any]) -> dict[str, Any]:
    """Strip redundant assertions, full text blobs, and inactive metrics."""
    mode = row.get("evaluation_mode", "answer_from_context")
    applicability = row.get("metric_applicability", {})

    active_metrics = {
        name: val for name, val in row.get("metrics", {}).items()
        if applicability.get(name, False) and val is not None
    }

    failed_checks = [check for check, passed in row.get("checks", {}).items() if not passed]

    retrieval = row.get("retrieval", {})
    token_usage = row.get("token_usage", {})

    return {
        "case_id": row.get("case_id"),
        "category": row.get("category"),
        "difficulty": row.get("difficulty"),
        "evaluation_mode": mode,
        "status": row.get("status"),
        "question": row.get("question"),
        "answer": row.get("answer"),
        "ground_truth": row.get("ground_truth"),
        "sources": row.get("sources"),
        "retrieved_chunk_ids": retrieval.get("retrieved_chunk_ids", []),
        "chunk_recall_at_k": retrieval.get("chunk_recall_at_k"),
        "expected_sources_retrieved": retrieval.get("expected_sources_retrieved"),
        "metrics": active_metrics,
        "failed_checks": failed_checks,
        "input_tokens": token_usage.get("input_tokens_estimate", 0),
        "output_tokens": token_usage.get("output_tokens_estimate", 0),
        "cost_usd": token_usage.get("total_cost_usd", 0.0),
        "error": row.get("error"),
    }


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "case_id", "category", "difficulty", "evaluation_mode", "status",
        "question", "answer", "ground_truth", "sources", "retrieved_chunk_ids",
        "chunk_recall_at_k", "expected_sources_retrieved", "metrics",
        "failed_checks", "input_tokens", "output_tokens", "cost_usd", "error"
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                name: json.dumps(row[name]) if isinstance(row[name], (list, dict)) else row[name]
                for name in fieldnames
            })


def _summary_markdown(rows: list[dict[str, Any]], config: dict[str, Any]) -> str:
    passed = sum(row["status"] == "passed" for row in rows)
    failed = sum(row["status"] == "failed" for row in rows)
    errors = sum(row["status"] == "error" for row in rows)

    metric_values: dict[str, list[float]] = {}
    metric_applicable: dict[str, int] = {}

    for row in rows:
        for name, value in row["metrics"].items():
            if row["metric_applicability"].get(name, True):
                metric_applicable[name] = metric_applicable.get(name, 0) + 1
                if value is not None:
                    metric_values.setdefault(name, []).append(value)

    total_input_tokens = sum(row.get("token_usage", {}).get("input_tokens_estimate", 0) for row in rows)
    total_output_tokens = sum(row.get("token_usage", {}).get("output_tokens_estimate", 0) for row in rows)
    total_cost_usd = sum(row.get("token_usage", {}).get("total_cost_usd", 0.0) for row in rows)

    lines = [
        "# Evaluation Summary",
        "",
        f"- Cases: {len(rows)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Errors: {errors}",
        "",
        "## Average Metrics (Applicable Cases Only)",
        "",
    ]
    if metric_values:
        lines.extend(
            f"- {name}: {sum(values) / len(values):.3f} (coverage: {len(values)}/{metric_applicable.get(name, len(rows))} cases)"
            for name, values in sorted(metric_values.items())
        )
    else:
        lines.append("No metric scores were applicable or produced.")

    lines.extend([
        "", "## Token Usage & Cost", "",
        f"- Total Input Tokens: {total_input_tokens:,}",
        f"- Total Output Tokens: {total_output_tokens:,}",
        f"- Total Cost: ${total_cost_usd:.6f}",
    ])

    mode_rows: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        mode_rows.setdefault(row.get("evaluation_mode", "answer_from_context"), []).append(row)

    active_metric_names = RAGASConfig.active_metric_names()

    lines.extend(["", "## Metrics Breakdown by Evaluation Mode", ""])
    for mode, grouped_rows in sorted(mode_rows.items()):
        parts = [f"**{mode}** ({len(grouped_rows)} cases)"]
        for name in sorted(active_metric_names):
            values = [
                row["metrics"].get(name)
                for row in grouped_rows
                if row.get("metric_applicability", {}).get(name, False) and row["metrics"].get(name) is not None
            ]
            parts.append(f"{name}={'N/A' if not values else f'{sum(values) / len(values):.3f}'}")
        lines.append(f"- {'; '.join(parts)}")

    retrieval_rows = [row.get("retrieval", {}) for row in rows if row.get("retrieval")]
    if retrieval_rows:
        recalls = [row["chunk_recall_at_k"] for row in retrieval_rows if row.get("chunk_recall_at_k") is not None]
        source_hits = sum(row.get("expected_sources_retrieved", False) for row in retrieval_rows)
        lines.extend([
            "", "## Retrieval Performance", "",
            f"- Expected sources retrieved: {source_hits}/{len(retrieval_rows)}",
            f"- Mean chunk recall@k: {'N/A' if not recalls else f'{sum(recalls) / len(recalls):.3f}'}",
        ])

    lines.extend([
        "", "## Case Results", "",
        "| Case | Mode | Category | Status | Failed Checks | Cost (USD) |",
        "| --- | --- | --- | --- | --- | ---: |"
    ])

    for row in rows:
        failed_checks = [k for k, v in row.get("checks", {}).items() if not v]
        failed_str = ", ".join(failed_checks) if failed_checks else "None"
        cost = row.get("token_usage", {}).get("total_cost_usd", 0.0)

        lines.append(
            f"| {row['case_id']} | {row.get('evaluation_mode', 'N/A')} | {row['category']} | "
            f"{row['status']} | {failed_str} | ${cost:.6f} |"
        )

    return "\n".join(lines) + "\n"
