from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests._helpers import iter_state_proof_vectors
from tests.transaction_asserts import (
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
    from tests.conftest import VectorLookup


@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_example(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_example(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_multisig_example(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_multisig_example(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_get_transaction_id(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_transaction_id(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_assign_fee(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_assign_fee(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_get_encoded_transaction_type(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encoded_transaction_type(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_decode_without_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_decode_without_prefix(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_decode_with_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_decode_with_prefix(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_encode_with_auth_address(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode_with_auth_address(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_encode_with_signature(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode_with_signature(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), iter_state_proof_vectors())
def test_encode(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode(label, vector_lookup(key))
