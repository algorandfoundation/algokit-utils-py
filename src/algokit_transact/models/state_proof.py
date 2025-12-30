from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import cast

from algokit_transact.codec.serde import bytes_seq, from_wire, int_seq, nested, to_wire, wire


@dataclass(slots=True, frozen=True)
class HashFactory:
    hash_type: int | None = field(default=None, metadata=wire("t"))


@dataclass(slots=True, frozen=True)
class MerkleArrayProof:
    path: list[bytes] | None = field(default=None, metadata=bytes_seq("pth"))
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


@dataclass(slots=True, frozen=True)
class StateProof:
    sig_commit: bytes | None = field(default=None, metadata=wire("c"))
    signed_weight: int | None = field(default=None, metadata=wire("w", keep_zero=True))
    sig_proofs: MerkleArrayProof | None = field(default=None, metadata=nested("S", MerkleArrayProof))
    part_proofs: MerkleArrayProof | None = field(default=None, metadata=nested("P", MerkleArrayProof))
    merkle_signature_salt_version: int | None = field(default=None, metadata=wire("v"))
    reveals: dict[int, Reveal] | None = field(
        default=None,
        metadata=wire(
            "r",
            encode=lambda obj: _encode_reveals(cast(dict[int, Reveal] | None, obj)),
            decode=lambda obj: _decode_reveals(obj),
        ),
    )
    positions_to_reveal: list[int] | None = field(default=None, metadata=int_seq("pr"))


@dataclass(slots=True, frozen=True)
class StateProofMessage:
    block_headers_commitment: bytes | None = field(default=None, metadata=wire("b"))
    voters_commitment: bytes | None = field(default=None, metadata=wire("v"))
    ln_proven_weight: int | None = field(default=None, metadata=wire("P"))
    first_attested_round: int | None = field(default=None, metadata=wire("f"))
    last_attested_round: int | None = field(default=None, metadata=wire("l"))


@dataclass(slots=True, frozen=True)
class StateProofTransactionFields:
    state_proof_type: int = field(default=0, metadata=wire("sptype"))
    # Flatten state proof and message at the transaction level (aliases under root: sp and spmsg)
    state_proof: StateProof | None = field(default=None, metadata=nested("sp", StateProof))
    message: StateProofMessage | None = field(default=None, metadata=nested("spmsg", StateProofMessage))


def _encode_reveals(mapping: Mapping[int, Reveal] | Iterable[Reveal] | None) -> dict[int, dict[str, object]] | None:
    if mapping is None:
        return None
    entries: Iterable[tuple[int, Reveal]]
    if isinstance(mapping, Mapping):
        entries = (
            (key if isinstance(key, int) else _coerce_reveal_position(key, idx), reveal)
            for idx, (key, reveal) in enumerate(mapping.items())
        )
    else:
        entries = ((_coerce_reveal_position(None, idx), reveal) for idx, reveal in enumerate(mapping))
    encoded: dict[int, dict[str, object]] = {}
    for position, reveal in entries:
        data = to_wire(reveal)
        payload = {key: value for key in ("p", "s") if (value := data.get(key)) is not None}
        if payload:
            encoded[int(position)] = payload
    return encoded or None


def _decode_reveals(obj: object | None) -> dict[int, Reveal] | None:
    if obj is None:
        return None

    if isinstance(obj, Mapping):
        decoded: dict[int, Reveal] = {}
        for key, value in obj.items():
            if not isinstance(value, Mapping):
                continue
            position = _coerce_reveal_position(key, len(decoded))
            payload = {k: v for k, v in value.items() if k in {"p", "s"}}
            if payload:
                decoded[position] = from_wire(Reveal, payload)
        return decoded or None

    if isinstance(obj, list):
        decoded_list: dict[int, Reveal] = {}
        for idx, value in enumerate(obj):
            if not isinstance(value, Mapping):
                continue
            position = _coerce_reveal_position(value.get("pos"), idx)
            payload = {k: v for k, v in value.items() if k in {"p", "s"}}
            if payload:
                decoded_list[position] = from_wire(Reveal, payload)
        return decoded_list or None

    return None


def _coerce_reveal_position(raw: object, fallback: int) -> int:
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        try:
            return int(raw)
        except ValueError:
            return fallback
    # Fallback silently to preserve legacy behavior when nodes omit this field.
    return fallback
