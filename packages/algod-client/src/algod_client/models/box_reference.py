from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BoxReference:
    """
    References a box of an application.
    """

    app: int = field(
        metadata=wire("app"),
    )
    name: bytes = field(
        metadata=wire("name"),
    )
