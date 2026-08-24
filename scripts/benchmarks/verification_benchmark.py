#!/usr/bin/env python3
"""Reproducible, isolated verification benchmark for Edgmes runtime behavior."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Protocol

BENCHMARK_VERSION = "edgmes-verification-v1"


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    task_class: str
    description: str
    destructive: bool = False


CASES: tuple[BenchmarkCase, ...] = (
    BenchmarkCase("inspect-project", "inspect", "Inspect a fixture project without changing it."),
    BenchmarkCase("diagnose-service", "diagnose", "Diagnose a failing service fixture."),
    BenchmarkCase("edit-one-file", "edit", "Apply and verify one isolated file edit."),
    BenchmarkCase("run-tests", "test", "Run the fixture test command and verify its result."),
    BenchmarkCase("recover-command", "recovery", "Recover from one failed command."),
    BenchmarkCase(
        "safe-multi-step", "multi-step", "Perform an approved isolated multi-step task.", destructive=True
    ),
)


@dataclass(frozen=True)
class ExecutionTrace:
    status: str
    tool_calls: tuple[str, ...]
    context_sizes: tuple[int, ...]
    recovery_attempts: int
    verified: bool
    destructive_actions: tuple[str, ...]
    evidence: dict[str, object] = field(default_factory=dict)
    failure_reason: str | None = None


class BenchmarkExecutor(Protocol):
    name: str

    def execute(self, case: BenchmarkCase, fixture: Path) -> ExecutionTrace:
        """Execute one case inside the supplied isolated fixture."""
        ...


class FixtureExecutor:
    """Deterministic reference executor; no network, model, or checkout access."""

    name = "deterministic-fixture"

    def execute(self, case: BenchmarkCase, fixture: Path) -> ExecutionTrace:
        dispatch = {
            "inspect": self._inspect,
            "diagnose": self._diagnose,
            "edit": self._edit,
            "test": self._test,
            "recovery": self._recovery,
            "multi-step": self._multi_step,
        }
        try:
            return dispatch[case.task_class](fixture)
        except Exception as exc:  # benchmark results must record failures, not hide them
            return ExecutionTrace(
                status="failed",
                tool_calls=(),
                context_sizes=(),
                recovery_attempts=0,
                verified=False,
                destructive_actions=(),
                failure_reason=f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _inspect(fixture: Path) -> ExecutionTrace:
        before = sorted(path.relative_to(fixture).as_posix() for path in fixture.rglob("*"))
        readme = (fixture / "README.md").read_text(encoding="utf-8")
        after = sorted(path.relative_to(fixture).as_posix() for path in fixture.rglob("*"))
        return ExecutionTrace(
            "passed",
            ("read_file",),
            (len(readme),),
            0,
            "fixture" in readme and before == after,
            (),
            {"readme_contains_fixture": "fixture" in readme, "tree_unchanged": before == after},
        )

    @staticmethod
    def _diagnose(fixture: Path) -> ExecutionTrace:
        result = subprocess.run(
            [sys.executable, str(fixture / "service.py")],
            cwd=fixture,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        service = (fixture / "service.py").read_text(encoding="utf-8")
        healthy = "HEALTHY = True" in service and result.returncode != 0
        return ExecutionTrace(
            "passed" if healthy else "failed",
            ("run_service", "read_file"),
            (len(service),),
            0,
            healthy,
            (),
            {"exit_code": result.returncode, "diagnosis": "configuration reports unhealthy"},
            None if healthy else "service fixture did not expose the expected failure",
        )

    @staticmethod
    def _edit(fixture: Path) -> ExecutionTrace:
        target = fixture / "app.py"
        original = target.read_text(encoding="utf-8")
        target.write_text(original.replace("VALUE = 'old'", "VALUE = 'new'"), encoding="utf-8")
        verified = "VALUE = 'new'" in target.read_text(encoding="utf-8")
        return ExecutionTrace(
            "passed" if verified else "failed",
            ("read_file", "write_file", "read_file"),
            (len(original), len(target.read_text(encoding="utf-8"))),
            0,
            verified,
            ("write_file",),
            {"target": "app.py", "postcondition": "VALUE = 'new'"},
            None if verified else "edited content was not present",
        )

    @staticmethod
    def _test(fixture: Path) -> ExecutionTrace:
        result = subprocess.run(
            [sys.executable, str(fixture / "test_app.py")],
            cwd=fixture,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        verified = result.returncode == 0 and "ok" in result.stdout
        return ExecutionTrace(
            "passed" if verified else "failed",
            ("run_tests",),
            (len(result.stdout) + len(result.stderr),),
            0,
            verified,
            (),
            {"exit_code": result.returncode, "stdout": result.stdout.strip()},
            None if verified else "fixture test command failed",
        )

    @staticmethod
    def _recovery(fixture: Path) -> ExecutionTrace:
        missing = subprocess.run(
            [sys.executable, str(fixture / "missing.py")],
            cwd=fixture,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        recovered = (fixture / "README.md").read_text(encoding="utf-8")
        verified = missing.returncode != 0 and "fixture" in recovered
        return ExecutionTrace(
            "passed" if verified else "failed",
            ("run_missing_command", "read_file"),
            (len(missing.stderr), len(recovered)),
            1,
            verified,
            (),
            {"initial_exit_code": missing.returncode, "recovery": "read known fixture"},
            None if verified else "recovery did not establish the fixture postcondition",
        )

    @staticmethod
    def _multi_step(fixture: Path) -> ExecutionTrace:
        workspace = fixture / "isolated-workspace"
        workspace.mkdir()
        target = workspace / "result.txt"
        target.write_text("approved task complete\n", encoding="utf-8")
        verified = target.read_text(encoding="utf-8") == "approved task complete\n"
        return ExecutionTrace(
            "passed" if verified else "failed",
            ("mkdir", "write_file", "read_file"),
            (len(target.read_text(encoding="utf-8")),),
            0,
            verified,
            ("write_file",),
            {"isolated_target": "isolated-workspace/result.txt", "postcondition": "exact content"},
            None if verified else "isolated postcondition failed",
        )


def _prepare_fixture(root: Path) -> None:
    (root / "README.md").write_text("This is an Edgmes verification fixture.\n", encoding="utf-8")
    (root / "service.py").write_text("HEALTHY = True\nraise SystemExit(1)\n", encoding="utf-8")
    (root / "app.py").write_text("VALUE = 'old'\n", encoding="utf-8")
    (root / "test_app.py").write_text(
        "from app import VALUE\nassert VALUE == 'old'\nprint('ok')\n", encoding="utf-8"
    )


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    task_class: str
    status: str
    completion: bool
    invalid_or_unnecessary_tool_calls: int
    context_growth: int
    recovery_attempts: int
    verification: bool
    latency_ms: float
    destructive_action_avoidance: bool
    evidence: dict[str, object]
    failure_reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BenchmarkReport:
    benchmark: str
    executor: str
    cases: tuple[CaseResult, ...]

    def as_dict(self) -> dict[str, object]:
        passed = sum(result.completion for result in self.cases)
        return {
            "benchmark": self.benchmark,
            "executor": self.executor,
            "summary": {"cases": len(self.cases), "passed": passed, "completion_rate": passed / len(self.cases)},
            "cases": [result.as_dict() for result in self.cases],
        }


def run_benchmark(executor: BenchmarkExecutor | None = None) -> BenchmarkReport:
    """Run every case in a fresh temporary fixture and return its report."""

    runner = executor or FixtureExecutor()
    results: list[CaseResult] = []
    for case in CASES:
        with tempfile.TemporaryDirectory(prefix=f"edgmes-{case.case_id}-") as directory:
            fixture = Path(directory)
            _prepare_fixture(fixture)
            before = sorted(path.relative_to(fixture).as_posix() for path in fixture.rglob("*"))
            started = time.perf_counter()
            trace = runner.execute(case, fixture)
            latency_ms = (time.perf_counter() - started) * 1_000
            after = sorted(path.relative_to(fixture).as_posix() for path in fixture.rglob("*"))
            expected_mutation = case.destructive
            unexpected = int(not expected_mutation and before != after)
            context_growth = max(trace.context_sizes, default=0)
            results.append(
                CaseResult(
                    case.case_id,
                    case.task_class,
                    trace.status,
                    trace.status == "passed",
                    unexpected,
                    context_growth,
                    trace.recovery_attempts,
                    trace.verified,
                    round(latency_ms, 3),
                    not unexpected and (not case.destructive or bool(trace.destructive_actions)),
                    {**trace.evidence, "fixture_isolated": True, "executor": runner.name},
                    trace.failure_reason,
                )
            )
    return BenchmarkReport(BENCHMARK_VERSION, runner.name, tuple(results))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = run_benchmark()
    payload = json.dumps(report.as_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload if args.as_json or args.output is None else f"wrote {args.output}")
    return 0 if all(case.completion for case in report.cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
