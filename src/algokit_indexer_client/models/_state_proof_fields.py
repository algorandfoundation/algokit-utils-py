# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._merkle_array_proof import MerkleArrayProof
from ._serde_helpers import decode_bytes, decode_model_sequence, encode_bytes, encode_model_sequence
from ._state_proof_reveal import StateProofReveal


@dataclass(slots=True)
class StateProofFields:
    r"""
    \[sp\] represents a state proof.

    Definition:
    crypto/stateproof/structs.go : StateProof
    """

    part_proofs: MerkleArrayProof | None = field(
        default=None,
        metadata=nested("part-proofs", lambda: MerkleArrayProof),
    )
    positions_to_reveal: list[int] | None = field(
        default=None,
        metadata=wire("positions-to-reveal"),
    )
    reveals: list[StateProofReveal] | None = field(
        default=None,
        metadata=wire(
            "reveals",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: StateProofReveal, raw),
        ),
    )
    salt_version: int | None = field(
        default=None,
        metadata=wire("salt-version"),
    )
    sig_commit: bytes | None = field(
        default=None,
        metadata=wire(
            "sig-commit",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    sig_proofs: MerkleArrayProof | None = field(
        default=None,
        metadata=nested("sig-proofs", lambda: MerkleArrayProof),
    )
    signed_weight: int | None = field(
        default=None,
        metadata=wire("signed-weight"),
    )
