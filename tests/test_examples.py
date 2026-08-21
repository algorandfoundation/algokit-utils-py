"""Runs every docs example in ``examples/`` against LocalNet and validates its snippet markers."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
EXAMPLE_TIMEOUT_SECONDS = 120

EXAMPLE_FILES = sorted(
    path for path in EXAMPLES_DIR.glob("**/*.py") if not path.name.startswith("_") and path.name != "__init__.py"
)


def _module_name(example: Path) -> str:
    return ".".join(example.relative_to(REPO_ROOT).with_suffix("").parts)


def _example_id(example: Path) -> str:
    return example.relative_to(EXAMPLES_DIR).with_suffix("").as_posix()


EXAMPLE_IDS = [_example_id(path) for path in EXAMPLE_FILES]


@pytest.mark.parametrize("example", EXAMPLE_FILES, ids=EXAMPLE_IDS)
def test_example_runs(example: Path) -> None:
    module = _module_name(example)
    result = subprocess.run(
        [sys.executable, "-m", module],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=EXAMPLE_TIMEOUT_SECONDS,
        check=False,
    )
    assert result.returncode == 0, (
        f"{module} exited with {result.returncode}\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )


@pytest.mark.parametrize("example", EXAMPLE_FILES, ids=EXAMPLE_IDS)
def test_example_snippet_markers(example: Path) -> None:
    """Each marker name must appear exactly twice and regions must not nest, per RemoteCode."""
    marker_prefix = "# example:"
    markers: list[str] = []
    for line in example.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(marker_prefix):
            markers.append(stripped[len(marker_prefix) :].strip())

    counts = {name: markers.count(name) for name in set(markers)}
    bad_counts = {name: count for name, count in counts.items() if count != 2}
    assert not bad_counts, f"{example.name}: markers must occur exactly twice, got {bad_counts}"

    open_name: str | None = None
    for name in markers:
        if open_name is None:
            open_name = name
        else:
            assert name == open_name, (
                f"{example.name}: region '{open_name}' overlaps with '{name}'; regions cannot nest"
            )
            open_name = None
    assert open_name is None, f"{example.name}: region '{open_name}' was never closed"
