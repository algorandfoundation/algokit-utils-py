# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class StateProofMessage:
    """
    Represents the message that the state proofs are attesting to.
    """

    block_headers_commitment: bytes = field(
        default=b"",
        metadata=wire(
            "BlockHeadersCommitment",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    first_attested_round: int = field(
        default=0,
        metadata=wire("FirstAttestedRound"),
    )
    last_attested_round: int = field(
        default=0,
        metadata=wire("LastAttestedRound"),
    )
    ln_proven_weight: int = field(
        default=0,
        metadata=wire("LnProvenWeight"),
    )
    voters_commitment: bytes = field(
        default=b"",
        metadata=wire(
            "VotersCommitment",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
