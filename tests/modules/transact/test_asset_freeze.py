from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from algokit_transact import TransactionValidationError, validate_transaction

from ._helpers import iter_asset_freeze_vectors
from ._validation import build_asset_freeze, clone_transaction
from .transaction_asserts import (
    assert_assign_fee,
    assert_decode_with_prefix,
    assert_decode_without_prefix,
    assert_encode,
    assert_encode_with_auth_address,
    assert_encode_with_signature,
    assert_encoded_transaction_type,
    assert_example,
    assert_transaction_id,
)

if TYPE_CHECKING:
    from .conftest import VectorLookup


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_vectors()))
def test_example(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_example(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_vectors()))
def test_get_transaction_id(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_transaction_id(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_vectors()))
def test_assign_fee(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_assign_fee(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_vectors()))
def test_get_encoded_transaction_type(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encoded_transaction_type(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_vectors()))
def test_decode_without_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_decode_without_prefix(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_vectors()))
def test_decode_with_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_decode_with_prefix(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_vectors()))
def test_encode_with_auth_address(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode_with_auth_address(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_vectors()))
def test_encode_with_signature(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode_with_signature(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_vectors()))
def test_encode(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode(label, vector_lookup(key))


def test_should_throw_error_when_asset_id_is_zero(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("assetFreeze")
    tx = clone_transaction(
        vector.transaction,
        asset_freeze=build_asset_freeze(
            asset_id=0,
            freeze_target="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            frozen=True,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    assert "Asset freeze validation failed: Asset ID must not be 0" in str(exc.value)


def test_should_validate_valid_asset_freeze_transaction(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("assetFreeze")
    tx = clone_transaction(
        vector.transaction,
        asset_freeze=build_asset_freeze(
            asset_id=123,
            freeze_target="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            frozen=True,
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_unfreeze_transaction(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("assetUnfreeze")
    tx = clone_transaction(
        vector.transaction,
        asset_freeze=build_asset_freeze(
            asset_id=123,
            freeze_target="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            frozen=False,
        ),
    )

    validate_transaction(tx)


def test_should_validate_freezing_sender_themselves(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("assetFreeze")
    sender = vector.transaction.sender
    tx = clone_transaction(
        vector.transaction,
        asset_freeze=build_asset_freeze(
            asset_id=123,
            freeze_target=sender,
            frozen=True,
        ),
    )

    validate_transaction(tx)


def test_should_validate_unfreezing_sender_themselves(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("assetUnfreeze")
    sender = vector.transaction.sender
    tx = clone_transaction(
        vector.transaction,
        asset_freeze=build_asset_freeze(
            asset_id=123,
            freeze_target=sender,
            frozen=False,
        ),
    )

    validate_transaction(tx)
