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
        ["agent/conversation_loop.py", "docs/README.md", "new-file.py"]
    )

    assert protected == ("agent/conversation_loop.py",)
    assert risk == "high"


def test_classify_paths_keeps_docs_only_delta_normal() -> None:
    protected, risk = MODULE.classify_paths(["docs/example.md", "website/page.md"])

    assert protected == ()
    assert risk == "normal"
