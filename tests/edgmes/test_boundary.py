from __future__ import annotations

import ast
from pathlib import Path


EDGMES_ROOT = Path(__file__).parents[2] / "edgmes"
FORBIDDEN_TOP_LEVEL_IMPORTS = {"agent", "tools", "gateway", "plugins", "hermes_cli"}


def test_edgmes_core_does_not_import_hermes_runtime_modules() -> None:
    for path in EDGMES_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".", 1)[0]]
            else:
                continue
            assert not FORBIDDEN_TOP_LEVEL_IMPORTS.intersection(names), path
