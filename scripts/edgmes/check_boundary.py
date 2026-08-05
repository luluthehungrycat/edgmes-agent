#!/usr/bin/env python3
"""Validate the installable Edgmes namespace boundary."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import sys
import tomllib

FORBIDDEN_ROOT_MODULES = frozenset(
    {
        "agent",
        "tools",
        "gateway",
        "plugins",
        "providers",
        "hermes_cli",
        "run_agent",
        "model_tools",
        "toolsets",
        "batch_runner",
        "trajectory_compressor",
        "toolset_distributions",
        "cli",
        "hermes_bootstrap",
        "hermes_constants",
        "hermes_state",
        "hermes_state_common",
        "hermes_state_portability",
        "hermes_state_schema",
        "hermes_state_search",
        "hermes_time",
        "hermes_logging",
        "utils",
        "mcp_serve",
    }
)
FORBIDDEN_HOME_MARKERS = (".hermes", "HERMES_HOME")


def check(root: Path) -> list[str]:
    errors: list[str] = []
    package = root / "edgmes"
    manifest = root / "pyproject.toml"
    if not package.is_dir():
        return [f"missing package directory: {package}"]
    if not manifest.is_file():
        return [f"missing package manifest: {manifest}"]
    manifest_text = manifest.read_text(encoding="utf-8")
    manifest_data = tomllib.loads(manifest_text)
    package_find = manifest_data.get("tool", {}).get("setuptools", {}).get("packages", {}).get("find", {})
    included_packages = package_find.get("include", [])
    forbidden_top_level = set(FORBIDDEN_ROOT_MODULES)
    forbidden_top_level.update(
        pattern.split(".", 1)[0]
        for pattern in included_packages
        if pattern and pattern.split(".", 1)[0] != "edgmes"
    )
    if '"edgmes"' not in manifest_text or '"edgmes.*"' not in manifest_text:
        errors.append("pyproject.toml does not include edgmes package discovery")
    if "edgmes = \"edgmes.runtime:_main\"" not in manifest_text:
        errors.append("pyproject.toml does not expose the edgmes console entry point")
    for path in sorted(package.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_HOME_MARKERS:
            if marker in source:
                errors.append(f"{path.relative_to(root)} references forbidden Hermes home marker {marker}")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            errors.append(f"{path.relative_to(root)} has syntax error: {exc}")
            continue
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    top = module.split(".", 1)[0]
                    if top in forbidden_top_level:
                        errors.append(f"{path.relative_to(root)} imports forbidden upstream namespace {module}")
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                module = node.module
                top = module.split(".", 1)[0]
                if top in forbidden_top_level:
                    errors.append(f"{path.relative_to(root)} imports forbidden upstream namespace {module}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    errors = check(args.root.resolve())
    if errors:
        print("Edgmes package boundary FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Edgmes package boundary OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
