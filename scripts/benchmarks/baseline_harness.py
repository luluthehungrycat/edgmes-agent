#!/usr/bin/env python3
"""Measure inherited Hermes preparation costs for the Edgmes baseline.

This deliberately does not call a provider or mutate the repository. It measures
runtime preparation separately from model inference so future Edgmes changes can
be compared against a stable, reproducible baseline.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any


@dataclass(frozen=True)
class Sample:
    name: str
    elapsed_ms: float
    details: dict[str, Any]


@dataclass(frozen=True)
class BenchmarkReport:
    benchmark: str
    repository: str
    python: str
    iterations: int
    samples: tuple[Sample, ...]

    def as_dict(self) -> dict[str, Any]:
        grouped: dict[str, list[Sample]] = {}
        for sample in self.samples:
            grouped.setdefault(sample.name, []).append(sample)

        phases: dict[str, Any] = {}
        for name, phase_samples in grouped.items():
            values = [sample.elapsed_ms for sample in phase_samples]
            phases[name] = {
                "samples_ms": [round(value, 3) for value in values],
                "median_ms": round(statistics.median(values), 3),
                "min_ms": round(min(values), 3),
                "max_ms": round(max(values), 3),
                "details": phase_samples[-1].details,
            }
        return {
            "benchmark": self.benchmark,
            "repository": self.repository,
            "python": self.python,
            "iterations": self.iterations,
            "phases": phases,
        }


def _run_subprocess_probe(
    name: str, source: str, *, repo_root: Path, iterations: int, env: dict[str, str]
) -> list[Sample]:
    samples: list[Sample] = []
    for _ in range(iterations):
        started = time.perf_counter()
        completed = subprocess.run(
            [sys.executable, "-c", source],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        if completed.returncode != 0:
            raise RuntimeError(
                f"{name} probe failed with exit {completed.returncode}: "
                f"{completed.stderr[-2000:]}"
            )
        try:
            details = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"{name} probe returned invalid JSON: {completed.stdout[-2000:]}"
            ) from exc
        samples.append(Sample(name, elapsed_ms, details))
    return samples


def run_benchmark(*, repo_root: Path, iterations: int = 3) -> BenchmarkReport:
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    repo_root = repo_root.resolve()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")
    with tempfile.TemporaryDirectory(prefix="edgmes-baseline-") as temp_home:
        env["HERMES_HOME"] = temp_home

        samples: list[Sample] = []
        samples.extend(
            _run_subprocess_probe(
                "startup_import",
                """
import json
import time
started = time.perf_counter()
import run_agent
elapsed = (time.perf_counter() - started) * 1000
print(json.dumps({"module": "run_agent", "import_ms": round(elapsed, 3)}))
""",
                repo_root=repo_root,
                iterations=iterations,
                env=env,
            )
        )
        samples.extend(
            _run_subprocess_probe(
                "prompt_assembly",
                """
import json
import time
from pathlib import Path
from agent import prompt_builder
started = time.perf_counter()
skills = prompt_builder.build_skills_system_prompt()
context = prompt_builder.build_context_files_prompt(Path.cwd())
elapsed = (time.perf_counter() - started) * 1000
print(json.dumps({
    "skills_chars": len(skills),
    "context_chars": len(context),
    "prompt_chars": len(skills) + len(context),
    "assembly_ms": round(elapsed, 3),
}))
""",
                repo_root=repo_root,
                iterations=iterations,
                env=env,
            )
        )
        samples.extend(
            _run_subprocess_probe(
                "tool_discovery_construction",
                """
import json
import time
from tools.registry import discover_builtin_tools, registry
started = time.perf_counter()
modules = discover_builtin_tools()
entries = registry.get_all_tool_names()
elapsed = (time.perf_counter() - started) * 1000
print(json.dumps({
    "imported_modules": len(modules),
    "registered_tools": len(entries),
    "construction_ms": round(elapsed, 3),
}))
""",
                repo_root=repo_root,
                iterations=iterations,
                env=env,
            )
        )

        # Representative task: read and summarize a bounded repository file.
        # This is intentionally provider-free; it measures a small useful task
        # without making network calls or modifying the checkout.
        samples.extend(
            _run_subprocess_probe(
                "representative_read_only_task",
                """
import json
from pathlib import Path
started = __import__('time').perf_counter()
path = Path('README_EDGMES.md')
text = path.read_text(encoding='utf-8')
result = {
    "path": str(path),
    "bytes": len(text.encode('utf-8')),
    "lines": len(text.splitlines()),
    "has_architecture_link": 'architecture' in text.lower(),
}
elapsed = (__import__('time').perf_counter() - started) * 1000
result['task_ms'] = round(elapsed, 3)
print(json.dumps(result))
""",
                repo_root=repo_root,
                iterations=iterations,
                env=env,
            )
        )

    return BenchmarkReport(
        benchmark="edgmes-inherited-hermes-baseline-v1",
        repository=str(repo_root),
        python=sys.version.split()[0],
        iterations=iterations,
        samples=tuple(samples),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iterations", type=int, default=3, help="cold subprocesses per phase"
    )
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--pretty", action="store_true", help="indent JSON output")
    args = parser.parse_args(argv)
    report = run_benchmark(repo_root=args.repo_root, iterations=args.iterations)
    print(json.dumps(report.as_dict(), indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
