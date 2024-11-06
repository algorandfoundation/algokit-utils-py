import algosdk
import pytest
from algokit_utils import Account, get_account
from algokit_utils.assets.asset_manager import (
    AccountAssetInformation,
    AssetInformation,
    BulkAssetOptInOutResult,
)
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import (
    AssetCreateParams,
    PaymentParams,
)
from algosdk.atomic_transaction_composer import AccountTransactionSigner

from tests.conftest import get_unique_name


@pytest.fixture()
def sender(funded_account: Account) -> Account:
    return funded_account


@pytest.fixture()
def receiver(algod_client: algosdk.v2client.algod.AlgodClient) -> Account:
    return get_account(algod_client, get_unique_name())


@pytest.fixture()
def algorand(funded_account: Account) -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_signer(sender=funded_account.address, signer=funded_account.signer)
    return client


def test_get_by_id(algorand: AlgorandClient, sender: Account) -> None:
    # First create an asset
    total = 1000
    create_result = algorand.send.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=total,
            decimals=0,
            default_frozen=False,
            unit_name="TEST",
            asset_name="Test Asset",
            url="https://example.com",
        )
    )
    asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]

    # Then get its info
    asset_info = algorand.asset.get_by_id(asset_id)

    assert isinstance(asset_info, AssetInformation)
    assert asset_info.asset_id == asset_id
    assert asset_info.total == total
    assert asset_info.decimals == 0
    assert asset_info.default_frozen is False
    assert asset_info.unit_name == "TEST"
    assert asset_info.asset_name == "Test Asset"
    assert asset_info.url == "https://example.com"
    assert asset_info.creator == sender.address


def test_get_account_information_with_address(algorand: AlgorandClient, sender: Account) -> None:
    # First create an asset
    total = 1000
    create_result = algorand.send.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=total,
            decimals=0,
            default_frozen=False,
            unit_name="TEST",
            asset_name="Test Asset",
            url="https://example.com",
        )
    )
    asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]

    # Then get account info
    account_info = algorand.asset.get_account_information(sender.address, asset_id)

    assert isinstance(account_info, AccountAssetInformation)
    assert account_info.asset_id == asset_id
    assert account_info.balance == total
    assert account_info.frozen is False


def test_get_account_information_with_account(algorand: AlgorandClient, sender: Account) -> None:
    # First create an asset
    total = 1000
    create_result = algorand.send.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=total,
            decimals=0,
            default_frozen=False,
            unit_name="TEST",
            asset_name="Test Asset",
            url="https://example.com",
        )
    )
    asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]

    # Then get account info
    account_info = algorand.asset.get_account_information(sender, asset_id)

    assert isinstance(account_info, AccountAssetInformation)
    assert account_info.asset_id == asset_id
    assert account_info.balance == total
    assert account_info.frozen is False


def test_get_account_information_with_transaction_signer(algorand: AlgorandClient, sender: Account) -> None:
    # First create an asset
    total = 1000
    create_result = algorand.send.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=total,
            decimals=0,
            default_frozen=False,
            unit_name="TEST",
            asset_name="Test Asset",
            url="https://example.com",
        )
    )
    asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]

    # Then get account info using transaction signer
    signer = AccountTransactionSigner(sender.private_key)
    account_info = algorand.asset.get_account_information(signer, asset_id)

    assert isinstance(account_info, AccountAssetInformation)
    assert account_info.asset_id == asset_id
    assert account_info.balance == total
    assert account_info.frozen is False


def test_bulk_opt_in_with_address(algorand: AlgorandClient, sender: Account, receiver: Account) -> None:
    # First create some assets
    asset_ids = []
    for i in range(3):
        create_result = algorand.send.asset_create(
            AssetCreateParams(
                sender=sender.address,
                total=1000,
                decimals=0,
                default_frozen=False,
                unit_name=f"TST{i}",
                asset_name=f"Test Asset {i}",
                url="https://example.com",
                signer=sender.signer,
            )
        )
        asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]
        asset_ids.append(asset_id)

    # Fund receiver
    algorand.send.payment(
        PaymentParams(
            sender=sender.address,
            receiver=receiver.address,
            amount=AlgoAmount.from_algos(1),
        )
    )

    # Then bulk opt-in
    results = algorand.asset.bulk_opt_in(receiver.address, asset_ids, signer=receiver.signer)

    assert len(results) == len(asset_ids)
    for result in results:
        assert isinstance(result, BulkAssetOptInOutResult)
        assert result.asset_id in asset_ids
        assert result.transaction_id


def test_bulk_opt_out_not_opted_in_fails(algorand: AlgorandClient, sender: Account, receiver: Account) -> None:
    # First create an asset
    create_result = algorand.send.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=1000,
            decimals=0,
            default_frozen=False,
            unit_name="TEST",
            asset_name="Test Asset",
            url="https://example.com",
        )
    )
    asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]

    # Fund receiver but don't opt-in
    algorand.send.payment(
        PaymentParams(
            sender=sender.address,
            receiver=receiver.address,
            amount=AlgoAmount.from_algos(1),
        )
    )

    # Then attempt to opt-out
    with pytest.raises(ValueError, match="is not opted-in"):
        algorand.asset.bulk_opt_out(receiver.address, [asset_id])
