from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SPEC = spec_from_file_location("upstream_sync", ROOT / "scripts/upstream/sync.py")
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_classify_paths_marks_inherited_runtime_as_high_risk() -> None:
    protected, risk = MODULE.classify_paths(
        [
            "agent/conversation_loop.py",
            "model_tools.py",
            "toolsets.py",
            "hermes_cli/auth.py",
            "acp_adapter/permissions.py",
            "docs/README.md",
            "new-file.py",
        ]
    )

    assert protected == (
        "agent/conversation_loop.py",
        "model_tools.py",
        "toolsets.py",
        "hermes_cli/auth.py",
        "acp_adapter/permissions.py",
    )
    assert risk == "high"


def test_classify_paths_keeps_docs_only_delta_normal() -> None:
    protected, risk = MODULE.classify_paths(["docs/example.md", "website/page.md"])

    assert protected == ()
    assert risk == "normal"


def test_create_branch_starts_from_configured_base(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(root: Path, *args: str) -> str:
        calls.append(args)
        return ""

    monkeypatch.setattr(MODULE, "git", fake_git)

    MODULE.create_branch(tmp_path, "upstream/main", "sync/example", "origin/main")

    assert calls == [
        ("status", "--porcelain"),
        ("switch", "-c", "sync/example", "origin/main"),
        ("merge", "--no-ff", "upstream/main", "-m", "chore(sync): merge upstream/main into Edgmes"),
    ]


def test_manifest_and_lockfile_changes_are_protected() -> None:
    protected, risk = MODULE.classify_paths(["pyproject.toml", "setup.py", "uv.lock"])

    assert protected == ("pyproject.toml", "setup.py", "uv.lock")
    assert risk == "high"


def test_classify_paths_uses_selected_manifest_root(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.setuptools.packages.find]\ninclude = ["edgmes", "edgmes.*", "new_runtime", "new_runtime.*"]\n',
        encoding="utf-8",
    )

    protected, risk = MODULE.classify_paths(["new_runtime/auth.py"], tmp_path)

    assert protected == ("new_runtime/auth.py",)
    assert risk == "high"
