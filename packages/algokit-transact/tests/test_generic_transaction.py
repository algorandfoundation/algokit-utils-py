from __future__ import annotations

import pytest
from algokit_transact import (
    AppCallTransactionFields,
    Transaction,
    TransactionType,
    assign_fee,
    calculate_fee,
    decode_transaction,
)


def test_malformed_bytes() -> None:
    with pytest.raises(ValueError, match="decoded msgpack is not a dict"):
        decode_transaction(b"\x01")


def test_encode_0_bytes() -> None:
    with pytest.raises(ValueError, match="^attempted to decode 0 bytes$"):
        decode_transaction(b"")


def _sample_app_call_tx() -> Transaction:
    return Transaction(
        transaction_type=TransactionType.AppCall,
        sender="XBYLS2E6YI6XXL5BWCAMOA4GTWHXWENZMX5UHXMRNWWUQ7BXCY5WC5TEPA",
        first_valid=1,
        last_valid=2,
        app_call=AppCallTransactionFields(approval_program=b"\x01", clear_state_program=b"\x02"),
    )


def test_calculate_fee_matches_assign_fee() -> None:
    tx = _sample_app_call_tx()
    fee = calculate_fee(tx, fee_per_byte=10, min_fee=1000)
    assigned = assign_fee(tx, fee_per_byte=10, min_fee=1000)
    assert assigned.fee == fee
