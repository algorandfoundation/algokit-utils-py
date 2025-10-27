from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BoxReference:
    """
    BoxReference names a box by its name and the application ID it belongs to.
    """

    app: int = field(
        metadata=wire("app"),
    )
    name: bytes = field(
        metadata=wire("name"),
    )
