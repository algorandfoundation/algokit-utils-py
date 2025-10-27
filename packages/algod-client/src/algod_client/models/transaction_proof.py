from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class TransactionProof:
    """
    Proof of transaction in a block.
    """

    hashtype: str = field(
        metadata=wire("hashtype"),
    )
    idx: int = field(
        metadata=wire("idx"),
    )
    proof: bytes = field(
        metadata=wire("proof"),
    )
    stibhash: bytes = field(
        metadata=wire("stibhash"),
    )
    treedepth: int = field(
        metadata=wire("treedepth"),
    )
