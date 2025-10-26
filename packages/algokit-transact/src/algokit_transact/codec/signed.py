from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from algokit_common.constants import SIGNATURE_BYTE_LENGTH

from algokit_transact.codec.msgpack import decode_msgpack, encode_msgpack
from algokit_transact.codec.serde import from_wire, to_wire_canonical
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction
from algokit_transact.ops.validate import validate_transaction


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


def encode_signed_transaction(stx: SignedTransaction) -> bytes:
    _validate_signed_transaction(stx)
    payload = to_wire_canonical(stx)
    return encode_msgpack(payload)


def encode_signed_transactions(signed_transactions: Iterable[SignedTransaction]) -> list[bytes]:
    return [encode_signed_transaction(stx) for stx in signed_transactions]


def decode_signed_transaction(encoded: bytes) -> SignedTransaction:
    raw: object = decode_msgpack(encoded)
    if not isinstance(raw, dict):
        raise ValueError("decoded signed transaction is not a dict")
    dto = cast(dict[str, object], raw)
    stx = from_wire(SignedTransaction, dto)
    if not isinstance(stx.transaction, Transaction):
        raise ValueError("signed transaction missing 'txn'")
    return stx


def decode_signed_transactions(encoded_signed_transactions: Iterable[bytes]) -> list[SignedTransaction]:
    return [decode_signed_transaction(item) for item in encoded_signed_transactions]
