from __future__ import annotations

from dataclasses import replace

from .codec import encode_transaction_raw
from .constants import SIGNATURE_ENCODING_INCR
from .types import Transaction


def estimate_transaction_size(tx: Transaction) -> int:
    raw = encode_transaction_raw(tx)
    return len(raw) + SIGNATURE_ENCODING_INCR


def assign_fee(
    tx: Transaction,
    *,
    fee_per_byte: int,
    min_fee: int,
    extra_fee: int | None = None,
    max_fee: int | None = None,
) -> Transaction:
    fee = 0
    if fee_per_byte > 0:
        fee = fee_per_byte * estimate_transaction_size(tx)
    fee = max(fee, min_fee)
    if extra_fee is not None:
        fee += extra_fee
    if max_fee is not None and fee > max_fee:
        raise ValueError(f"Transaction fee {fee} µALGO is greater than max fee {max_fee} µALGO")
    return replace(tx, fee=fee)
