import pytest


from .conftest import TestDataLookup
from .transaction_asserts import (
    assert_assign_fee,
    assert_decode_with_prefix,
    assert_decode_without_prefix,
    assert_encode,
    assert_encode_with_signature,
    assert_encoded_transaction_type,
    assert_example,
    assert_transaction_id,
)

# Polytest Suite: Payment

# Polytest Group: Transaction Tests


@pytest.mark.group_transaction_tests
def test_example(test_data_lookup: TestDataLookup) -> None:
    """A human-readable example of forming a transaction and signing it"""
    vector = test_data_lookup("simplePayment")
    assert_example("payment", vector)


@pytest.mark.group_transaction_tests
def test_get_transaction_id(test_data_lookup: TestDataLookup) -> None:
    """A transaction id can be obtained from a transaction"""
    vector = test_data_lookup("simplePayment")
    assert_transaction_id("payment", vector)


@pytest.mark.group_transaction_tests
def test_assign_fee(test_data_lookup: TestDataLookup) -> None:
    """A fee can be calculated and assigned to a transaction"""
    vector = test_data_lookup("simplePayment")
    assert_assign_fee("payment", vector)


@pytest.mark.group_transaction_tests
def test_get_encoded_transaction_type(test_data_lookup: TestDataLookup) -> None:
    """The transaction type of an encoded transaction can be retrieved"""
    vector = test_data_lookup("simplePayment")
    assert_encoded_transaction_type("payment", vector)


@pytest.mark.group_transaction_tests
def test_decode_without_prefix(test_data_lookup: TestDataLookup) -> None:
    """A transaction without TX prefix and valid fields is decoded properly"""
    vector = test_data_lookup("simplePayment")
    assert_decode_without_prefix("payment", vector)


@pytest.mark.group_transaction_tests
def test_decode_with_prefix(test_data_lookup: TestDataLookup) -> None:
    """A transaction with TX prefix and valid fields is decoded properly"""
    vector = test_data_lookup("simplePayment")
    assert_decode_with_prefix("payment", vector)


@pytest.mark.group_transaction_tests
def test_encode_with_signature(test_data_lookup: TestDataLookup) -> None:
    """A signature can be attached to a encoded transaction"""
    vector = test_data_lookup("simplePayment")
    assert_encode_with_signature("payment", vector)


@pytest.mark.group_transaction_tests
def test_encode(test_data_lookup: TestDataLookup) -> None:
    """A transaction with valid fields is encoded properly"""
    vector = test_data_lookup("simplePayment")
    assert_encode("payment", vector)
