from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import algosdk
import pytest
from algokit_utils import (
    Account,
    ApplicationClient,
    get_account,
)
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.assets.asset_manager import AssetManager
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCall,
    AppCreateParams,
    AssetConfigParams,
    AssetCreateParams,
    AssetDestroyParams,
    AssetFreezeParams,
    AssetOptInParams,
    AssetOptOutParams,
    AssetTransferParams,
    OnlineKeyRegistrationParams,
    PaymentParams,
    TransactionComposer,
)
from algokit_utils.transactions.transaction_sender import AlgorandClientTransactionSender
from algosdk.transaction import (
    ApplicationCallTxn,
    ApplicationCreateTxn,
    AssetConfigTxn,
    AssetCreateTxn,
    AssetDestroyTxn,
    AssetFreezeTxn,
    AssetTransferTxn,
    PaymentTxn,
)

from tests.conftest import get_unique_name


@pytest.fixture()
def sender(funded_account: Account) -> Account:
    return funded_account


@pytest.fixture()
def receiver(algod_client: "algosdk.v2client.algod.AlgodClient") -> Account:
    return get_account(algod_client, get_unique_name())


@pytest.fixture()
def transaction_sender(
    algod_client: "algosdk.v2client.algod.AlgodClient", sender: Account
) -> AlgorandClientTransactionSender:
    composer = TransactionComposer(
        algod=algod_client,
        get_signer=lambda _: sender.signer,
    )
    return AlgorandClientTransactionSender(
        new_group=lambda: composer,
        asset_manager=AssetManager(),
        app_manager=AppManager(algod_client),
        algod_client=algod_client,
    )


def test_payment(transaction_sender: AlgorandClientTransactionSender, sender: Account, receiver: Account) -> None:
    amount = AlgoAmount.from_algos(1)
    result = transaction_sender.payment(
        PaymentParams(
            sender=sender.address,
            receiver=receiver.address,
            amount=amount,
        )
    )

    assert len(result.tx_ids) == 1
    assert result.confirmed_round > 0
    txn = cast(PaymentTxn, result.transactions[0].txn)
    assert txn.sender == sender.address
    assert txn.receiver == receiver.address
    assert txn.amt == amount.micro_algos


def test_asset_create(transaction_sender: AlgorandClientTransactionSender, sender: Account) -> None:
    total = 1000
    params = AssetCreateParams(
        sender=sender.address,
        total=total,
        decimals=0,
        default_frozen=False,
        unit_name="TEST",
        asset_name="Test Asset",
        url="https://example.com",
    )

    result = transaction_sender.asset_create(params)
    assert len(result.tx_ids) == 1
    assert result.confirmed_round > 0
    txn = cast(AssetCreateTxn, result.transactions[0].txn)
    assert txn.sender == sender.address
    assert txn.total == total
    assert txn.decimals == 0
    assert txn.default_frozen is False
    assert txn.unit_name == "TEST"
    assert txn.asset_name == "Test Asset"
    assert txn.url == "https://example.com"


def test_asset_config(transaction_sender: AlgorandClientTransactionSender, sender: Account, receiver: Account) -> None:
    # First create an asset
    create_result = transaction_sender.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=1000,
            decimals=0,
            default_frozen=False,
            unit_name="CFG",
            asset_name="Config Asset",
            manager=sender.address,
        )
    )
    asset_id = int(create_result.confirmed_transactions[0]["asset-index"])

    # Then configure it
    config_params = AssetConfigParams(
        sender=sender.address,
        asset_id=asset_id,
        manager=receiver.address,
    )
    result = transaction_sender.asset_config(config_params)

    assert len(result.tx_ids) == 1
    txn = cast(AssetConfigTxn, result.transactions[0].txn)
    assert txn.sender == sender.address
    assert txn.index == asset_id
    assert txn.manager == receiver.address


def test_asset_freeze(transaction_sender: AlgorandClientTransactionSender, sender: Account, receiver: Account) -> None:
    # First create an asset
    create_result = transaction_sender.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=1000,
            decimals=0,
            default_frozen=False,
            unit_name="FRZ",
            asset_name="Freeze Asset",
            freeze=sender.address,
        )
    )
    asset_id = int(create_result.confirmed_transactions[0]["asset-index"])

    # Then freeze it
    freeze_params = AssetFreezeParams(
        sender=sender.address,
        asset_id=asset_id,
        account=receiver.address,
        frozen=True,
    )
    result = transaction_sender.asset_freeze(freeze_params)

    assert len(result.tx_ids) == 1
    txn = cast(AssetFreezeTxn, result.transactions[0].txn)
    assert txn.sender == sender.address
    assert txn.index == asset_id
    assert txn.target == receiver.address
    assert txn.new_freeze_state is True


def test_asset_destroy(transaction_sender: AlgorandClientTransactionSender, sender: Account) -> None:
    # First create an asset
    create_result = transaction_sender.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=1000,
            decimals=0,
            default_frozen=False,
            unit_name="DEL",
            asset_name="Delete Asset",
            manager=sender.address,
        )
    )
    asset_id = int(create_result.confirmed_transactions[0]["asset-index"])

    # Then destroy it
    destroy_params = AssetDestroyParams(
        sender=sender.address,
        asset_id=asset_id,
    )
    result = transaction_sender.asset_destroy(destroy_params)

    assert len(result.tx_ids) == 1
    txn = cast(AssetDestroyTxn, result.transactions[0].txn)
    assert txn.sender == sender.address
    assert txn.index == asset_id


def test_asset_transfer(
    transaction_sender: AlgorandClientTransactionSender, sender: Account, receiver: Account
) -> None:
    # First create an asset
    create_result = transaction_sender.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=1000,
            decimals=0,
            default_frozen=False,
            unit_name="XFR",
            asset_name="Transfer Asset",
        )
    )
    asset_id = int(create_result.confirmed_transactions[0]["asset-index"])

    # Then opt-in receiver
    transaction_sender.asset_opt_in(
        AssetOptInParams(
            sender=receiver.address,
            asset_id=asset_id,
        )
    )

    # Then transfer it
    amount = 100
    transfer_params = AssetTransferParams(
        sender=sender.address,
        asset_id=asset_id,
        receiver=receiver.address,
        amount=amount,
    )
    result = transaction_sender.asset_transfer(transfer_params)

    assert len(result.tx_ids) == 1
    txn = cast(AssetTransferTxn, result.transactions[0].txn)
    assert txn.sender == sender.address
    assert txn.index == asset_id
    assert txn.receiver == receiver.address
    assert txn.amount == amount


def test_asset_opt_in(transaction_sender: AlgorandClientTransactionSender, sender: Account, receiver: Account) -> None:
    # First create an asset
    create_result = transaction_sender.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=1000,
            decimals=0,
            default_frozen=False,
            unit_name="OPT",
            asset_name="Opt Asset",
        )
    )
    asset_id = int(create_result.confirmed_transactions[0]["asset-index"])

    # Then opt-in
    opt_in_params = AssetOptInParams(
        sender=receiver.address,
        asset_id=asset_id,
    )
    result = transaction_sender.asset_opt_in(opt_in_params)

    assert len(result.tx_ids) == 1
    txn = cast(AssetTransferTxn, result.transactions[0].txn)
    assert txn.sender == receiver.address
    assert txn.index == asset_id
    assert txn.amount == 0
    assert txn.receiver == receiver.address


def test_asset_opt_out(transaction_sender: AlgorandClientTransactionSender, sender: Account, receiver: Account) -> None:
    # First create an asset
    create_result = transaction_sender.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=1000,
            decimals=0,
            default_frozen=False,
            unit_name="OUT",
            asset_name="Opt Out Asset",
        )
    )
    asset_id = int(create_result.confirmed_transactions[0]["asset-index"])

    # Then opt-in
    transaction_sender.asset_opt_in(
        AssetOptInParams(
            sender=receiver.address,
            asset_id=asset_id,
        )
    )

    # Then opt-out
    opt_out_params = AssetOptOutParams(
        sender=receiver.address,
        asset_id=asset_id,
        close_to=sender.address,
    )
    result = transaction_sender.asset_opt_out(opt_out_params)

    assert len(result.tx_ids) == 1
    txn = cast(AssetTransferTxn, result.transactions[0].txn)
    assert txn.sender == receiver.address
    assert txn.index == asset_id
    assert txn.amount == 0
    assert txn.receiver == receiver.address
    assert txn.close_assets_to == sender.address


def test_app_create(transaction_sender: AlgorandClientTransactionSender, sender: Account) -> None:
    approval_program = "#pragma version 6\nint 1"
    clear_state_program = "#pragma version 6\nint 1"
    params = AppCreateParams(
        sender=sender.address,
        approval_program=approval_program,
        clear_state_program=clear_state_program,
        schema={"global_ints": 0, "global_bytes": 0, "local_ints": 0, "local_bytes": 0},
    )

    result = transaction_sender.app_create(params)
    assert result.app_id > 0
    assert result.app_address
    txn = cast(ApplicationCreateTxn, result.transaction)
    assert txn.sender == sender.address
    assert txn.approval_program == b"\x06\x81\x01"
    assert txn.clear_program == b"\x06\x81\x01"


def test_app_call_method_call(transaction_sender: AlgorandClientTransactionSender, sender: Account) -> None:
    # First create app
    app_client = ApplicationClient(
        client=transaction_sender._algod,
        app_spec=Path(__file__).parent / "artifacts/hello_world/application.json",
        sender=sender.address,
        signer=sender.signer,
    )
    app_response = app_client.create()
    assert app_response.tx_id

    # Then call it
    method = algosdk.abi.Method.from_signature("hello(string)string")
    params = AppCallMethodCall(
        sender=sender.address,
        app_id=app_client.app_id,
        method=method,
        args=["world"],
    )
    result = transaction_sender.app_call_method_call(params)

    assert result.return_value == "Hello, world"
    txn = cast(ApplicationCallTxn, result.transaction)
    assert txn.sender == sender.address
    assert txn.index == app_client.app_id


def test_method_call_logging(transaction_sender: AlgorandClientTransactionSender, sender: Account) -> None:
    method = algosdk.abi.Method.from_signature("hello(string)string")
    args = ["test"]
    result = transaction_sender._get_method_call_for_log(method, args)
    assert result == "hello(['test'])"


@patch("logging.Logger.debug")
def test_payment_logging(
    mock_debug: MagicMock,
    transaction_sender: AlgorandClientTransactionSender,
    sender: Account,
    receiver: Account,
) -> None:
    amount = AlgoAmount.from_algos(1)
    transaction_sender.payment(
        PaymentParams(
            sender=sender.address,
            receiver=receiver.address,
            amount=amount,
        )
    )

    assert mock_debug.call_count == 1
    log_message = mock_debug.call_args[0][0]
    assert "Sending" in log_message
    assert str(amount.micro_algos) in log_message
    assert sender.address in log_message
    assert receiver.address in log_message


def test_online_key_registration(transaction_sender: AlgorandClientTransactionSender, sender: Account) -> None:
    params = OnlineKeyRegistrationParams(
        sender=sender.address,
        vote_key="vote_key",
        selection_key="selection_key",
        state_proof_key=b"state_proof_key",
        vote_first=1,
        vote_last=10,
        vote_key_dilution=100,
    )

    result = transaction_sender.online_key_registration(params)
    assert len(result.tx_ids) == 1
    assert result.confirmed_round > 0
