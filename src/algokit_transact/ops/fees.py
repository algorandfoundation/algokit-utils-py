from dataclasses import replace

from algokit_common.constants import SIGNATURE_ENCODING_INCR
from algokit_transact.codec.transaction import encode_transaction_raw
from algokit_transact.models.transaction import Transaction


def estimate_transaction_size(tx: Transaction) -> int:
    raw = encode_transaction_raw(tx)
    return len(raw) + SIGNATURE_ENCODING_INCR


def calculate_fee(
    tx: Transaction,
    *,
    fee_per_byte: int,
    min_fee: int,
    extra_fee: int | None = None,
    max_fee: int | None = None,
) -> int:
    fee = 0
    if fee_per_byte > 0:
        fee = fee_per_byte * estimate_transaction_size(tx)
    fee = max(fee, min_fee)
    if extra_fee is not None:
        fee += extra_fee
    if max_fee is not None and fee > max_fee:
        raise ValueError(f"Transaction fee {fee} µALGO is greater than max fee {max_fee} µALGO")
    return fee


def assign_fee(
    tx: Transaction,
    *,
    fee_per_byte: int,
    min_fee: int,
    extra_fee: int | None = None,
    max_fee: int | None = None,
) -> Transaction:
    fee = calculate_fee(
        tx,
        fee_per_byte=fee_per_byte,
        min_fee=min_fee,
        extra_fee=extra_fee,
        max_fee=max_fee,
    )
    return replace(tx, fee=fee)
