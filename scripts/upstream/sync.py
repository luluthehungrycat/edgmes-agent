#!/usr/bin/env python3
"""Plan or create a reviewable merge of upstream/main into Edgmes main."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import datetime as dt
import json
from pathlib import Path
import subprocess
import tomllib
from typing import Sequence

PROTECTED_PREFIXES = (
    "agent/",
    "tools/",
    "gateway/",
    "plugins/",
    "providers/",
    "run_agent.py",
    "model_tools.py",
    "toolsets.py",
    "pyproject.toml",
    "uv.lock",
    "prompt",
    "context",
    "hermes_state",
    "memory",
    "session",
)
DEFAULT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class SyncPlan:
    base: str
    target: str
    merge_base: str
    commit_count: int
    changed_paths: tuple[str, ...]
    protected_paths: tuple[str, ...]
    risk: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def protected_prefixes(root: Path = DEFAULT_ROOT) -> tuple[str, ...]:
    """Return static plus every packaged upstream namespace from the manifest."""
    prefixes = set(PROTECTED_PREFIXES)
    manifest = root / "pyproject.toml"
    if manifest.is_file():
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
        setuptools = data.get("tool", {}).get("setuptools", {})
        for module in setuptools.get("py-modules", []):
            if module:
                prefixes.add(module)
        for pattern in setuptools.get("packages", {}).get("find", {}).get("include", []):
            if pattern:
                prefixes.add(pattern.split(".", 1)[0] + "/")
    return tuple(sorted(prefixes))


def classify_paths(paths: Sequence[str], root: Path = DEFAULT_ROOT) -> tuple[tuple[str, ...], str]:
    prefixes = protected_prefixes(root)
    protected = tuple(
        path for path in paths if any(path == prefix or path.startswith(prefix) for prefix in prefixes)
    )
    return protected, "high" if protected else "normal"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


def plan(root: Path, base: str = "origin/main", target: str = "upstream/main") -> SyncPlan:
    merge_base = git(root, "merge-base", base, target)
    commit_count = int(git(root, "rev-list", "--count", f"{merge_base}..{target}") or "0")
    raw = git(root, "diff", "--name-only", "--diff-filter=ACDMRTUXB", merge_base, target)
    changed = tuple(path for path in raw.splitlines() if path)
    protected, risk = classify_paths(changed, root)
    return SyncPlan(base, target, merge_base, commit_count, changed, protected, risk)


def create_branch(root: Path, target: str, branch: str, base: str = "origin/main") -> None:
    status = git(root, "status", "--porcelain")
    if status:
        raise RuntimeError("working tree must be clean before creating an upstream sync branch")
    git(root, "switch", "-c", branch, base)
    git(root, "merge", "--no-ff", target, "-m", f"chore(sync): merge {target} into Edgmes")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--target", default="upstream/main")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--create-branch", action="store_true")
    parser.add_argument("--branch", default=f"sync/upstream-{dt.date.today().isoformat()}")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    result = plan(root, args.base, args.target)
    if args.create_branch:
        if result.commit_count == 0:
            raise SystemExit("upstream is already synchronized")
        create_branch(root, args.target, args.branch, args.base)
    if args.as_json:
        print(json.dumps(result.as_dict(), sort_keys=True))
    else:
        print(f"upstream commits: {result.commit_count}")
        print(f"changed paths: {len(result.changed_paths)}")
        print(f"risk: {result.risk}")
        if result.protected_paths:
            print("protected paths:")
            for path in result.protected_paths:
                print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
