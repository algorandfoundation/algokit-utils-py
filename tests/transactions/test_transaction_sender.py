from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import algosdk
import pytest
from algosdk.transaction import (
    ApplicationCreateTxn,
    AssetConfigTxn,
    AssetCreateTxn,
    AssetDestroyTxn,
    AssetFreezeTxn,
    AssetTransferTxn,
    PaymentTxn,
)

from algokit_utils import (
    Account,
    get_account,
)
from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.assets.asset_manager import AssetManager
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCall,
    AppCallParams,
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
from tests.conftest import get_unique_name


@pytest.fixture
def algorand(funded_account: Account) -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_signer(sender=funded_account.address, signer=funded_account.signer)
    return client


@pytest.fixture
def sender(funded_account: Account) -> Account:
    return funded_account


@pytest.fixture
def receiver(algod_client: "algosdk.v2client.algod.AlgodClient") -> Account:
    return get_account(algod_client, get_unique_name())


@pytest.fixture
def raw_hello_world_arc32_app_spec() -> str:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "hello_world" / "arc32_app_spec.json"
    return raw_json_spec.read_text()


@pytest.fixture
def test_hello_world_arc32_app_spec() -> ApplicationSpecification:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "hello_world" / "arc32_app_spec.json"
    return ApplicationSpecification.from_json(raw_json_spec.read_text())


@pytest.fixture
def test_hello_world_arc32_app_id(
    algorand: AlgorandClient, funded_account: Account, test_hello_world_arc32_app_spec: ApplicationSpecification
) -> int:
    global_schema = test_hello_world_arc32_app_spec.global_state_schema
    local_schema = test_hello_world_arc32_app_spec.local_state_schema
    response = algorand.send.app_create(
        AppCreateParams(
            sender=funded_account.address,
            approval_program=test_hello_world_arc32_app_spec.approval_program,
            clear_state_program=test_hello_world_arc32_app_spec.clear_program,
            schema={
                "global_ints": global_schema.num_uints,
                "global_bytes": global_schema.num_byte_slices,
                "local_ints": local_schema.num_uints,
                "local_bytes": local_schema.num_byte_slices,
            },  # type: ignore[arg-type]
        )
    )
    return response.app_id


@pytest.fixture
def transaction_sender(
    algod_client: "algosdk.v2client.algod.AlgodClient", sender: Account
) -> AlgorandClientTransactionSender:
    def new_group() -> TransactionComposer:
        return TransactionComposer(
            algod=algod_client,
            get_signer=lambda _: sender.signer,
        )

    return AlgorandClientTransactionSender(
        new_group=new_group,
        asset_manager=AssetManager(algod_client, new_group),
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
    assert result.confirmations[-1]["confirmed-round"] > 0  # type: ignore[call-overload]
    txn = cast(PaymentTxn, result.transaction)
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
    assert result.confirmations[-1]["confirmed-round"] > 0  # type: ignore[call-overload]
    txn = cast(AssetCreateTxn, result.transaction)
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
            url="https://example.com",
            manager=sender.address,
        )
    )
    asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]

    # Then configure it
    config_params = AssetConfigParams(
        sender=sender.address,
        asset_id=asset_id,
        manager=receiver.address,
    )
    result = transaction_sender.asset_config(config_params)

    assert len(result.tx_ids) == 1
    assert isinstance(result.transaction, AssetConfigTxn)
    assert result.transaction.sender == sender.address
    assert result.transaction.index == asset_id
    assert result.transaction.manager == receiver.address


def test_asset_freeze(
    transaction_sender: AlgorandClientTransactionSender,
    sender: Account,
) -> None:
    # First create an asset
    create_result = transaction_sender.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=1000,
            decimals=0,
            default_frozen=False,
            unit_name="FRZ",
            url="https://example.com",
            asset_name="Freeze Asset",
            freeze=sender.address,
            manager=sender.address,
        )
    )
    asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]

    # Then freeze it
    freeze_params = AssetFreezeParams(
        sender=sender.address,
        asset_id=asset_id,
        account=sender.address,
        frozen=True,
    )
    result = transaction_sender.asset_freeze(freeze_params)

    assert len(result.tx_ids) == 1
    txn = cast(AssetFreezeTxn, result.transaction)
    assert txn.sender == sender.address
    assert txn.index == asset_id
    assert txn.target == sender.address
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
            url="https://example.com",
        )
    )
    asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]

    # Then destroy it
    destroy_params = AssetDestroyParams(
        sender=sender.address,
        asset_id=asset_id,
    )
    result = transaction_sender.asset_destroy(destroy_params)

    assert len(result.tx_ids) == 1
    txn = cast(AssetDestroyTxn, result.transaction)
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
            url="https://example.com",
            unit_name="XFR",
            asset_name="Transfer Asset",
        )
    )
    asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]

    # Then opt-in receiver
    transaction_sender.asset_opt_in(
        AssetOptInParams(
            sender=receiver.address,
            asset_id=asset_id,
            signer=receiver.signer,
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
    txn = cast(AssetTransferTxn, result.transaction)
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
            url="https://example.com",
            unit_name="OPT",
            asset_name="Opt Asset",
        )
    )
    asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]

    # Then opt-in
    opt_in_params = AssetOptInParams(
        sender=receiver.address,
        asset_id=asset_id,
        signer=receiver.signer,
    )
    result = transaction_sender.asset_opt_in(opt_in_params)

    assert len(result.tx_ids) == 1
    txn = cast(AssetTransferTxn, result.transaction)
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
            url="https://example.com",
            unit_name="OUT",
            asset_name="Opt Out Asset",
        )
    )
    asset_id = int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]

    # Then opt-in
    transaction_sender.asset_opt_in(
        AssetOptInParams(
            sender=receiver.address,
            asset_id=asset_id,
            signer=receiver.signer,
        )
    )

    # Then opt-out
    opt_out_params = AssetOptOutParams(
        sender=receiver.address,
        asset_id=asset_id,
        creator=sender.address,
        signer=receiver.signer,
    )
    result = transaction_sender.asset_opt_out(params=opt_out_params)

    txn = cast(AssetTransferTxn, result.transaction)
    assert txn.sender == receiver.address
    assert txn.index == asset_id
    assert txn.amount == 0
    assert txn.receiver == receiver.address
    assert txn.close_assets_to == sender.address


# TODO: add remaining tests for app_update, app_delete, app_create_method_call, app_update method call, app_delete method call


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


def test_app_call(
    test_hello_world_arc32_app_id: int, transaction_sender: AlgorandClientTransactionSender, sender: Account
) -> None:
    params = AppCallParams(
        app_id=test_hello_world_arc32_app_id,
        sender=sender.address,
        args=[b"\x02\xbe\xce\x11", b"test"],
    )

    result = transaction_sender.app_call(params)
    assert not result.return_value  # TODO: improve checks


def test_app_call_method_call(
    test_hello_world_arc32_app_id: int, transaction_sender: AlgorandClientTransactionSender, sender: Account
) -> None:
    params = AppCallMethodCall(
        app_id=test_hello_world_arc32_app_id,
        sender=sender.address,
        method=algosdk.abi.Method.from_signature("hello(string)string"),
        args=["test"],
    )

    result = transaction_sender.app_call_method_call(params)
    assert result.return_value == "Hello2, test"


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
    assert "Sending 1,000,000 µALGO" in log_message
    assert sender.address in log_message
    assert receiver.address in log_message


def test_online_key_registration(transaction_sender: AlgorandClientTransactionSender, sender: Account) -> None:
    sp = transaction_sender._algod.suggested_params()  # noqa: SLF001

    params = OnlineKeyRegistrationParams(
        sender=sender.address,
        vote_key="G/lqTV6MKspW6J8wH2d8ZliZ5XZVZsruqSBJMwLwlmo=",
        selection_key="LrpLhvzr+QpN/bivh6IPpOaKGbGzTTB5lJtVfixmmgk=",
        state_proof_key=b"RpUpNWfZMjZ1zOOjv3MF2tjO714jsBt0GKnNsw0ihJ4HSZwci+d9zvUi3i67LwFUJgjQ5Dz4zZgHgGduElnmSA==",
        vote_first=sp.first,
        vote_last=sp.first + int(10e6),
        vote_key_dilution=100,
    )

    result = transaction_sender.online_key_registration(params)
    assert len(result.tx_ids) == 1
    assert result.confirmations[-1]["confirmed-round"] > 0  # type: ignore[call-overload]
