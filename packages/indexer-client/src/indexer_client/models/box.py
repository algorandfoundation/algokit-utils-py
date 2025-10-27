from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class Box:
    """
    Box name and its content.
    """

    name: bytes = field(
        metadata=wire("name"),
    )
    round_: int = field(
        metadata=wire("round"),
    )
    value: bytes = field(
        metadata=wire("value"),
    )
