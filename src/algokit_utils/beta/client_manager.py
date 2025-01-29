from typing import Any

from algokit_utils.beta._utils import handle_getattr


def __getattr__(name: str) -> Any:  # noqa: ANN401
    """Handle deprecated imports of parameter classes"""

    handle_getattr(name)
