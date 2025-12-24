import pytest

from algokit_transact import TransactionValidationError, validate_transaction
from tests.modules.transact._validation import build_asset_freeze, clone_transaction
from tests.modules.transact.conftest import TestDataLookup


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
