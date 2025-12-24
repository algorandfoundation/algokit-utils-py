import pytest

from algokit_transact import TransactionValidationError, validate_transaction

from ._helpers import iter_asset_freeze_test_data
from ._validation import build_asset_freeze, clone_transaction
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


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_test_data()))
def test_example(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_example(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_test_data()))
def test_get_transaction_id(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_transaction_id(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_test_data()))
def test_assign_fee(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_assign_fee(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_test_data()))
def test_get_encoded_transaction_type(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_encoded_transaction_type(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_test_data()))
def test_decode_without_prefix(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_decode_without_prefix(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_test_data()))
def test_decode_with_prefix(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_decode_with_prefix(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_test_data()))
def test_encode_with_signature(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_encode_with_signature(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_freeze_test_data()))
def test_encode(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_encode(label, test_data_lookup(key))


def test_should_throw_error_when_asset_id_is_zero(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("assetFreeze")
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


def test_should_validate_valid_asset_freeze_transaction(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("assetFreeze")
    tx = clone_transaction(
        vector.transaction,
        asset_freeze=build_asset_freeze(
            asset_id=123,
            freeze_target="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            frozen=True,
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_unfreeze_transaction(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("assetUnfreeze")
    tx = clone_transaction(
        vector.transaction,
        asset_freeze=build_asset_freeze(
            asset_id=123,
            freeze_target="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            frozen=False,
        ),
    )

    validate_transaction(tx)


def test_should_validate_freezing_sender_themselves(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("assetFreeze")
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


def test_should_validate_unfreezing_sender_themselves(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("assetUnfreeze")
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
