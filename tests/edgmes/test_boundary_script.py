from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = spec_from_file_location("check_boundary", ROOT / "scripts/edgmes/check_boundary.py")
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_edgmes_boundary_passes_current_tree() -> None:
    assert MODULE.check(ROOT) == []


def test_boundary_rejects_forbidden_import_and_home_marker(tmp_path: Path) -> None:
    (tmp_path / "edgmes").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project.scripts]\nedgmes = "edgmes.runtime:_main"\n'
        '[tool.setuptools.packages.find]\ninclude = ["edgmes", "edgmes.*"]\n',
        encoding="utf-8",
    )
    (tmp_path / "edgmes" / "bad.py").write_text(
        "import tools\nHOME = '~/.hermes'\n", encoding="utf-8"
    )

    errors = MODULE.check(tmp_path)

    assert any("forbidden upstream namespace tools" in error for error in errors)
    assert any("forbidden Hermes home marker" in error for error in errors)


def test_boundary_rejects_root_hermes_runtime_imports(tmp_path: Path) -> None:
    (tmp_path / "edgmes").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project.scripts]\nedgmes = "edgmes.runtime:_main"\n'
        '[tool.setuptools.packages.find]\ninclude = ["edgmes", "edgmes.*"]\n',
        encoding="utf-8",
    )
    (tmp_path / "edgmes" / "bad.py").write_text(
        "from hermes_constants import get_hermes_home\n"
        "import hermes_state\n"
        "import hermes_logging\n",
        encoding="utf-8",
    )

    errors = MODULE.check(tmp_path)

    assert any("forbidden upstream namespace hermes_constants" in error for error in errors)
    assert any("forbidden upstream namespace hermes_state" in error for error in errors)
    assert any("forbidden upstream namespace hermes_logging" in error for error in errors)


def test_boundary_derives_packaged_upstream_namespaces(tmp_path: Path) -> None:
    (tmp_path / "edgmes").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project.scripts]\nedgmes = "edgmes.runtime:_main"\n'
        '[tool.setuptools.packages.find]\n'
        'include = ["edgmes", "edgmes.*", "tui_gateway", "cron.*", "acp_adapter.*"]\n',
        encoding="utf-8",
    )
    (tmp_path / "edgmes" / "bad.py").write_text(
        "import tui_gateway\n"
        "from cron.scheduler import scheduler\n"
        "from acp_adapter.entry import connect\n",
        encoding="utf-8",
    )

    errors = MODULE.check(tmp_path)

    assert any("forbidden upstream namespace tui_gateway" in error for error in errors)
    assert any("forbidden upstream namespace cron.scheduler" in error for error in errors)
    assert any("forbidden upstream namespace acp_adapter.entry" in error for error in errors)
