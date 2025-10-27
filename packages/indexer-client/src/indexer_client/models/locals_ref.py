from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class LocalsRef:
    """
    LocalsRef names a local state by referring to an Address and App it belongs to.
    """

    address: str = field(
        metadata=wire("address"),
    )
    app: int = field(
        metadata=wire("app"),
    )
