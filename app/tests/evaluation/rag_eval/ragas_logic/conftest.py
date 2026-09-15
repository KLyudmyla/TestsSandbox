import json
from pathlib import Path
import pytest

from app.tests.evaluation.rag_eval.ragas_logic.eval_runner import run_ragas, EvaluationCaseResult
from app.tests.evaluation.rag_eval.ragas_logic.ragas_config import RAGASConfig
from app.tests.evaluation.rag_eval.ragas_logic.reports import write_reports
from app.tests.evaluation.rag_eval.ragas_logic.run_evals import load_agent


@pytest.fixture(scope="session")
def agent_fixture():
    """Initializes the agent and uploads documents once per test session."""
    return load_agent()


@pytest.fixture(scope="session")
def ragas_runner_fixture(request):
    """Provides the live RAGAS runner unless --skip-ragas is passed."""
    if request.config.getoption("--skip-ragas", default=False):
        return None
    return lambda prepared, answers: run_ragas(prepared, answers)


def pytest_addoption(parser):
    """Adds CLI options to pytest for controlling RAGAS scoring and report output."""
    parser.addoption(
        "--skip-ragas", action="store_true", help="Skip live RAGAS metric scoring."
    )
    parser.addoption(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[3] / RAGASConfig.OUTPUT_DIR,
        help="Directory to save evaluation reports.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Ensures results storage directory exists prior to test execution."""
    results_dir = config.rootpath / ".pytest_cache" / "eval_results"
    results_dir.mkdir(parents=True, exist_ok=True)


def record_case_result(pytestconfig, result: EvaluationCaseResult):

    """Atomically record individual evaluation result to an isolated per-case file."""
    results_dir = pytestconfig.rootpath / ".pytest_cache" / "eval_results"
    case_file = results_dir / f"{result.case_id}.json"

    # Write case result to dedicated file to prevent write locks during xdist runs
    case_file.write_text(json.dumps(result.__dict__, default=str, indent=2), encoding="utf-8")


def pytest_sessionfinish(session, exitstatus):
    """Aggregates per-case JSON files across all workers and generates reports."""
    # Run only on the main process (skip worker nodes in pytest-xdist)
    if hasattr(session.config, "workerinput"):
        return

    results_dir = session.config.rootpath / ".pytest_cache" / "eval_results"

    if results_dir.exists():
        raw_results = []
        for file_path in results_dir.glob("*.json"):
            try:
                raw_results.append(json.loads(file_path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue

        if raw_results:
            results = [EvaluationCaseResult(**item) for item in raw_results]
            output_dir = session.config.getoption("--output-dir")
            skip_ragas = session.config.getoption("--skip-ragas", default=False)

            report_dir = write_reports(
                results,
                output_dir,
                {
                    "metrics": list(RAGASConfig.METRICS),
                    "skip_ragas": skip_ragas,
                    "record_count": len(results),
                },
            )
            print(f"\nEvaluation reports written to {report_dir}")
