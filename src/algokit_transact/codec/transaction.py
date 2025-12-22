from collections.abc import Iterable, Mapping
from typing import cast

from algokit_common.constants import TRANSACTION_DOMAIN_SEPARATOR
from algokit_transact.codec.msgpack import decode_msgpack, encode_msgpack
from algokit_transact.codec.serde import from_wire, to_wire, to_wire_canonical
from algokit_transact.models.transaction import Transaction, TransactionType


def _from_type_str(s: str) -> TransactionType:
    return TransactionType(s)


def to_transaction_dto(tx: Transaction) -> dict[str, object]:
    return to_wire(tx)


def encode_transaction_raw(tx: Transaction) -> bytes:
    canonical = to_wire_canonical(tx)
    return encode_msgpack(canonical)


def encode_transaction(tx: Transaction) -> bytes:
    raw = encode_transaction_raw(tx)
    prefix = TRANSACTION_DOMAIN_SEPARATOR.encode()
    return prefix + raw


def encode_transactions(transactions: Iterable[Transaction]) -> list[bytes]:
    return [encode_transaction(tx) for tx in transactions]


def from_transaction_dto(dto: Mapping[str, object]) -> Transaction:
    return from_wire(Transaction, dto)


def decode_transaction(encoded: bytes) -> Transaction:
    if not encoded:
        raise ValueError("attempted to decode 0 bytes")

    prefix = TRANSACTION_DOMAIN_SEPARATOR.encode()
    payload = encoded[len(prefix) :] if encoded.startswith(prefix) else encoded

    raw = decode_msgpack(payload)
    if not isinstance(raw, dict):
        raise ValueError("decoded msgpack is not a dict")

    return from_transaction_dto(cast(dict[str, object], raw))


def decode_transactions(encoded_transactions: Iterable[bytes]) -> list[Transaction]:
    return [decode_transaction(item) for item in encoded_transactions]


def get_encoded_transaction_type(encoded_transaction: bytes) -> TransactionType:
    prefix = TRANSACTION_DOMAIN_SEPARATOR.encode()
    payload = encoded_transaction[len(prefix) :] if encoded_transaction.startswith(prefix) else encoded_transaction

    raw = decode_msgpack(payload)
    if isinstance(raw, dict) and isinstance(tx_type := raw.get("type"), str):
        return _from_type_str(tx_type)

    return decode_transaction(encoded_transaction).transaction_type
