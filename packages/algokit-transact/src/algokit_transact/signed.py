from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from .address import address_from_public_key, public_key_from_address
from .codec import _omit_defaults_and_sort, to_transaction_dto
from .constants import SIGNATURE_BYTE_LENGTH
from .dto import LogicSignatureDto, MultisigDto, MultisigSubsigDto, TransactionDto
from .dto_utils import require_bytes
from .msgpack_utils import decode_msgpack, encode_msgpack
from .types import (
    LogicSignature,
    MultisigSignature,
    MultisigSubsignature,
    SignedTransaction,
)
from .validation import validate_transaction


def _validate_signed_transaction(stx: SignedTransaction) -> None:
    validate_transaction(stx.transaction)

    signatures = [stx.signature, stx.multi_signature, stx.logic_signature]
    set_count = sum(1 for item in signatures if item is not None)
    if set_count == 0:
        raise ValueError("At least one signature type must be set")
    if set_count > 1:
        raise ValueError("Only one signature type can be set")

    if stx.signature is not None and len(stx.signature) != SIGNATURE_BYTE_LENGTH:
        raise ValueError("Signature must be 64 bytes")


def _multisig_to_dto(msig: MultisigSignature | None) -> MultisigDto | None:
    if msig is None:
        return None

    subsig_dtos: list[MultisigSubsigDto] = []
    for subsig in msig.subsignatures:
        entry: MultisigSubsigDto = {"pk": public_key_from_address(subsig.address)}
        if subsig.signature is not None:
            entry["s"] = subsig.signature
        subsig_dtos.append(entry)

    items: list[tuple[str, object]] = []
    if subsig_dtos:
        items.append(("subsig", subsig_dtos))
    items.append(("thr", msig.threshold))
    items.append(("v", msig.version))
    return cast(MultisigDto, dict(items))


def _logic_to_dto(lsig: LogicSignature | None) -> LogicSignatureDto | None:
    if lsig is None:
        return None
    dto: LogicSignatureDto = {"l": lsig.logic}
    if lsig.args:
        dto["arg"] = list(lsig.args)
    if lsig.signature is not None:
        dto["sig"] = lsig.signature
    msig_dto = _multisig_to_dto(lsig.multi_signature)
    if msig_dto is not None:
        dto["msig"] = msig_dto
    return dto


def encode_signed_transaction(stx: SignedTransaction) -> bytes:
    _validate_signed_transaction(stx)
    # Build canonical DTO directly (omit defaults and sort keys) to avoid msgpack round-trip
    txn_dto = cast(TransactionDto, _omit_defaults_and_sort(dict(to_transaction_dto(stx.transaction))))

    items: list[tuple[str, object]] = []
    if stx.auth_address is not None:
        items.append(("sgnr", public_key_from_address(stx.auth_address)))
    if stx.signature is not None:
        items.append(("sig", stx.signature))
    msig_dto = _multisig_to_dto(stx.multi_signature)
    if msig_dto is not None:
        items.append(("msig", msig_dto))
    lsig_dto = _logic_to_dto(stx.logic_signature)
    if lsig_dto is not None:
        items.append(("lsig", lsig_dto))
    items.append(("txn", txn_dto))

    return encode_msgpack(dict(items))


def encode_signed_transactions(signed_transactions: Iterable[SignedTransaction]) -> list[bytes]:
    return [encode_signed_transaction(stx) for stx in signed_transactions]


def _dto_to_multisig(msig_dto: object | None) -> MultisigSignature | None:
    if not isinstance(msig_dto, dict):
        return None
    version = msig_dto.get("v")
    threshold = msig_dto.get("thr")
    subsig_payload = msig_dto.get("subsig")
    subsigs: list[MultisigSubsignature] = []
    if isinstance(subsig_payload, list):
        for entry in subsig_payload:
            if not isinstance(entry, dict):
                continue
            pk = entry.get("pk")
            signature = entry.get("s")
            if isinstance(pk, bytes | bytearray):
                address = address_from_public_key(bytes(pk))
                sig_bytes = bytes(signature) if isinstance(signature, bytes | bytearray) else None
                subsigs.append(MultisigSubsignature(address=address, signature=sig_bytes))
    return MultisigSignature(
        version=int(version or 0),
        threshold=int(threshold or 0),
        subsignatures=tuple(subsigs),
    )


def _dto_to_logic(lsig_dto: object | None) -> LogicSignature | None:
    if not isinstance(lsig_dto, dict):
        return None
    logic = require_bytes(lsig_dto.get("l"), field="logic signature logic program")
    args_payload = lsig_dto.get("arg")
    args: tuple[bytes, ...] | None = None
    if isinstance(args_payload, list):
        args = tuple(bytes(arg) for arg in args_payload if isinstance(arg, bytes | bytearray))
        if not args:
            args = None
    signature = lsig_dto.get("sig")
    msig = _dto_to_multisig(lsig_dto.get("msig"))
    return LogicSignature(
        logic=bytes(logic),
        args=args,
        signature=bytes(signature) if isinstance(signature, bytes | bytearray) else None,
        multi_signature=msig,
    )


def decode_signed_transaction(encoded: bytes) -> SignedTransaction:
    raw: object = decode_msgpack(encoded)
    if not isinstance(raw, dict):
        raise ValueError("decoded signed transaction is not a dict")
    dto = cast(dict[str, object], raw)
    txn = dto.get("txn")
    if not isinstance(txn, dict):
        raise ValueError("signed transaction missing 'txn'")
    txn_dict = cast(TransactionDto, txn)

    sig = dto.get("sig")
    raw_sig = bytes(sig) if isinstance(sig, bytes | bytearray) else None

    msig = _dto_to_multisig(dto.get("msig")) if dto.get("msig") is not None else None
    lsig = _dto_to_logic(dto.get("lsig")) if dto.get("lsig") is not None else None
    auth_address = None
    sgnr = dto.get("sgnr")
    if isinstance(sgnr, bytes | bytearray):
        auth_address = address_from_public_key(bytes(sgnr))

    from .codec import from_transaction_dto

    return SignedTransaction(
        transaction=from_transaction_dto(txn_dict),
        signature=raw_sig,
        multi_signature=msig,
        logic_signature=lsig,
        auth_address=auth_address,
    )


def decode_signed_transactions(encoded_signed_transactions: Iterable[bytes]) -> list[SignedTransaction]:
    return [decode_signed_transaction(item) for item in encoded_signed_transactions]
