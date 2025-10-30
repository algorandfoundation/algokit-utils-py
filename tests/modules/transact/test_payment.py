from __future__ import annotations

from typing import TYPE_CHECKING

from algokit_transact import PaymentTransactionFields, validate_transaction

from ._validation import clone_transaction
from .transaction_asserts import (
    assert_assign_fee,
    assert_decode_with_prefix,
    assert_decode_without_prefix,
    assert_encode,
    assert_encode_with_auth_address,
    assert_encode_with_signature,
    assert_encoded_transaction_type,
    assert_example,
    assert_multisig_example,
    assert_transaction_id,
)

if TYPE_CHECKING:
    from .conftest import VectorLookup


def test_example(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    assert_example("payment", vector)


def test_multisig_example(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    assert_multisig_example("payment", vector)


def test_get_transaction_id(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    assert_transaction_id("payment", vector)


def test_assign_fee(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    assert_assign_fee("payment", vector)


def test_get_encoded_transaction_type(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    assert_encoded_transaction_type("payment", vector)


def test_decode_without_prefix(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    assert_decode_without_prefix("payment", vector)


def test_decode_with_prefix(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    assert_decode_with_prefix("payment", vector)


def test_encode_with_auth_address(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    assert_encode_with_auth_address("payment", vector)


def test_encode_with_signature(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    assert_encode_with_signature("payment", vector)


def test_encode(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    assert_encode("payment", vector)


def test_should_validate_valid_payment_transaction(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    tx = clone_transaction(
        vector.transaction,
        payment=PaymentTransactionFields(
            amount=1000,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_payment_transaction_with_zero_amount(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    tx = clone_transaction(
        vector.transaction,
        payment=PaymentTransactionFields(
            amount=0,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_payment_transaction_with_close_remainder(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    tx = clone_transaction(
        vector.transaction,
        payment=PaymentTransactionFields(
            amount=1000,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            close_remainder_to="BNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_self_payment_transaction(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("simplePayment")
    sender = vector.transaction.sender
    tx = clone_transaction(
        vector.transaction,
        payment=PaymentTransactionFields(
            amount=1000,
            receiver=sender,
        ),
    )

    validate_transaction(tx)
