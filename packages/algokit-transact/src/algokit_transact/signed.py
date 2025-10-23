from __future__ import annotations

from collections import OrderedDict

import msgpack

from .codec import to_transaction_dto
from .types import SignedTransaction


def encode_signed_transaction(stx: SignedTransaction) -> bytes:
    dto = to_transaction_dto(stx.transaction)
    payload = OrderedDict(
        [
            ("sig", stx.signature),
            ("txn", dto),
        ]
    )
    return msgpack.packb(payload, use_bin_type=True, strict_types=True)


def decode_signed_transaction(encoded: bytes) -> SignedTransaction:
    dto = msgpack.unpackb(encoded, raw=False)
    if not isinstance(dto, dict):
        raise ValueError("decoded signed transaction is not a dict")
    sig = dto.get("sig")
    if not isinstance(sig, bytes | bytearray):
        raise ValueError("signed transaction missing 'sig'")
    txn = dto.get("txn")
    if not isinstance(txn, dict):
        raise ValueError("signed transaction missing 'txn'")
    from .codec import from_transaction_dto

    return SignedTransaction(transaction=from_transaction_dto(txn), signature=bytes(sig))
