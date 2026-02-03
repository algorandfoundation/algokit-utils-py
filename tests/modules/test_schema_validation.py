"""Runtime schema validation tests for all API clients."""

import pytest
from pydantic import ValidationError

from algokit_algod_client.schemas import AccountSchema, NodeStatusResponseSchema
from algokit_indexer_client.schemas import AccountResponseSchema
from algokit_kmd_client.schemas import CreateWalletResponseSchema, WalletSchema


def test_algod_schemas_validate():
    """Algod schemas validate correct data and reject invalid data."""
    valid = {
        "address": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ",
        "amount": 1000000,
        "amount-without-pending-rewards": 1000000,
        "min-balance": 100000,
        "pending-rewards": 0,
        "rewards": 0,
        "round": 1000,
        "status": "Offline",
        "total-apps-opted-in": 0,
        "total-assets-opted-in": 0,
        "total-created-apps": 0,
        "total-created-assets": 0,
    }

    account = AccountSchema.model_validate(valid)
    assert account.address == valid["address"]
    assert account.amount == 1000000

    # Test type validation - amount should be an integer
    with pytest.raises(ValidationError):
        AccountSchema.model_validate({**valid, "amount": "not_int"})

    # Test uint64 bounds - amount cannot be negative
    with pytest.raises(ValidationError):
        AccountSchema.model_validate({**valid, "amount": -1})


def test_kmd_schemas_validate():
    """KMD schemas validate nested structures."""
    valid = {"wallet": {"id": "test-id", "name": "test-wallet"}}

    wallet = CreateWalletResponseSchema.model_validate(valid)
    assert wallet.wallet.name == "test-wallet"

    # Test type validation - wallet should be an object, not a string
    with pytest.raises(ValidationError):
        CreateWalletResponseSchema.model_validate({"wallet": "not_an_object"})


def test_indexer_schemas_validate():
    """Indexer schemas validate with enums from models."""
    valid = {
        "current-round": 1000,
        "account": {
            "address": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ",
            "amount": 1000000,
            "amount-without-pending-rewards": 1000000,
            "created-at-round": 0,
            "deleted": False,
            "min-balance": 100000,
            "pending-rewards": 0,
            "reward-base": 0,
            "rewards": 0,
            "round": 1000,
            "status": "Offline",
            "total-apps-opted-in": 0,
            "total-assets-opted-in": 0,
            "total-created-apps": 0,
            "total-created-assets": 0,
        },
    }

    response = AccountResponseSchema.model_validate(valid)
    assert response.current_round == 1000
    assert response.account.address == valid["account"]["address"]

    # Test type validation - current-round should be an integer
    with pytest.raises(ValidationError):
        AccountResponseSchema.model_validate({**valid, "current-round": "not_an_int"})


@pytest.mark.localnet
def test_algod_runtime_validation(algod_client: object) -> None:
    """Validate real algod API responses."""
    response = algod_client.status()  # type: ignore[attr-defined]
    validated = NodeStatusResponseSchema.model_validate(response)
    assert validated.last_round >= 0


class TestBasicValidation:
    """Test basic schema validation."""

    def test_valid_data(self) -> None:
        """Valid data should pass validation."""
        valid_data = {
            "address": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ",
            "amount": 1000000,
            "min-balance": 100000,
        }
        schema = AccountSchema.model_validate(valid_data)
        assert schema.address == valid_data["address"]
        assert schema.amount == 1000000

    def test_invalid_type(self) -> None:
        """Invalid type should fail validation."""
        with pytest.raises(ValidationError):
            AccountSchema.model_validate(
                {
                    "address": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ",
                    "amount": "not_a_number",
                    "min-balance": 100000,
                }
            )


class TestUint64Bounds:
    """Test uint64 field bounds validation."""

    def test_valid_uint64(self) -> None:
        """Values within uint64 range should pass."""
        data = {
            "address": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ",
            "amount": 1000000,
            "min-balance": 100000,
        }
        schema = AccountSchema.model_validate(data)
        assert schema.amount == 1000000
        assert schema.min_balance == 100000

    def test_max_uint64(self) -> None:
        """Maximum uint64 value should pass."""
        max_uint64 = 18446744073709551615
        data = {
            "address": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ",
            "amount": max_uint64,
            "min-balance": 0,
        }
        schema = AccountSchema.model_validate(data)
        assert schema.amount == max_uint64

    def test_negative_uint64(self) -> None:
        """Negative values should fail."""
        with pytest.raises(ValidationError) as exc_info:
            AccountSchema.model_validate(
                {
                    "address": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ",
                    "amount": -1,
                    "min-balance": 0,
                }
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_overflow_uint64(self) -> None:
        """Values exceeding uint64 max should fail."""
        with pytest.raises(ValidationError) as exc_info:
            AccountSchema.model_validate(
                {
                    "address": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ",
                    "amount": 18446744073709551616,  # max_uint64 + 1
                    "min-balance": 0,
                }
            )
        assert "less than or equal to" in str(exc_info.value)


class TestSchemaImports:
    """Test that schemas can be imported correctly."""

    def test_algod_schemas_import(self) -> None:
        """Algod schemas should be importable."""
        from algokit_algod_client.schemas import (
            ApplicationSchema,
            AssetSchema,
        )

        assert AccountSchema is not None
        assert AssetSchema is not None
        assert ApplicationSchema is not None

    def test_kmd_schemas_import(self) -> None:
        """KMD schemas should be importable."""
        from algokit_kmd_client.schemas import CreateWalletRequestSchema

        assert WalletSchema is not None
        assert CreateWalletRequestSchema is not None

    def test_indexer_schemas_import(self) -> None:
        """Indexer schemas should be importable."""
        from algokit_indexer_client.schemas import (
            AccountSchema as IndexerAccountSchema,
            BlockSchema,
            TransactionSchema,
        )

        assert IndexerAccountSchema is not None
        assert TransactionSchema is not None
        assert BlockSchema is not None
