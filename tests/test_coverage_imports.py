import sys
import importlib
import typing
from unittest.mock import patch


def test_imports_fallback_no_numba() -> None:
    # Remove from sys.modules to force reload
    if "img2ascii.core.sampling" in sys.modules:
        del sys.modules["img2ascii.core.sampling"]

    orig_import = __import__

    def mock_import(name: str, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        if name == "numba" or name.startswith("numba."):
            raise ImportError("Mocked import error")
        return orig_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        import img2ascii.core.sampling as sampling

        assert not sampling.HAS_NUMBA

    # Restore module
    if "img2ascii.core.sampling" in sys.modules:
        del sys.modules["img2ascii.core.sampling"]
    importlib.import_module("img2ascii.core.sampling")


def test_imports_fallback_no_scipy() -> None:
    if "img2ascii.renderers.ascii_art" in sys.modules:
        del sys.modules["img2ascii.renderers.ascii_art"]

    orig_import = __import__

    def mock_import(name: str, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        if name == "scipy" or name.startswith("scipy."):
            raise ImportError("Mocked import error")
        return orig_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        import img2ascii.renderers.ascii_art as ascii_art

        assert not ascii_art.HAS_SCIPY

    # Restore module
    if "img2ascii.renderers.ascii_art" in sys.modules:
        del sys.modules["img2ascii.renderers.ascii_art"]
    importlib.import_module("img2ascii.renderers.ascii_art")
