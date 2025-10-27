from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BoxDescriptor:
    """
    Box descriptor describes a Box.
    """

    name: bytes = field(
        metadata=wire("name"),
    )
