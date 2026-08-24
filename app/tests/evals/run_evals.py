"""Command-line entry point for local RAG evaluation runs."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from app.tests.evals.eval_runner import run_batch, run_ragas
from app.tests.evals.golden_dataset import MY_DATASET
from app.tests.evals.ragas_config import RAGASConfig
from app.tests.evals.reports import write_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local RAG evaluation dataset.")
    parser.add_argument("--skip-ragas", action="store_true", help="Run deterministic checks without live RAGAS scoring.")
    parser.add_argument("--limit", type=int, help="Evaluate only the first N records.")
    parser.add_argument("--category", help="Evaluate only one dataset category.")
    project_root = Path(__file__).resolve().parents[3]
    default_output_dir = project_root / RAGASConfig.OUTPUT_DIR
    parser.add_argument("--output-dir", type=Path, default=default_output_dir)
    return parser


def load_agent():
    from app.agent import DocumentSearchAgent

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for live agent evaluation.")
    agent = DocumentSearchAgent(openai_api_key=api_key, model_name=RAGASConfig.LLM_MODEL)
    knowledge_base_dir = Path(__file__).resolve().parents[2] / "knowledge_base"
    for file_path in knowledge_base_dir.glob("*.txt"):
        agent.upload_document(file_path.read_text(encoding="utf-8"), file_path.name)
    return agent


def main() -> int:
    args = build_parser().parse_args()
    records = MY_DATASET
    if args.category:
        records = [record for record in records if record.get("metadata", {}).get("category") == args.category]
    if args.limit is not None:
        records = records[:args.limit]

    agent = load_agent()
    ragas_runner = None if args.skip_ragas else lambda prepared, answers: run_ragas(prepared, answers)
    results = run_batch(records, agent=agent, ragas_runner=ragas_runner)
    report_dir = write_reports(
        results,
        args.output_dir,
        {"metrics": list(RAGASConfig.METRICS), "skip_ragas": args.skip_ragas, "record_count": len(records)},
    )
    print(f"Evaluation reports written to {report_dir}")
    return 0 if all(result.status == "passed" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
