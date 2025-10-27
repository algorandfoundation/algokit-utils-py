from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .allocations_for_genesis_file import AllocationsForGenesisFile


@dataclass(slots=True)
class GenesisFileInJson:
    alloc: list[AllocationsForGenesisFile] = field(
        metadata=wire(
            "alloc",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AllocationsForGenesisFile, raw),
        ),
    )
    fees: str = field(
        metadata=wire("fees"),
    )
    id_: str = field(
        metadata=wire("id"),
    )
    network: str = field(
        metadata=wire("network"),
    )
    proto: str = field(
        metadata=wire("proto"),
    )
    rwd: str = field(
        metadata=wire("rwd"),
    )
    timestamp: int = field(
        metadata=wire("timestamp"),
    )
    comment: str | None = field(
        default=None,
        metadata=wire("comment"),
    )
    devmode: bool | None = field(
        default=None,
        metadata=wire("devmode"),
    )
