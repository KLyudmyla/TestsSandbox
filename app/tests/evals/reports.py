"""Report writers for evaluation results."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.tests.evals.eval_runner import EvaluationCaseResult, results_as_dict


def write_reports(results: list[EvaluationCaseResult], output_dir: Path, config: dict[str, Any]) -> Path:
    """Write JSON, CSV, and Markdown reports into a timestamped run directory."""
    run_dir = output_dir / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = results_as_dict(results)
    (run_dir / "results.json").write_text(json.dumps({"config": config, "results": rows}, indent=2), encoding="utf-8")
    _write_csv(rows, run_dir / "results.csv")
    (run_dir / "summary.md").write_text(_summary_markdown(rows, config), encoding="utf-8")
    return run_dir


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "case_id", "category", "difficulty", "question", "answer", "ground_truth",
        "reference_contexts", "sources", "contexts", "metrics", "checks", "status", "error",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: json.dumps(row[name]) if isinstance(row[name], (list, dict)) else row[name] for name in fieldnames})


def _summary_markdown(rows: list[dict[str, Any]], config: dict[str, Any]) -> str:
    passed = sum(row["status"] == "passed" for row in rows)
    failed = sum(row["status"] == "failed" for row in rows)
    errors = sum(row["status"] == "error" for row in rows)
    metric_values: dict[str, list[float]] = {}
    for row in rows:
        for name, value in row["metrics"].items():
            if value is not None:
                metric_values.setdefault(name, []).append(value)

    lines = [
        "# Evaluation Summary",
        "",
        f"- Cases: {len(rows)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Errors: {errors}",
        f"- Metrics: {', '.join(config.get('metrics', [])) or 'none'}",
        "",
        "## Average Metrics",
        "",
    ]
    if metric_values:
        lines.extend(f"- {name}: {sum(values) / len(values):.3f}" for name, values in sorted(metric_values.items()))
    else:
        lines.append("No metric scores were produced.")
    lines.extend(["", "## Case Results", "", "| Case | Category | Status |", "| --- | --- | --- |"])
    lines.extend(f"| {row['case_id']} | {row['category']} | {row['status']} |" for row in rows)
    return "\n".join(lines) + "\n"
