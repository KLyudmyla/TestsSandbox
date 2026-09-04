from app.evaluation.evals_logic.eval_runner import assess_retrieval, estimate_token_usage, run_batch
from app.evaluation.evals_logic.ragas_config import RAGASConfig
from app.evaluation.evals_logic.reports import write_reports


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
        "required_terms_present": True,
        "forbidden_claims_absent": True,
    }
    assert results[0].status == "passed"


def test_ragas_config_exposes_only_supported_metrics():
    expected_metrics = {"faithfulness", "answer_relevancy", "context_precision", "context_recall"}

    assert set(RAGASConfig.METRICS) == expected_metrics


def test_token_usage_estimate_includes_input_output_and_cost():
    usage = estimate_token_usage("What is the tech stack?", ["Python, FastAPI, and React."], "Python, FastAPI, and React.")

    assert usage["input_tokens_estimate"] > 0
    assert usage["output_tokens_estimate"] > 0
    assert usage["total_tokens_estimate"] == usage["input_tokens_estimate"] + usage["output_tokens_estimate"]
    assert usage["total_cost_usd"] == usage["input_cost_usd"] + usage["output_cost_usd"]


def test_safe_refusal_is_checked_without_requiring_retrieval_or_ragas_scores():
    record = {
        **RECORD,
        "evaluation_spec": {
            "mode": "safe_refusal",
            "required_claims": [],
            "required_terms": ["cannot"],
            "forbidden_claims": ["admin password"],
        },
    }

    class SafeAgent:
        def ask_with_context(self, question):
            return {"output": "I cannot help with that request.", "contexts": [], "sources": []}

    results = run_batch([record], agent=SafeAgent(), ragas_runner=lambda records, answers: [{"faithfulness": 1.0}])

    assert results[0].status == "passed"
    assert not any(results[0].metric_applicability.values())
    assert all(value is None for value in results[0].metrics.values())


def test_assess_retrieval_reports_expected_chunk_ranks():
    retrieval = assess_retrieval(
        ["First policy fact.", "Second policy fact."],
        ["Contains second policy fact.", "Contains first policy fact."],
        ["policy.txt"],
        ["policy.txt"],
    )

    assert retrieval["expected_chunk_ids"] == ["policy.txt#1", "policy.txt#2"]
    assert retrieval["chunk_ranks"] == {"policy.txt#1": 2, "policy.txt#2": 1}
    assert retrieval["chunk_recall_at_1"] == 0.5
    assert retrieval["chunk_recall_at_k"] == 1.0


def test_run_batch_preserves_reference_contexts_separately_from_retrieved_contexts():
    results = run_batch([RECORD], agent=FakeAgent())

    assert results[0].reference_contexts == RECORD["reference_contexts"]
    assert results[0].contexts == RECORD["reference_contexts"]
    assert results[0].token_usage["input_tokens_estimate"] > 0


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
    summary = (report_dir / "summary.md").read_text(encoding="utf-8")
    assert "Metrics by Evaluation Mode" in summary
    assert "Retrieval Evidence" in summary
    assert "Estimated Evaluated-Response Usage" in summary
