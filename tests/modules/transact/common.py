"""Shared helpers for Algokit Transact pytest suites.

This module mirrors the role of ``common.ts`` in the TypeScript workspace by
providing ready-to-use test vectors and helpers for parametrisation.
"""

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, SupportsInt, TypeVar

from algokit_transact import (
    AppCallTransactionFields,
    AssetConfigTransactionFields,
    AssetFreezeTransactionFields,
    AssetTransferTransactionFields,
    BoxReference,
    FalconSignatureStruct,
    FalconVerifier,
    HashFactory,
    HeartbeatProof,
    HeartbeatTransactionFields,
    KeyRegistrationTransactionFields,
    MerkleArrayProof,
    MerkleSignatureVerifier,
    OnApplicationComplete,
    Participant,
    PaymentTransactionFields,
    Reveal,
    SigslotCommit,
    StateProof,
    StateProofMessage,
    StateProofTransactionFields,
    StateSchema,
    Transaction,
    TransactionType,
)

T = TypeVar("T")

TESTS_DIR = Path(__file__).resolve().parent
DATA_PATH = TESTS_DIR / "data" / "test_data.json"


@dataclass(frozen=True)
class TransactionVector:
    """Python-friendly representation of a single transaction test case."""

    name: str
    transaction: Transaction
    unsigned_bytes: bytes
    signed_bytes: bytes | None
    id: str | None
    id_raw: bytes | None
    signing_private_key: bytes | None
    rekeyed_sender_auth_address: str | None
    rekeyed_sender_signed_bytes: bytes | None
    multisig_addresses: tuple[str, ...]
    multisig_signed_bytes: bytes | None
    raw: Mapping[str, Any]


def _bytes_or_none(value: object) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes | bytearray):
        return bytes(value)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return bytes(value)
    raise TypeError(f"Expected byte-like sequence, received {type(value)!r}")


def _tuple_or_none(seq: Iterable[Any] | None, caster: Callable[[Any], T]) -> tuple[T, ...] | None:
    if seq is None:
        return None
    items = tuple(caster(item) for item in seq)
    return items or None


def _tuple_bytes(seq: Iterable[Any] | None) -> tuple[bytes, ...] | None:
    if seq is None:
        return None
    items: list[bytes] = []
    for item in seq:
        b = _bytes_or_none(item)
        if b is not None:
            items.append(b)
    return tuple(items) if items else None


def _parse_state_schema(payload: Mapping[str, Any] | None) -> StateSchema | None:
    if not payload:
        return None
    return StateSchema(
        num_uints=int(payload.get("numUints", 0)),
        num_byte_slices=int(payload.get("numByteSlices", 0)),
    )


def _parse_payment(payload: Mapping[str, Any] | None) -> PaymentTransactionFields | None:
    if not payload:
        return None
    return PaymentTransactionFields(
        amount=int(payload["amount"]),
        receiver=str(payload["receiver"]),
        close_remainder_to=payload.get("closeRemainderTo"),
    )


def _parse_asset_transfer(payload: Mapping[str, Any] | None) -> AssetTransferTransactionFields | None:
    if not payload:
        return None
    return AssetTransferTransactionFields(
        asset_id=int(payload["assetId"]),
        amount=int(payload["amount"]),
        receiver=str(payload["receiver"]),
        close_remainder_to=payload.get("closeRemainderTo"),
        asset_sender=payload.get("assetSender"),
    )


def _parse_asset_config(payload: Mapping[str, Any] | None) -> AssetConfigTransactionFields | None:
    if not payload:
        return None
    return AssetConfigTransactionFields(
        asset_id=int(payload["assetId"]),
        total=_maybe_int(payload.get("total")),
        decimals=_maybe_int(payload.get("decimals")),
        default_frozen=_maybe_bool(payload.get("defaultFrozen")),
        unit_name=payload.get("unitName"),
        asset_name=payload.get("assetName"),
        url=payload.get("url"),
        metadata_hash=_bytes_or_none(payload.get("metadataHash")),
        manager=payload.get("manager"),
        reserve=payload.get("reserve"),
        freeze=payload.get("freeze"),
        clawback=payload.get("clawback"),
    )


def _parse_app_call(payload: Mapping[str, Any] | None) -> AppCallTransactionFields | None:
    if not payload:
        return None
    args = _tuple_bytes(payload.get("args"))
    account_refs = _tuple_or_none(payload.get("accountReferences"), str)
    app_refs = _tuple_or_none(payload.get("appReferences"), int)
    asset_refs = _tuple_or_none(payload.get("assetReferences"), int)
    return AppCallTransactionFields(
        app_id=int(payload.get("appId", 0)),
        on_complete=OnApplicationComplete[payload.get("onComplete", "NoOp")],
        approval_program=_bytes_or_none(payload.get("approvalProgram")),
        clear_state_program=_bytes_or_none(payload.get("clearStateProgram")),
        global_state_schema=_parse_state_schema(payload.get("globalStateSchema")),
        local_state_schema=_parse_state_schema(payload.get("localStateSchema")),
        args=args,
        account_references=account_refs,
        app_references=app_refs,
        asset_references=asset_refs,
        extra_program_pages=_maybe_int(payload.get("extraProgramPages")),
        box_references=_parse_box_references(payload.get("boxReferences")),
    )


def _parse_box_references(payload: object | None) -> tuple[BoxReference, ...] | None:
    if not isinstance(payload, Iterable):
        return None
    refs: list[BoxReference] = []
    for item in payload:
        if not isinstance(item, Mapping):
            continue
        name = _bytes_or_none(item.get("name")) or b""
        refs.append(
            BoxReference(
                app_id=_maybe_int(item.get("appId")) or 0,
                name=name,
            )
        )
    return tuple(refs) if refs else None


def _parse_key_registration(payload: Mapping[str, Any] | None) -> KeyRegistrationTransactionFields | None:
    if payload is None:
        return None
    return KeyRegistrationTransactionFields(
        vote_key=_bytes_or_none(payload.get("voteKey")),
        selection_key=_bytes_or_none(payload.get("selectionKey")),
        vote_first=_maybe_int(payload.get("voteFirst")),
        vote_last=_maybe_int(payload.get("voteLast")),
        vote_key_dilution=_maybe_int(payload.get("voteKeyDilution")),
        state_proof_key=_bytes_or_none(payload.get("stateProofKey")),
        non_participation=_maybe_bool(payload.get("nonParticipation")),
    )


def _parse_asset_freeze(payload: Mapping[str, Any] | None) -> AssetFreezeTransactionFields | None:
    if not payload:
        return None
    frozen = payload.get("frozen")
    if frozen is None:
        frozen = False
    return AssetFreezeTransactionFields(
        asset_id=int(payload["assetId"]),
        freeze_target=str(payload["freezeTarget"]),
        frozen=bool(frozen),
    )


def _parse_heartbeat(payload: Mapping[str, Any] | None) -> HeartbeatTransactionFields | None:
    if not payload:
        return None
    proof_payload = payload.get("proof") if isinstance(payload.get("proof"), Mapping) else None
    proof = None
    if proof_payload is not None:
        proof = HeartbeatProof(
            signature=_bytes_or_none(proof_payload.get("sig")),
            public_key=_bytes_or_none(proof_payload.get("pk")),
            public_key_2=_bytes_or_none(proof_payload.get("pk2")),
            public_key_1_signature=_bytes_or_none(proof_payload.get("pk1Sig")),
            public_key_2_signature=_bytes_or_none(proof_payload.get("pk2Sig")),
        )
    return HeartbeatTransactionFields(
        address=payload.get("address"),
        proof=proof,
        seed=_bytes_or_none(payload.get("seed")),
        vote_id=_bytes_or_none(payload.get("voteId")),
        key_dilution=_maybe_int(payload.get("keyDilution")),
    )


def _parse_hash_factory(payload: Mapping[str, Any] | None) -> HashFactory | None:
    if not payload:
        return None
    return HashFactory(hash_type=_maybe_int(payload.get("hashType")))


def _parse_merkle_array_proof(payload: Mapping[str, Any] | None) -> MerkleArrayProof | None:
    if not payload:
        return None
    path_payload = payload.get("path")
    path: tuple[bytes, ...] | None = None
    if isinstance(path_payload, list):
        converted_path: list[bytes] = []
        for item in path_payload:
            item_bytes = _bytes_or_none(item)
            if item_bytes is None:
                raise TypeError("Expected byte-like path entry")
            converted_path.append(item_bytes)
        path = tuple(converted_path)
    return MerkleArrayProof(
        path=path,
        hash_factory=_parse_hash_factory(payload.get("hashFactory"))
        if isinstance(payload.get("hashFactory"), Mapping)
        else None,
        tree_depth=_maybe_int(payload.get("treeDepth")),
    )


def _parse_merkle_signature_verifier(payload: Mapping[str, Any] | None) -> MerkleSignatureVerifier | None:
    if not payload:
        return None
    return MerkleSignatureVerifier(
        commitment=_bytes_or_none(payload.get("commitment")),
        key_lifetime=_maybe_int(payload.get("keyLifetime")),
    )


def _parse_participant(payload: Mapping[str, Any] | None) -> Participant | None:
    if not payload:
        return None
    return Participant(
        verifier=_parse_merkle_signature_verifier(
            payload.get("verifier") if isinstance(payload.get("verifier"), Mapping) else None
        ),
        weight=_maybe_int(payload.get("weight")),
    )


def _parse_falcon_verifier(payload: Mapping[str, Any] | None) -> FalconVerifier | None:
    if not payload:
        return None
    return FalconVerifier(public_key=_bytes_or_none(payload.get("publicKey")))


def _parse_falcon_signature(payload: Mapping[str, Any] | None) -> FalconSignatureStruct | None:
    if not payload:
        return None
    return FalconSignatureStruct(
        signature=_bytes_or_none(payload.get("signature")),
        vector_commitment_index=_maybe_int(payload.get("vectorCommitmentIndex")),
        proof=_parse_merkle_array_proof(payload.get("proof") if isinstance(payload.get("proof"), Mapping) else None),
        verifying_key=_parse_falcon_verifier(
            payload.get("verifyingKey") if isinstance(payload.get("verifyingKey"), Mapping) else None
        ),
    )


def _parse_sigslot(payload: Mapping[str, Any] | None) -> SigslotCommit | None:
    if not payload:
        return None
    return SigslotCommit(
        sig=_parse_falcon_signature(payload.get("sig") if isinstance(payload.get("sig"), Mapping) else None),
        lower_sig_weight=_maybe_int(payload.get("lowerSigWeight")),
    )


def _parse_reveals(payload: object) -> tuple[Reveal, ...] | None:
    if not isinstance(payload, list):
        return None
    reveals: list[Reveal] = []
    for item in payload:
        if not isinstance(item, Mapping):
            continue
        reveals.append(
            Reveal(
                participant=_parse_participant(
                    item.get("participant") if isinstance(item.get("participant"), Mapping) else None
                ),
                sigslot=_parse_sigslot(item.get("sigslot") if isinstance(item.get("sigslot"), Mapping) else None),
                position=_maybe_int(item.get("position", 0)),
            )
        )
    return tuple(reveals)


def _parse_state_proof(payload: Mapping[str, Any] | None) -> StateProof | None:
    if not payload:
        return None
    return StateProof(
        sig_commit=_bytes_or_none(payload.get("sigCommit")),
        signed_weight=_maybe_int(payload.get("signedWeight")),
        sig_proofs=_parse_merkle_array_proof(
            payload.get("sigProofs") if isinstance(payload.get("sigProofs"), Mapping) else None
        ),
        part_proofs=_parse_merkle_array_proof(
            payload.get("partProofs") if isinstance(payload.get("partProofs"), Mapping) else None
        ),
        merkle_signature_salt_version=_maybe_int(payload.get("merkleSignatureSaltVersion")),
        reveals=_parse_reveals(payload.get("reveals")),
        positions_to_reveal=_tuple_or_none(payload.get("positionsToReveal"), int),
    )


def _parse_state_proof_message(payload: Mapping[str, Any] | None) -> StateProofMessage | None:
    if not payload:
        return None
    return StateProofMessage(
        block_headers_commitment=_bytes_or_none(payload.get("blockHeadersCommitment")),
        voters_commitment=_bytes_or_none(payload.get("votersCommitment")),
        ln_proven_weight=_maybe_int(payload.get("lnProvenWeight")),
        first_attested_round=_maybe_int(payload.get("firstAttestedRound")),
        last_attested_round=_maybe_int(payload.get("lastAttestedRound")),
    )


def _parse_state_proof_fields(payload: Mapping[str, Any] | None) -> StateProofTransactionFields | None:
    if not payload:
        return None
    return StateProofTransactionFields(
        state_proof_type=_maybe_int(payload.get("stateProofType")),
        state_proof=_parse_state_proof(
            payload.get("stateProof") if isinstance(payload.get("stateProof"), Mapping) else None
        ),
        message=_parse_state_proof_message(
            payload.get("message") if isinstance(payload.get("message"), Mapping) else None
        ),
    )


def _maybe_int(value: SupportsInt | str | bytes | bytearray | None) -> int | None:
    if value is None:
        return None
    return int(value)


def _maybe_bool(value: object | None) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _parse_transaction(payload: Mapping[str, Any]) -> Transaction:
    tx_type_raw = payload["transactionType"]
    tx_type = TransactionType[tx_type_raw]
    return Transaction(
        transaction_type=tx_type,
        sender=str(payload["sender"]),
        first_valid=int(payload["firstValid"]),
        last_valid=int(payload["lastValid"]),
        fee=_maybe_int(payload.get("fee")),
        genesis_hash=_bytes_or_none(payload.get("genesisHash")),
        genesis_id=payload.get("genesisId"),
        note=_bytes_or_none(payload.get("note")),
        rekey_to=payload.get("rekeyTo"),
        lease=_bytes_or_none(payload.get("lease")),
        group=_bytes_or_none(payload.get("group")),
        payment=_parse_payment(payload.get("payment")),
        asset_transfer=_parse_asset_transfer(payload.get("assetTransfer")),
        asset_config=_parse_asset_config(payload.get("assetConfig")),
        app_call=_parse_app_call(payload.get("appCall")),
        key_registration=_parse_key_registration(payload.get("keyRegistration")),
        asset_freeze=_parse_asset_freeze(payload.get("assetFreeze")),
        heartbeat=_parse_heartbeat(payload.get("heartbeat")),
        state_proof=_parse_state_proof_fields(payload.get("stateProof")),
    )


@lru_cache(maxsize=1)
def load_raw_vectors() -> Mapping[str, Any]:
    """Return the parsed JSON payload exactly as stored on disk."""

    data = json.loads(DATA_PATH.read_text())
    if not isinstance(data, dict):
        raise TypeError("Malformed test vector payload")
    return data


@lru_cache(maxsize=1)
def load_test_vectors() -> Mapping[str, TransactionVector]:
    """Return the fully parsed transaction vectors."""

    raw = load_raw_vectors()
    vectors: dict[str, TransactionVector] = {}
    for name, payload in raw.items():
        transaction = _parse_transaction(payload["transaction"])
        vectors[name] = TransactionVector(
            name=name,
            transaction=transaction,
            unsigned_bytes=_require_bytes(payload.get("unsignedBytes"), f"{name}.unsignedBytes"),
            signed_bytes=_bytes_or_none(payload.get("signedBytes")),
            id=payload.get("id"),
            id_raw=_bytes_or_none(payload.get("idRaw")),
            signing_private_key=_bytes_or_none(payload.get("signingPrivateKey")),
            rekeyed_sender_auth_address=payload.get("rekeyedSenderAuthAddress"),
            rekeyed_sender_signed_bytes=_bytes_or_none(payload.get("rekeyedSenderSignedBytes")),
            multisig_addresses=tuple(payload.get("multisigAddresses", [])),
            multisig_signed_bytes=_bytes_or_none(payload.get("multisigSignedBytes")),
            raw=payload,
        )
    return vectors


def _require_bytes(value: object | None, label: str) -> bytes:
    result = _bytes_or_none(value)
    if result is None:
        raise ValueError(f"Expected byte sequence for {label}")
    return result


def get_test_vector(name: str) -> TransactionVector:
    """Convenience accessor mirroring ``testData.<name>`` in TS."""

    vectors = load_test_vectors()
    try:
        return vectors[name]
    except KeyError as exc:  # pragma: no cover - defensive guard for future ports
        raise KeyError(f"Unknown test vector: {name!r}") from exc


def iter_test_vectors(*names: str) -> Iterable[TransactionVector]:
    """Yield vectors for the provided names, or all of them if none supplied."""

    vectors = load_test_vectors()
    if not names:
        return vectors.values()
    return (vectors[name] for name in names)


__all__ = [
    "TransactionVector",
    "get_test_vector",
    "iter_test_vectors",
    "load_test_vectors",
]
