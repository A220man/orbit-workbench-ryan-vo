"""Unit tests for the AI coding agent benchmark evaluation runner."""
from app.services.evaluator import BENCHMARK_DATASET, BenchmarkEvaluator


def test_benchmark_suite_execution():
    evaluator = BenchmarkEvaluator()
    summary = evaluator.run_suite()

    assert summary.total_cases == 20
    assert summary.passed_cases >= 18
    assert summary.accuracy_rate >= 0.90
    assert summary.containment_compliance_rate == 1.0
    assert summary.honest_data_rate == 1.0
    assert summary.avg_render_latency_ms < 50.0  # Under 50ms average render time
    assert len(summary.cases) == 20


def test_benchmark_single_case():
    evaluator = BenchmarkEvaluator()
    single_case = [BENCHMARK_DATASET[0]]  # Azure AKS case
    summary = evaluator.run_suite(single_case)

    assert summary.total_cases == 1
    assert summary.passed_cases == 1
    assert summary.cases[0].passed
    assert summary.cases[0].validation.containment_compliant
