import pytest
from app.tests.evaluation.rag_eval.ragas_logic.eval_runner import run_batch
from app.tests.evaluation.datasets.golden_dataset import MY_DATASET
from app.tests.evaluation.rag_eval.ragas_logic.conftest import record_case_result


class TestCasesForRagasDataset:

    @pytest.mark.parametrize(
        "case",
        MY_DATASET,
        ids=[record["id_name"] for record in MY_DATASET],
    )
    def test_eval_case(self, case, agent_fixture, ragas_runner_fixture, pytestconfig):
        """Evaluates individual datasets cases using RAGAS and deterministic checks."""
        results = run_batch([case], agent=agent_fixture, ragas_runner=ragas_runner_fixture)
        result = results[0]

        # Atomically record case result for final report aggregation
        record_case_result(pytestconfig, result)

        # Assert pass condition
        assert result.status == "passed", (
            f"Evaluation failed for {result.case_id}\n"
            f"Error: {result.error}\n"
            f"Checks: {result.checks}\n"
            f"Metrics: {result.metrics}"
        )
