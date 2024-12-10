import pytest

from algokit_utils import (
    DeploymentFailedError,
    get_next_version,
)


@pytest.mark.parametrize(
    ("current", "expected_next"),
    [
        ("1", "2"),
        ("v1", "v2"),
        ("v1-alpha", "v2-alpha"),
        ("1.0", "1.1"),
        ("v1.0", "v1.1"),
        ("v1.0-alpha", "v1.1-alpha"),
        ("1.0.0", "1.0.1"),
        ("v1.0.0", "v1.0.1"),
        ("v1.0.0-alpha", "v1.0.1-alpha"),
    ],
)
def test_auto_version_increment(current: str, expected_next: str) -> None:
    value = get_next_version(current)
    assert value == expected_next


def test_auto_version_increment_failure() -> None:
    with pytest.raises(DeploymentFailedError):
        get_next_version("teapot")
