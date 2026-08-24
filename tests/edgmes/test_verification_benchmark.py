import json

from scripts.benchmarks.verification_benchmark import BENCHMARK_VERSION, run_benchmark


def test_verification_benchmark_runs_all_cases_in_isolation() -> None:
    report = run_benchmark()
    data = report.as_dict()

    assert data["benchmark"] == BENCHMARK_VERSION
    assert data["summary"] == {"cases": 6, "passed": 6, "completion_rate": 1.0}
    cases = data["cases"]
    assert isinstance(cases, list)
    assert all(isinstance(case, dict) for case in cases)
    assert all(case["evidence"]["fixture_isolated"] for case in cases)
    assert all(case["verification"] for case in cases)


def test_benchmark_report_is_json_serializable() -> None:
    report = run_benchmark()

    encoded = json.dumps(report.as_dict(), sort_keys=True)

    assert "safe-multi-step" in encoded
    assert "destructive_action_avoidance" in encoded