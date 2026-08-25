from app.tests.evals.eval_runner import run_batch
from app.tests.evals.ragas_config import RAGASConfig, RAGASMetricsDescriptions
from app.tests.evals.reports import write_reports


RECORD = {
    "id": "case-001",
    "question": "What is the tech stack?",
    "reference_contexts": ["Python, FastAPI, and React."],
    "answer": "",
    "ground_truth": "Python, FastAPI, and React.",
    "metadata": {
        "source_docs": ["engineering_stack.txt"],
        "category": "Engineering",
        "difficulty": "easy",
    },
}


class FakeAgent:
    def ask_with_context(self, question):
        assert question == RECORD["question"]
        return {
            "output": "Python, FastAPI, and React.",
            "contexts": RECORD["reference_contexts"],
            "sources": ["engineering_stack.txt"],
        }


def test_run_batch_captures_agent_result_and_checks():
    results = run_batch([RECORD], agent=FakeAgent())

    assert results[0].answer == "Python, FastAPI, and React."
    assert results[0].checks == {
        "expected_sources_retrieved": True,
        "answer_present": True,
        "expected_behavior": True,
    }
    assert results[0].status == "passed"


def test_ragas_config_exposes_only_supported_metrics():
    expected_metrics = {"faithfulness", "answer_relevancy", "context_precision", "context_recall"}

    assert set(RAGASConfig.METRICS) == expected_metrics
    assert set(RAGASMetricsDescriptions.DESCRIPTIONS) == expected_metrics


def test_run_batch_accepts_mocked_ragas_runner():
    results = run_batch(
        [RECORD],
        agent=FakeAgent(),
        ragas_runner=lambda records, answers: [{"faithfulness": 1.0}],
    )

    assert results[0].metrics == {"faithfulness": 1.0}


def test_run_batch_preserves_reference_contexts_separately_from_retrieved_contexts():
    results = run_batch([RECORD], agent=FakeAgent())

    assert results[0].reference_contexts == RECORD["reference_contexts"]
    assert results[0].contexts == RECORD["reference_contexts"]


def test_run_batch_keeps_deterministic_status_when_ragas_fails():
    def failing_ragas_runner(records, answers):
        raise RuntimeError("judge unavailable")

    results = run_batch([RECORD], agent=FakeAgent(), ragas_runner=failing_ragas_runner)

    assert results[0].status == "passed"
    assert "RAGAS evaluation failed" in results[0].error


def test_write_reports_creates_json_csv_and_markdown(tmp_path):
    results = run_batch([RECORD], agent=FakeAgent())
    report_dir = write_reports(results, tmp_path, {"metrics": [], "skip_ragas": True})

    assert (report_dir / "results.json").exists()
    assert (report_dir / "results.csv").exists()
    assert (report_dir / "summary.md").exists()
