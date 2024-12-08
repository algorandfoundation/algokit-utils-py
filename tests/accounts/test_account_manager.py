import algosdk
import pytest

from algokit_utils import Account
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.models.amount import AlgoAmount
from tests.conftest import get_unique_name


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_local_net()


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> Account:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account, dispenser, AlgoAmount.from_algos(100), min_funding_increment=AlgoAmount.from_algos(1)
    )
    algorand.set_signer(sender=new_account.address, signer=new_account.signer)
    return new_account


def test_new_account_is_retrieved_and_funded(algorand: AlgorandClient) -> None:
    # Act
    account_name = get_unique_name()
    account = algorand.account.from_environment(account_name)

    # Assert
    account_info = algorand.account.get_information(account.address)
    assert account_info["amount"] > 0


def test_same_account_is_subsequently_retrieved(algorand: AlgorandClient) -> None:
    # Arrange
    account_name = get_unique_name()

    # Act
    account1 = algorand.account.from_environment(account_name)
    account2 = algorand.account.from_environment(account_name)

    # Assert - accounts should be different objects but with same underlying keys
    assert account1 is not account2
    assert account1.address == account2.address
    assert account1.private_key == account2.private_key


def test_environment_is_used_in_preference_to_kmd(algorand: AlgorandClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    account_name = get_unique_name()
    account1 = algorand.account.from_environment(account_name)

    # Set up environment variable for second account
    env_account_name = "TEST_ACCOUNT"
    monkeypatch.setenv(f"{env_account_name}_MNEMONIC", algosdk.mnemonic.from_private_key(account1.private_key))

    # Act
    account2 = algorand.account.from_environment(env_account_name)

    # Assert - accounts should be different objects but with same underlying keys
    assert account1 is not account2
    assert account1.address == account2.address
    assert account1.private_key == account2.private_key


def test_random_account_creation(algorand: AlgorandClient) -> None:
    # Act
    account = algorand.account.random()

    # Assert
    assert account.address
    assert account.private_key
    assert len(account.public_key) == 32


def test_ensure_funded_from_environment(algorand: AlgorandClient) -> None:
    # Arrange
    account = algorand.account.random()
    min_balance = AlgoAmount.from_algos(1)

    # Act
    result = algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=min_balance,
    )

    # Assert
    assert result is not None
    assert result.amount_funded is not None
    account_info = algorand.account.get_information(account.address)
    assert account_info["amount"] >= min_balance.micro_algos


def test_get_account_information(algorand: AlgorandClient) -> None:
    # Arrange
    account = algorand.account.random()

    # Act
    info = algorand.account.get_information(account.address)

    # Assert
    assert isinstance(info, dict)
    assert "amount" in info
    assert "min-balance" in info
    assert "address" in info
    assert info["address"] == account.address
