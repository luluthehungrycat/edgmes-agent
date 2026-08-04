from pathlib import Path

from scripts.benchmarks.baseline_harness import run_benchmark


def test_baseline_report_has_all_preparation_phases() -> None:
    report = run_benchmark(repo_root=Path(__file__).parents[2], iterations=1)
    data = report.as_dict()
    assert data["benchmark"] == "edgmes-inherited-hermes-baseline-v1"
    assert set(data["phases"]) == {
        "startup_import",
        "prompt_assembly",
        "tool_discovery_construction",
        "representative_read_only_task",
    }
    for phase in data["phases"].values():
        assert phase["median_ms"] >= 0
        assert len(phase["samples_ms"]) == 1
