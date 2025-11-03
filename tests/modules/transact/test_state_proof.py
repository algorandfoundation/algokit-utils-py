import pytest

from ._helpers import iter_state_proof_vectors
from .conftest import VectorLookup
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

# Polytest Suite: State Proof

# Polytest Group: Transaction Tests


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_example(label: str, key: str, vector_lookup: VectorLookup) -> None:
    """A human-readable example of forming a transaction and signing it"""
    assert_example(label, vector_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_multisig_example(label: str, key: str, vector_lookup: VectorLookup) -> None:
    """A human-readable example of forming a transaction and signing it with a multisignature sig"""
    assert_multisig_example(label, vector_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_get_transaction_id(label: str, key: str, vector_lookup: VectorLookup) -> None:
    """A transaction id can be obtained from a transaction"""
    assert_transaction_id(label, vector_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_assign_fee(label: str, key: str, vector_lookup: VectorLookup) -> None:
    """A fee can be calculated and assigned to a transaction"""
    assert_assign_fee(label, vector_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_get_encoded_transaction_type(label: str, key: str, vector_lookup: VectorLookup) -> None:
    """The transaction type of an encoded transaction can be retrieved"""
    assert_encoded_transaction_type(label, vector_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_decode_without_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    """A transaction without TX prefix and valid fields is decoded properly"""
    assert_decode_without_prefix(label, vector_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_decode_with_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    """A transaction with TX prefix and valid fields is decoded properly"""
    assert_decode_with_prefix(label, vector_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_encode_with_auth_address(label: str, key: str, vector_lookup: VectorLookup) -> None:
    """An auth address can be attached to a encoded transaction with a signature"""
    assert_encode_with_auth_address(label, vector_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_encode_with_signature(label: str, key: str, vector_lookup: VectorLookup) -> None:
    """A signature can be attached to a encoded transaction"""
    assert_encode_with_signature(label, vector_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_encode(label: str, key: str, vector_lookup: VectorLookup) -> None:
    """A transaction with valid fields is encoded properly"""
    assert_encode(label, vector_lookup(key))
