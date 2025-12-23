from collections.abc import Iterable
from typing import cast

from algokit_transact.codec.msgpack import decode_msgpack, encode_msgpack
from algokit_transact.codec.serde import from_wire, to_wire_canonical
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction
from algokit_transact.signing.logic_signature import LogicSigSignature


def encode_signed_transaction(stx: SignedTransaction) -> bytes:
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
    if not isinstance(stx.txn, Transaction):
        raise ValueError("signed transaction missing 'txn'")
    return stx


def decode_signed_transactions(encoded_signed_transactions: Iterable[bytes]) -> list[SignedTransaction]:
    return [decode_signed_transaction(item) for item in encoded_signed_transactions]


def decode_logic_signature(encoded: bytes) -> LogicSigSignature:
    raw: object = decode_msgpack(encoded)
    if not isinstance(raw, dict):
        raise ValueError("decoded logic signature is not a dict")
    dto = raw
    return from_wire(LogicSigSignature, dto)
