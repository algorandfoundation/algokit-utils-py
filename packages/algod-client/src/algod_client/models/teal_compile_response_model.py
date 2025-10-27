from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class TealCompileResponseModel:
    hash: str = field(
        metadata=wire("hash"),
    )
    result: str = field(
        metadata=wire("result"),
    )
    sourcemap: dict[str, object] | None = field(
        default=None,
        metadata=wire("sourcemap"),
    )
