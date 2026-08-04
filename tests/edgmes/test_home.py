from pathlib import Path

import pytest

from edgmes.home import EdgmesHome, HomeConfigurationError


def test_default_home_is_independent_from_hermes(tmp_path: Path) -> None:
    home = EdgmesHome.resolve(environ={}, user_home=tmp_path)
    assert home.root == tmp_path / ".edgmes"
    assert home.root != tmp_path / ".hermes"
    assert not home.root.exists()


def test_absolute_override_is_honored(tmp_path: Path) -> None:
    target = tmp_path / "isolated-edgmes"
    home = EdgmesHome.resolve(environ={"EDGMES_HOME": str(target)})
    assert home.root == target


def test_relative_override_is_rejected() -> None:
    with pytest.raises(HomeConfigurationError, match="absolute"):
        EdgmesHome.resolve(environ={"EDGMES_HOME": "relative"})


def test_initialize_creates_only_edgmes_directories(tmp_path: Path) -> None:
    home = EdgmesHome.resolve(environ={}, user_home=tmp_path)
    home.initialize()
    assert all(path.is_dir() for path in home.directories)
    assert not (tmp_path / ".hermes").exists()
