# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .merkle_array_proof import MerkleArrayProof


@dataclass(slots=True)
class StateProofSignature:
    falcon_signature: bytes | None = field(
        default=None,
        metadata=wire("falcon-signature"),
    )
    merkle_array_index: int | None = field(
        default=None,
        metadata=wire("merkle-array-index"),
    )
    proof: MerkleArrayProof | None = field(
        default=None,
        metadata=nested("proof", lambda: MerkleArrayProof),
    )
    verifying_key: bytes | None = field(
        default=None,
        metadata=wire("verifying-key"),
    )
