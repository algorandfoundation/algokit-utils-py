"""Shared helpers for Algokit Transact pytest suites.

This module mirrors the role of ``common.ts`` in the TypeScript workspace by
providing ready-to-use test vectors and helpers for parametrisation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from algokit_transact.types import (
    AppCallFields,
    AssetConfigFields,
    AssetFreezeFields,
    AssetTransferFields,
    KeyRegistrationFields,
    OnApplicationComplete,
    PaymentFields,
    StateSchema,
    Transaction,
    TransactionType,
)

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


def _bytes_or_none(value: Any) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return bytes(value)
    raise TypeError(f"Expected byte-like sequence, received {type(value)!r}")


def _tuple_or_none(seq: Iterable[Any] | None, caster) -> tuple[Any, ...] | None:
    if seq is None:
        return None
    items = tuple(caster(item) for item in seq)
    return items or None


def _parse_state_schema(payload: Mapping[str, Any] | None) -> StateSchema | None:
    if not payload:
        return None
    return StateSchema(
        num_uints=int(payload.get("numUints", 0)),
        num_byte_slices=int(payload.get("numByteSlices", 0)),
    )


def _parse_payment(payload: Mapping[str, Any] | None) -> PaymentFields | None:
    if not payload:
        return None
    return PaymentFields(
        amount=int(payload["amount"]),
        receiver=str(payload["receiver"]),
        close_remainder_to=payload.get("closeRemainderTo"),
    )


def _parse_asset_transfer(payload: Mapping[str, Any] | None) -> AssetTransferFields | None:
    if not payload:
        return None
    return AssetTransferFields(
        asset_id=int(payload["assetId"]),
        amount=int(payload["amount"]),
        receiver=str(payload["receiver"]),
        close_remainder_to=payload.get("closeRemainderTo"),
        asset_sender=payload.get("assetSender"),
    )


def _parse_asset_config(payload: Mapping[str, Any] | None) -> AssetConfigFields | None:
    if not payload:
        return None
    return AssetConfigFields(
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


def _parse_app_call(payload: Mapping[str, Any] | None) -> AppCallFields | None:
    if not payload:
        return None
    args = _tuple_or_none(payload.get("args"), _bytes_or_none)
    account_refs = _tuple_or_none(payload.get("accountReferences"), str)
    app_refs = _tuple_or_none(payload.get("appReferences"), int)
    asset_refs = _tuple_or_none(payload.get("assetReferences"), int)
    return AppCallFields(
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
    )


def _parse_key_registration(payload: Mapping[str, Any] | None) -> KeyRegistrationFields | None:
    if not payload:
        return None
    return KeyRegistrationFields(
        vote_key=_bytes_or_none(payload.get("voteKey")),
        selection_key=_bytes_or_none(payload.get("selectionKey")),
        vote_first=_maybe_int(payload.get("voteFirst")),
        vote_last=_maybe_int(payload.get("voteLast")),
        vote_key_dilution=_maybe_int(payload.get("voteKeyDilution")),
        state_proof_key=_bytes_or_none(payload.get("stateProofKey")),
        non_participation=_maybe_bool(payload.get("nonParticipation")),
    )


def _parse_asset_freeze(payload: Mapping[str, Any] | None) -> AssetFreezeFields | None:
    if not payload:
        return None
    frozen = payload.get("frozen")
    if frozen is None:
        frozen = False
    return AssetFreezeFields(
        asset_id=int(payload["assetId"]),
        freeze_target=str(payload["freezeTarget"]),
        frozen=bool(frozen),
    )


def _maybe_int(value: Any | None) -> int | None:
    if value is None:
        return None
    return int(value)


def _maybe_bool(value: Any | None) -> bool | None:
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
    )


@lru_cache(maxsize=1)
def load_raw_vectors() -> Mapping[str, Any]:
    """Return the parsed JSON payload exactly as stored on disk."""

    return json.loads(DATA_PATH.read_text())


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


def _require_bytes(value: Any | None, label: str) -> bytes:
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
