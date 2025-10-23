from __future__ import annotations

from .codec import encode_transaction
from .constants import TRANSACTION_ID_LENGTH
from .hashing import base32_nopad_encode, sha512_256
from .types import Transaction


def get_transaction_id_raw(transaction: Transaction) -> bytes:
    encoded = encode_transaction(transaction)
    return sha512_256(encoded)


def get_transaction_id(transaction: Transaction) -> str:
    raw = get_transaction_id_raw(transaction)
    return base32_nopad_encode(raw)[:TRANSACTION_ID_LENGTH]
