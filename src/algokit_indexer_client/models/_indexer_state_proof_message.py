# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class IndexerStateProofMessage:
    block_headers_commitment: bytes | None = field(
        default=None,
        metadata=wire(
            "block-headers-commitment",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    first_attested_round: int | None = field(
        default=None,
        metadata=wire("first-attested-round"),
    )
    latest_attested_round: int | None = field(
        default=None,
        metadata=wire("latest-attested-round"),
    )
    ln_proven_weight: int | None = field(
        default=None,
        metadata=wire("ln-proven-weight"),
    )
    voters_commitment: bytes | None = field(
        default=None,
        metadata=wire(
            "voters-commitment",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
