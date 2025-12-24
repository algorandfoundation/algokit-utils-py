import pytest

from ._helpers import iter_state_proof_test_data
from .conftest import TestDataLookup
from .transaction_asserts import (
    assert_assign_fee,
    assert_decode_with_prefix,
    assert_decode_without_prefix,
    assert_encode,
    assert_encode_with_signature,
    assert_encoded_transaction_type,
    assert_example,
    assert_multisig_example,
    assert_transaction_id,
)

# Polytest Suite: State Proof

# Polytest Group: Transaction Tests


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_test_data())
def test_example(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A human-readable example of forming a transaction and signing it"""
    assert_example(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_test_data())
def test_multisig_example(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A human-readable example of forming a transaction and signing it with a multisignature sig"""
    assert_multisig_example(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_test_data())
def test_get_transaction_id(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A transaction id can be obtained from a transaction"""
    assert_transaction_id(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_test_data())
def test_assign_fee(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A fee can be calculated and assigned to a transaction"""
    assert_assign_fee(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_test_data())
def test_get_encoded_transaction_type(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """The transaction type of an encoded transaction can be retrieved"""
    assert_encoded_transaction_type(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_test_data())
def test_decode_without_prefix(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A transaction without TX prefix and valid fields is decoded properly"""
    assert_decode_without_prefix(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_test_data())
def test_decode_with_prefix(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A transaction with TX prefix and valid fields is decoded properly"""
    assert_decode_with_prefix(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_test_data())
def test_encode_with_signature(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A signature can be attached to a encoded transaction"""
    assert_encode_with_signature(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_test_data())
def test_encode(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A transaction with valid fields is encoded properly"""
    assert_encode(label, test_data_lookup(key))
