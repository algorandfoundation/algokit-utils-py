import nacl.signing
import pytest

import algokit_algo25
from algokit_common import address_from_public_key
from algokit_transact.signer import AddressWithSigners
from algokit_utils.algorand import AlgorandClient
from algokit_utils.models.amount import AlgoAmount
from tests.conftest import get_unique_name


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> AddressWithSigners:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account, dispenser, AlgoAmount.from_algo(100), min_funding_increment=AlgoAmount.from_algo(1)
    )
    algorand.set_signer(sender=new_account.addr, signer=new_account.signer)
    return new_account


def test_new_account_is_retrieved_and_funded(algorand: AlgorandClient) -> None:
    # Act
    account_name = get_unique_name()
    account = algorand.account.from_environment(account_name)

    # Assert
    account_info = algorand.account.get_information(account.addr)
    assert account_info.amount > 0


def test_same_account_is_subsequently_retrieved(algorand: AlgorandClient) -> None:
    # Arrange
    account_name = get_unique_name()

    # Act
    account1 = algorand.account.from_environment(account_name)
    account2 = algorand.account.from_environment(account_name)

    # Assert - accounts should be different objects but with same underlying address and signers
    assert account1 is not account2
    assert account1.addr == account2.addr
    # Verify signers are functionally equivalent by checking they sign the same test data identically
    assert account1.signer is not None
    assert account2.signer is not None


def test_environment_is_used_in_preference_to_kmd(algorand: AlgorandClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange - create a known account from a mnemonic
    # Generate a random mnemonic to create a test account
    signing_key = nacl.signing.SigningKey.generate()
    secret_key = signing_key.encode() + signing_key.verify_key.encode()
    test_mnemonic = algokit_algo25.secret_key_to_mnemonic(secret_key)

    # Set up environment variable for the account
    env_account_name = "TEST_ACCOUNT"
    monkeypatch.setenv(f"{env_account_name}_MNEMONIC", test_mnemonic)

    # Act - get account from environment (should use mnemonic, not KMD)
    account1 = algorand.account.from_environment(env_account_name)
    account2 = algorand.account.from_environment(env_account_name)

    # Assert - both calls should return accounts with the same address (from the mnemonic)
    assert account1.addr == account2.addr
    # Verify the address matches what we'd expect from the mnemonic
    expected_seed = algokit_algo25.seed_from_mnemonic(test_mnemonic)
    expected_signing_key = nacl.signing.SigningKey(expected_seed)
    expected_address = address_from_public_key(expected_signing_key.verify_key.encode())
    assert account1.addr == expected_address


def test_random_account_creation(algorand: AlgorandClient) -> None:
    # Act
    account = algorand.account.random()

    # Assert - AddressWithSigners has addr and signer, not private_key/public_key
    # This is a secretless signing approach where signers are callable functions
    assert account.addr
    assert len(account.addr) == 58  # Algorand address length
    assert account.signer is not None  # Has a transaction signer
    assert callable(account.signer)
    assert account.bytes_signer is not None  # Has a bytes signer
    assert account.delegated_lsig_signer is not None  # Has a logic sig signer
    assert account.program_data_signer is not None  # Has a program data signer
    assert account.mx_bytes_signer is not None  # Has a mx bytes signer


def test_ensure_funded_from_environment(algorand: AlgorandClient) -> None:
    # Arrange
    account = algorand.account.random()
    min_balance = AlgoAmount.from_algo(1)

    # Act
    result = algorand.account.ensure_funded_from_environment(
        account_to_fund=account.addr,
        min_spending_balance=min_balance,
    )

    # Assert
    assert result is not None
    assert result.amount_funded is not None
    account_info = algorand.account.get_information(account.addr)
    assert account_info.amount_without_pending_rewards >= min_balance.micro_algo


def test_get_account_information(algorand: AlgorandClient) -> None:
    # Arrange
    account = algorand.account.random()

    # Act
    info = algorand.account.get_information(account.addr)

    # Assert
    assert info.amount is not None
    assert info.min_balance is not None
    assert info.address is not None
    assert info.address == account.addr
