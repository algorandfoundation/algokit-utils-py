from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class HoldingRef:
    """
    HoldingRef names a holding by referring to an Address and Asset it belongs to.
    """

    address: str = field(
        metadata=wire("address"),
    )
    asset: int = field(
        metadata=wire("asset"),
    )
