from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .box_reference import BoxReference
from .holding_ref import HoldingRef
from .locals_ref import LocalsRef


@dataclass(slots=True)
class ResourceRef:
    """
    ResourceRef names a single resource. Only one of the fields should be set.
    """

    address: str | None = field(
        default=None,
        metadata=wire("address"),
    )
    application_id: int | None = field(
        default=None,
        metadata=wire("application-id"),
    )
    asset_id: int | None = field(
        default=None,
        metadata=wire("asset-id"),
    )
    box: BoxReference | None = field(
        default=None,
        metadata=nested("box", lambda: BoxReference),
    )
    holding: HoldingRef | None = field(
        default=None,
        metadata=nested("holding", lambda: HoldingRef),
    )
    local: LocalsRef | None = field(
        default=None,
        metadata=nested("local", lambda: LocalsRef),
    )
