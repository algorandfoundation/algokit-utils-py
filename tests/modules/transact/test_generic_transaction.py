import pytest

import msgpack
from algokit_transact import (
    AppCallTransactionFields,
    Transaction,
    TransactionType,
    assign_fee,
    calculate_fee,
    decode_transaction,
)

# Polytest Suite: Generic Transaction

# Polytest Group: Generic Transaction Tests


@pytest.mark.group_generic_transaction_tests
def test_malformed_bytes() -> None:
    """Ensure a helpful error message is thrown when attempting to decode malformed bytes"""
    with pytest.raises(ValueError, match="decoded msgpack is not a dict"):
        decode_transaction(b"\x01")


@pytest.mark.group_generic_transaction_tests
def test_unknown_transaction_type() -> None:
    """Ensure unknown transaction types can be decoded without errors (forward compatibility)"""
    address_bytes = bytes(
        [
            230,
            185,
            154,
            253,
            65,
            13,
            19,
            221,
            14,
            138,
            126,
            148,
            184,
            121,
            29,
            48,
            92,
            117,
            6,
            238,
            183,
            225,
            250,
            65,
            14,
            118,
            26,
            59,
            98,
            44,
            225,
            20,
        ]
    )

    wire_transaction = {
        "amt": 1000,
        "fv": 1000,
        "lv": 2000,
        "rcv": address_bytes,
        "snd": address_bytes,
        "type": "xyz",  # An unknown transaction type
    }

    encoded = msgpack.packb(wire_transaction)
    decoded = decode_transaction(encoded)

    assert decoded.transaction_type == TransactionType.Unknown
    assert decoded.first_valid == 1000
    assert decoded.last_valid == 2000
    assert decoded.sender == "424ZV7KBBUJ52DUKP2KLQ6I5GBOHKBXOW7Q7UQIOOYNDWYRM4EKOSMVVRI"
    # Type-specific fields should be None for unknown transaction types
    assert decoded.payment is None
    assert decoded.asset_transfer is None
    assert decoded.asset_config is None
    assert decoded.application_call is None
    assert decoded.key_registration is None
    assert decoded.asset_freeze is None
    assert decoded.heartbeat is None
    assert decoded.state_proof is None


@pytest.mark.group_generic_transaction_tests
def test_encode_0_bytes() -> None:
    """Ensure a helpful error message is thrown when attempting to encode 0 bytes"""
    with pytest.raises(ValueError, match="^attempted to decode 0 bytes$"):
        decode_transaction(b"")


def _sample_app_call_tx() -> Transaction:
    return Transaction(
        transaction_type=TransactionType.AppCall,
        sender="XBYLS2E6YI6XXL5BWCAMOA4GTWHXWENZMX5UHXMRNWWUQ7BXCY5WC5TEPA",
        first_valid=1,
        last_valid=2,
        application_call=AppCallTransactionFields(approval_program=b"\x01", clear_state_program=b"\x02"),
    )


def test_calculate_fee_matches_assign_fee() -> None:
    tx = _sample_app_call_tx()
    fee = calculate_fee(tx, fee_per_byte=10, min_fee=1000)
    assigned = assign_fee(tx, fee_per_byte=10, min_fee=1000)
    assert assigned.fee == fee
