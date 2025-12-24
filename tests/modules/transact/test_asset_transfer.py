import pytest

from algokit_transact import TransactionValidationError, validate_transaction

from ._helpers import iter_asset_transfer_test_data
from ._validation import build_asset_transfer, clone_transaction
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


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_test_data()))
def test_example(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_example(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_test_data()))
def test_multisig_example(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_multisig_example(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_test_data()))
def test_get_transaction_id(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_transaction_id(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_test_data()))
def test_assign_fee(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_assign_fee(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_test_data()))
def test_get_encoded_transaction_type(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_encoded_transaction_type(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_test_data()))
def test_decode_without_prefix(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_decode_without_prefix(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_test_data()))
def test_decode_with_prefix(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_decode_with_prefix(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_test_data()))
def test_encode_with_signature(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_encode_with_signature(label, test_data_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_asset_transfer_test_data()))
def test_encode(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    assert_encode(label, test_data_lookup(key))


def test_should_throw_error_when_asset_id_is_zero(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("optInAssetTransfer")
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


def test_should_validate_valid_asset_transfer_transaction(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("optInAssetTransfer")
    tx = clone_transaction(
        vector.transaction,
        asset_transfer=build_asset_transfer(
            asset_id=123,
            amount=1000,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_opt_in_transaction(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("optInAssetTransfer")
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


def test_should_validate_asset_transfer_with_clawback(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("optInAssetTransfer")
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


def test_should_validate_asset_opt_out_transaction(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("optInAssetTransfer")
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


def test_should_validate_asset_transfer_with_clawback_and_close_remainder(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("optInAssetTransfer")
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


def test_should_validate_asset_transfer_to_self(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("optInAssetTransfer")
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


def test_should_validate_asset_close_out_transaction(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("optInAssetTransfer")
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
