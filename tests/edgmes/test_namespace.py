from edgmes import __version__


def test_edgmes_namespace_is_importable() -> None:
    assert __version__ == "0.1.0.dev0"
