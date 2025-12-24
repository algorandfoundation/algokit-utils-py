import pytest

from algokit_transact import TransactionValidationError, validate_transaction
from tests.modules.transact._validation import build_asset_transfer, clone_transaction
from tests.modules.transact.conftest import TestDataLookup


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
