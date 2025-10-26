from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from algokit_transact import TransactionValidationError, validate_transaction

from tests._helpers import iter_asset_transfer_vectors
from tests._validation import build_asset_transfer, clone_transaction
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


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_vectors()))
def test_example(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_example(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_vectors()))
def test_multisig_example(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_multisig_example(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_vectors()))
def test_get_transaction_id(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_transaction_id(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_vectors()))
def test_assign_fee(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_assign_fee(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_vectors()))
def test_get_encoded_transaction_type(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encoded_transaction_type(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_vectors()))
def test_decode_without_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_decode_without_prefix(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_vectors()))
def test_decode_with_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_decode_with_prefix(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_vectors()))
def test_encode_with_auth_address(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode_with_auth_address(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_vectors()))
def test_encode_with_signature(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode_with_signature(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_vectors()))
def test_encode(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode(label, vector_lookup(key))


def test_should_throw_error_when_asset_id_is_zero(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("optInAssetTransfer")
    tx = clone_transaction(
        vector.transaction,
        asset_transfer=build_asset_transfer(
            asset_id=0,
            amount=1000,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    assert "Asset transfer validation failed: Asset ID must not be 0" in str(exc.value)


def test_should_validate_valid_asset_transfer_transaction(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("optInAssetTransfer")
    tx = clone_transaction(
        vector.transaction,
        asset_transfer=build_asset_transfer(
            asset_id=123,
            amount=1000,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_opt_in_transaction(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("optInAssetTransfer")
    sender = vector.transaction.sender
    tx = clone_transaction(
        vector.transaction,
        asset_transfer=build_asset_transfer(
            asset_id=123,
            amount=0,
            receiver=sender,
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_transfer_with_clawback(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("optInAssetTransfer")
    tx = clone_transaction(
        vector.transaction,
        asset_transfer=build_asset_transfer(
            asset_id=123,
            amount=1000,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            asset_sender="BNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_opt_out_transaction(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("optInAssetTransfer")
    tx = clone_transaction(
        vector.transaction,
        asset_transfer=build_asset_transfer(
            asset_id=123,
            amount=1000,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            close_remainder_to="BNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_transfer_with_clawback_and_close_remainder(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("optInAssetTransfer")
    tx = clone_transaction(
        vector.transaction,
        asset_transfer=build_asset_transfer(
            asset_id=123,
            amount=1000,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            asset_sender="CNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            close_remainder_to="BNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_transfer_to_self(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("optInAssetTransfer")
    sender = vector.transaction.sender
    tx = clone_transaction(
        vector.transaction,
        asset_transfer=build_asset_transfer(
            asset_id=123,
            amount=1000,
            receiver=sender,
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_close_out_transaction(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("optInAssetTransfer")
    tx = clone_transaction(
        vector.transaction,
        asset_transfer=build_asset_transfer(
            asset_id=123,
            amount=0,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            close_remainder_to="BNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)
