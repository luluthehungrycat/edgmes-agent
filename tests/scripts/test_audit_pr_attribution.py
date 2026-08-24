from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SPEC = spec_from_file_location("audit_pr_attribution", ROOT / "scripts" / "audit_pr_attribution.py")
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_sync_branch_excludes_imported_upstream_parent(monkeypatch):
    calls = []

    def fake_run(*args, check=True):
        calls.append(args)
        if args == ("git", "merge-base", "origin/main", "HEAD"):
            return "base"
        if args == ("git", "branch", "--show-current"):
            return "feat/upstream-sync-conflict-resolution"
        if args[:4] == ("git", "log", "base..HEAD", "--merges"):
            return "sync-merge"
        if args == ("git", "rev-parse", "sync-merge^2"):
            return "upstream-parent"
        if args[:3] == ("git", "log", "base..HEAD") and "--not" in args:
            return "downstream@example.com\n"
        raise AssertionError(args)

    monkeypatch.setattr(MODULE, "run", fake_run)

    assert MODULE.new_emails() == ["downstream@example.com"]
    assert ("git", "log", "base..HEAD", "--not", "upstream-parent", "--format=%ae", "--no-merges") in calls


def test_ordinary_branch_keeps_existing_attribution_scope(monkeypatch):
    calls = []

    def fake_run(*args, check=True):
        calls.append(args)
        if args == ("git", "merge-base", "origin/main", "HEAD"):
            return "base"
        if args == ("git", "branch", "--show-current"):
            return "feature/ordinary"
        if args[:3] == ("git", "log", "base..HEAD"):
            return "ordinary@example.com\n"
        raise AssertionError(args)

    monkeypatch.setattr(MODULE, "run", fake_run)

    assert MODULE.new_emails() == ["ordinary@example.com"]
    assert all("--not" not in call for call in calls)
