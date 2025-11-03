from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

from algokit_transact.codec.serde import bytes_seq, from_wire, int_seq, nested, to_wire, wire


@dataclass(slots=True, frozen=True)
class HashFactory:
    hash_type: int | None = field(default=None, metadata=wire("t"))


@dataclass(slots=True, frozen=True)
class MerkleArrayProof:
    path: tuple[bytes, ...] | None = field(default=None, metadata=bytes_seq("pth"))
    hash_factory: HashFactory | None = field(default=None, metadata=nested("hsh", HashFactory))
    tree_depth: int | None = field(default=None, metadata=wire("td"))


@dataclass(slots=True, frozen=True)
class MerkleSignatureVerifier:
    commitment: bytes | None = field(default=None, metadata=wire("cmt"))
    key_lifetime: int | None = field(default=None, metadata=wire("lf"))


@dataclass(slots=True, frozen=True)
class Participant:
    verifier: MerkleSignatureVerifier | None = field(default=None, metadata=nested("p", MerkleSignatureVerifier))
    weight: int | None = field(default=None, metadata=wire("w"))


@dataclass(slots=True, frozen=True)
class FalconVerifier:
    public_key: bytes | None = field(default=None, metadata=wire("k"))


@dataclass(slots=True, frozen=True)
class FalconSignatureStruct:
    signature: bytes | None = field(default=None, metadata=wire("sig"))
    vector_commitment_index: int | None = field(default=None, metadata=wire("idx"))
    proof: MerkleArrayProof | None = field(default=None, metadata=nested("prf", MerkleArrayProof))
    verifying_key: FalconVerifier | None = field(default=None, metadata=nested("vkey", FalconVerifier))


@dataclass(slots=True, frozen=True)
class SigslotCommit:
    sig: FalconSignatureStruct | None = field(default=None, metadata=nested("s", FalconSignatureStruct))
    lower_sig_weight: int | None = field(default=None, metadata=wire("l"))


@dataclass(slots=True, frozen=True)
class Reveal:
    participant: Participant | None = field(default=None, metadata=nested("p", Participant))
    sigslot: SigslotCommit | None = field(default=None, metadata=nested("s", SigslotCommit))
    position: int | None = field(default=None, metadata=wire("pos"))


@dataclass(slots=True, frozen=True)
class StateProof:
    sig_commit: bytes | None = field(default=None, metadata=wire("c"))
    signed_weight: int | None = field(default=None, metadata=wire("w", keep_zero=True))
    sig_proofs: MerkleArrayProof | None = field(default=None, metadata=nested("S", MerkleArrayProof))
    part_proofs: MerkleArrayProof | None = field(default=None, metadata=nested("P", MerkleArrayProof))
    merkle_signature_salt_version: int | None = field(default=None, metadata=wire("v"))
    reveals: tuple[Reveal, ...] | None = field(
        default=None,
        metadata=wire(
            "r",
            encode=lambda obj: _encode_reveals(cast(tuple[Reveal, ...] | None, obj)),
            decode=lambda obj: _decode_reveals(obj),
        ),
    )
    positions_to_reveal: tuple[int, ...] | None = field(default=None, metadata=int_seq("pr"))


@dataclass(slots=True, frozen=True)
class StateProofMessage:
    block_headers_commitment: bytes | None = field(default=None, metadata=wire("b"))
    voters_commitment: bytes | None = field(default=None, metadata=wire("v"))
    ln_proven_weight: int | None = field(default=None, metadata=wire("P"))
    first_attested_round: int | None = field(default=None, metadata=wire("f"))
    last_attested_round: int | None = field(default=None, metadata=wire("l"))


@dataclass(slots=True, frozen=True)
class StateProofTransactionFields:
    state_proof_type: int | None = field(default=None, metadata=wire("sptype"))
    # Flatten state proof and message at the transaction level (aliases under root: sp and spmsg)
    state_proof: StateProof | None = field(default=None, metadata=nested("sp", StateProof))
    message: StateProofMessage | None = field(default=None, metadata=nested("spmsg", StateProofMessage))


def _encode_reveals(seq: tuple[Reveal, ...] | None) -> dict[int, dict[str, object]] | None:
    match seq:
        case None | ():
            return None
        case _:
            return {
                pos if isinstance(pos := to_wire(item).get("pos"), int) else idx: {
                    k: v for k in ("p", "s") if (v := to_wire(item).get(k)) is not None
                }
                for idx, item in enumerate(seq)
            }


def _decode_reveals(obj: object | None) -> tuple[Reveal, ...] | None:
    if obj is None:
        return None

    if isinstance(obj, Mapping):
        # Also support legacy map form: { pos: {p:..., s:...} }
        return tuple(
            from_wire(
                Reveal, {**(v if isinstance(v, Mapping) else {}), "pos": int(k) if isinstance(k, int | str) else 0}
            )
            for k, v in obj.items()
        )

    if isinstance(obj, list):
        return tuple(
            from_wire(
                Reveal, {**(v if isinstance(v, Mapping) else {}), "pos": v.get("pos") if isinstance(v, Mapping) else i}
            )
            for i, v in enumerate(obj)
        )

    return None
