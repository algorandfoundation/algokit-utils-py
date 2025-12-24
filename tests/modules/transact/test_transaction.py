import msgpack
import pytest

from algokit_common import MAX_TRANSACTION_GROUP_SIZE
from algokit_transact import (
    AppCallTransactionFields,
    Transaction,
    TransactionType,
    assign_fee,
    calculate_fee,
    decode_transaction,
    group_transactions,
)

from .common import TransactionTestData
from .conftest import TestDataLookup


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


def _simple_group_test_data(test_data_lookup: TestDataLookup) -> list[TransactionTestData]:
    payment = test_data_lookup("simplePayment")
    opt_in = test_data_lookup("optInAssetTransfer")
    return [payment, opt_in]


def test_group_transactions_max_size(test_data_lookup: TestDataLookup) -> None:
    vectors = _simple_group_test_data(test_data_lookup)
    base = vectors[0].transaction
    # Create MAX_TRANSACTION_GROUP_SIZE + 1 copies (with different first_valid to avoid identical txs)
    over_limit = [
        base.__class__(
            transaction_type=TransactionType.Payment,
            sender=base.sender,
            first_valid=base.first_valid + i,
            last_valid=base.last_valid + i,
            payment=base.payment,
        )
        for i in range(MAX_TRANSACTION_GROUP_SIZE + 1)
    ]

    with pytest.raises(ValueError, match=rf"max limit of {MAX_TRANSACTION_GROUP_SIZE}"):
        group_transactions(over_limit)
