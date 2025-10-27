from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class LightBlockHeaderProof:
    """
    Proof of membership and position of a light block header.
    """

    index: int = field(
        metadata=wire("index"),
    )
    proof: bytes = field(
        metadata=wire("proof"),
    )
    treedepth: int = field(
        metadata=wire("treedepth"),
    )
