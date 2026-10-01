"""Checks the packaging contract that a single interpreter's test run cannot cover."""

import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]

import img2ascii

PACKAGE_ROOT = Path(img2ascii.__file__).parent
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = sorted(PACKAGE_ROOT.rglob("*.py"))


def _pyproject():
    with open(PROJECT_ROOT / "pyproject.toml", "rb") as handle:
        return tomllib.load(handle)


def test_py_typed_marker_is_shipped():
    # Without it, PEP 561 forbids consumers from using these annotations.
    assert (PACKAGE_ROOT / "py.typed").is_file()


def test_pep604_annotations_have_the_future_import():
    """`X | None` is a runtime TypeError before 3.10 unless annotations are postponed.

    The package advertises support down to requires-python, so any module using the
    syntax must postpone evaluation.
    """
    offenders = []
    for path in SOURCE_FILES:
        text = path.read_text(encoding="utf-8")
        code = "\n".join(
            line for line in text.splitlines() if not line.strip().startswith("#")
        )
        uses_pep604 = " | None" in code or "None | " in code
        if uses_pep604 and "from __future__ import annotations" not in text:
            offenders.append(path.relative_to(PACKAGE_ROOT).as_posix())
    assert not offenders, (
        "these modules use PEP 604 unions without postponed annotations: "
        f"{offenders}"
    )


def test_every_module_imports_on_the_declared_minimum_version():
    """Guards the floor declared in pyproject against accidental syntax bumps."""
    requires = _pyproject()["project"]["requires-python"]
    assert requires.startswith(">="), requires
    floor = tuple(int(part) for part in requires.removeprefix(">=").split("."))

    if sys.version_info[:2] == floor:
        # Running on the floor already proves it; nothing further to check.
        return

    # Otherwise assert the classifiers do not promise a version below the floor.
    for classifier in _pyproject()["project"]["classifiers"]:
        prefix = "Programming Language :: Python :: "
        if not classifier.startswith(prefix):
            continue
        version = classifier[len(prefix) :]
        if version == "3":
            continue
        promised = tuple(int(part) for part in version.split("."))
        assert promised >= floor, (
            f"classifier promises Python {version}, below requires-python {requires}"
        )


def test_declared_classifiers_cover_the_supported_range():
    classifiers = _pyproject()["project"]["classifiers"]
    running = f"Programming Language :: Python :: {sys.version_info.major}.{sys.version_info.minor}"
    assert running in classifiers, (
        f"tests run on {running.rsplit(' ', 1)[-1]} but it is not advertised"
    )
