# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._allocations_for_genesis_file import AllocationsForGenesisFile
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class GenesisFileInJson:
    alloc: list[AllocationsForGenesisFile] = field(
        default_factory=list,
        metadata=wire(
            "alloc",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AllocationsForGenesisFile, raw),
        ),
    )
    fees: str = field(
        default="",
        metadata=wire("fees"),
    )
    id_: str = field(
        default="",
        metadata=wire("id"),
    )
    network: str = field(
        default="",
        metadata=wire("network"),
    )
    proto: str = field(
        default="",
        metadata=wire("proto"),
    )
    rwd: str = field(
        default="",
        metadata=wire("rwd"),
    )
    comment: str | None = field(
        default=None,
        metadata=wire("comment"),
    )
    devmode: bool | None = field(
        default=None,
        metadata=wire("devmode"),
    )
    timestamp: int | None = field(
        default=None,
        metadata=wire("timestamp"),
    )
