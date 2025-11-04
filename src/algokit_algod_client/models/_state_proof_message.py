# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class StateProofMessage:
    """
    Represents the message that the state proofs are attesting to.
    """

    block_headers_commitment: bytes = field(
        metadata=wire("BlockHeadersCommitment"),
    )
    first_attested_round: int = field(
        metadata=wire("FirstAttestedRound"),
    )
    last_attested_round: int = field(
        metadata=wire("LastAttestedRound"),
    )
    ln_proven_weight: int = field(
        metadata=wire("LnProvenWeight"),
    )
    voters_commitment: bytes = field(
        metadata=wire("VotersCommitment"),
    )
