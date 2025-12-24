import pytest

from algokit_transact import Transaction, TransactionValidationError, validate_transaction

from ._helpers import iter_asset_config_test_data
from ._validation import (
    assert_validation_error,
    build_asset_config,
    clone_transaction,
)
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

# Polytest Suite: AssetConfig

# Polytest Group: Transaction Tests


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), list(iter_asset_config_test_data()))
def test_example(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A human-readable example of forming a transaction and signing it"""
    assert_example(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), list(iter_asset_config_test_data()))
def test_multisig_example(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A human-readable example of forming a transaction and signing it with a multisignature sig"""
    assert_multisig_example(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), list(iter_asset_config_test_data()))
def test_get_transaction_id(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A transaction id can be obtained from a transaction"""
    assert_transaction_id(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), list(iter_asset_config_test_data()))
def test_assign_fee(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A fee can be calculated and assigned to a transaction"""
    assert_assign_fee(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), list(iter_asset_config_test_data()))
def test_get_encoded_transaction_type(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """The transaction type of an encoded transaction can be retrieved"""
    assert_encoded_transaction_type(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), list(iter_asset_config_test_data()))
def test_decode_without_prefix(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A transaction without TX prefix and valid fields is decoded properly"""
    assert_decode_without_prefix(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), list(iter_asset_config_test_data()))
def test_decode_with_prefix(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A transaction with TX prefix and valid fields is decoded properly"""
    assert_decode_with_prefix(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), list(iter_asset_config_test_data()))
def test_encode_with_signature(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A signature can be attached to a encoded transaction"""
    assert_encode_with_signature(label, test_data_lookup(key))


@pytest.mark.group_transaction_tests
@pytest.mark.parametrize(("label", "key"), list(iter_asset_config_test_data()))
def test_encode(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A transaction with valid fields is encoded properly"""
    assert_encode(label, test_data_lookup(key))


@pytest.fixture
def asset_create_transaction(test_data_lookup: TestDataLookup) -> Transaction:
    return test_data_lookup("assetCreate").transaction


@pytest.fixture
def asset_reconfig_transaction(test_data_lookup: TestDataLookup) -> Transaction:
    return test_data_lookup("assetConfig").transaction


@pytest.fixture
def asset_destroy_transaction(test_data_lookup: TestDataLookup) -> Transaction:
    return test_data_lookup("assetDestroy").transaction


def test_should_throw_error_when_total_is_missing_for_asset_creation(asset_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        asset_create_transaction,
        asset_config=build_asset_config(
            asset_id=0,
            decimals=2,
            asset_name="Test Asset",
            unit_name="TA",
        ),
    )

    assert_validation_error(tx, "Asset config validation failed: Total is required")


def test_should_throw_error_when_decimals_exceed_maximum(asset_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        asset_create_transaction,
        asset_config=build_asset_config(
            asset_id=0,
            total=1_000_000,
            decimals=20,
            asset_name="Test Asset",
            unit_name="TA",
        ),
    )

    assert_validation_error(
        tx,
        "Asset config validation failed: Decimals cannot exceed 19 decimal places, got 20",
    )


def test_should_throw_error_when_unit_name_is_too_long(asset_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        asset_create_transaction,
        asset_config=build_asset_config(
            asset_id=0,
            total=1_000_000,
            decimals=2,
            asset_name="Test Asset",
            unit_name="TOOLONGUNITNAME",
        ),
    )

    assert_validation_error(
        tx,
        "Asset config validation failed: Unit name cannot exceed 8 bytes, got 15",
    )


def test_should_throw_error_when_asset_name_is_too_long(asset_create_transaction: Transaction) -> None:
    long_name = "A" * 33
    tx = clone_transaction(
        asset_create_transaction,
        asset_config=build_asset_config(
            asset_id=0,
            total=1_000_000,
            decimals=2,
            asset_name=long_name,
            unit_name="TA",
        ),
    )

    assert_validation_error(
        tx,
        "Asset config validation failed: Asset name cannot exceed 32 bytes, got 33",
    )


def test_should_throw_error_when_url_is_too_long(asset_create_transaction: Transaction) -> None:
    long_url = "https://" + "a" * 90
    tx = clone_transaction(
        asset_create_transaction,
        asset_config=build_asset_config(
            asset_id=0,
            total=1_000_000,
            decimals=2,
            asset_name="Test Asset",
            unit_name="TA",
            url=long_url,
        ),
    )

    assert_validation_error(tx, "Asset config validation failed: Url cannot exceed 96 bytes")


def test_should_throw_multiple_errors_for_asset_creation(asset_create_transaction: Transaction) -> None:
    long_name = "A" * 33
    long_url = "https://" + "a" * 90
    tx = clone_transaction(
        asset_create_transaction,
        asset_config=build_asset_config(
            asset_id=0,
            decimals=20,
            asset_name=long_name,
            unit_name="TOOLONGUNITNAME",
            url=long_url,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    message = str(exc.value)
    assert "Asset config validation failed:" in message
    assert "Total is required" in message
    assert "Decimals cannot exceed 19 decimal places" in message
    assert "Asset name cannot exceed 32 bytes" in message
    assert "Unit name cannot exceed 8 bytes" in message
    assert "Url cannot exceed 96 bytes" in message


def test_should_validate_valid_asset_creation_transaction(asset_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        asset_create_transaction,
        asset_config=build_asset_config(
            asset_id=0,
            total=1_000_000,
            decimals=2,
            default_frozen=False,
            asset_name="Test Asset",
            unit_name="TA",
            url="https://example.com",
            metadata_hash=b"\x00" * 32,
            manager="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            reserve="BNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            freeze="CNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            clawback="DNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_creation_with_minimum_values(asset_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        asset_create_transaction,
        asset_config=build_asset_config(
            asset_id=0,
            total=1,
            decimals=0,
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_creation_with_maximum_values(asset_create_transaction: Transaction) -> None:
    max_name = "A" * 32
    max_unit = "MAXUNIT8"
    max_url = "https://" + "a" * 88
    tx = clone_transaction(
        asset_create_transaction,
        asset_config=build_asset_config(
            asset_id=0,
            total=18_446_744_073_709_551_615,
            decimals=19,
            asset_name=max_name,
            unit_name=max_unit,
            url=max_url,
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_creation_with_default_frozen_true(asset_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        asset_create_transaction,
        asset_config=build_asset_config(
            asset_id=0,
            total=1_000_000,
            decimals=2,
            default_frozen=True,
            freeze="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_throw_error_when_modifying_total(asset_reconfig_transaction: Transaction) -> None:
    tx = clone_transaction(
        asset_reconfig_transaction,
        asset_config=build_asset_config(asset_id=123, total=2_000_000),
    )

    assert_validation_error(tx, "Asset config validation failed: Total is immutable and cannot be changed")


def test_should_throw_error_when_modifying_decimals(asset_reconfig_transaction: Transaction) -> None:
    tx = clone_transaction(
        asset_reconfig_transaction,
        asset_config=build_asset_config(asset_id=123, decimals=3),
    )

    assert_validation_error(tx, "Asset config validation failed: Decimals is immutable and cannot be changed")


def test_should_throw_multiple_errors_when_modifying_immutable_fields(
    asset_reconfig_transaction: Transaction,
) -> None:
    tx = clone_transaction(
        asset_reconfig_transaction,
        asset_config=build_asset_config(
            asset_id=123,
            total=2_000_000,
            decimals=3,
            default_frozen=True,
            asset_name="New Name",
            unit_name="NEW",
            url="https://new.com",
            metadata_hash=b"\x00" * 32,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    message = str(exc.value)
    assert "Asset config validation failed:" in message
    assert "Total is immutable" in message
    assert "Decimals is immutable" in message
    assert "Default frozen is immutable" in message
    assert "Asset name is immutable" in message
    assert "Unit name is immutable" in message
    assert "Url is immutable" in message
    assert "Metadata hash is immutable" in message


def test_should_validate_valid_asset_reconfiguration(asset_reconfig_transaction: Transaction) -> None:
    tx = clone_transaction(
        asset_reconfig_transaction,
        asset_config=build_asset_config(
            asset_id=123,
            manager="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            reserve="BNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            freeze="CNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            clawback="DNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_destruction(asset_destroy_transaction: Transaction) -> None:
    validate_transaction(asset_destroy_transaction)


def test_should_validate_asset_reconfiguration_removing_special_addresses(
    asset_reconfig_transaction: Transaction,
) -> None:
    tx = clone_transaction(
        asset_reconfig_transaction,
        asset_config=build_asset_config(
            asset_id=123,
            manager="",
            reserve="",
            freeze="",
            clawback="",
        ),
    )

    validate_transaction(tx)


def test_should_validate_asset_reconfiguration_with_single_field_change(
    asset_reconfig_transaction: Transaction,
) -> None:
    tx = clone_transaction(
        asset_reconfig_transaction,
        asset_config=build_asset_config(
            asset_id=123,
            manager="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)
