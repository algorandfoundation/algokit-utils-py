from pathlib import Path
from unittest.mock import MagicMock, patch

import algosdk
import pytest
from algosdk.transaction import OnComplete

from algokit_utils import _EXPERIMENTAL_DEPENDENCIES_INSTALLED, SigningAccount
from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.algorand import AlgorandClient
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.assets.asset_manager import AssetManager
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCallParams,
    AppCallParams,
    AppCreateParams,
    AssetConfigParams,
    AssetCreateParams,
    AssetDestroyParams,
    AssetFreezeParams,
    AssetOptInParams,
    AssetOptOutParams,
    AssetTransferParams,
    OfflineKeyRegistrationParams,
    OnlineKeyRegistrationParams,
    PaymentParams,
    TransactionComposer,
)
from algokit_utils.transactions.transaction_sender import AlgorandClientTransactionSender


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> SigningAccount:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account, dispenser, AlgoAmount.from_algo(100), min_funding_increment=AlgoAmount.from_algo(1)
    )
    algorand.set_signer(sender=new_account.address, signer=new_account.signer)
    return new_account


@pytest.fixture
def sender(funded_account: SigningAccount) -> SigningAccount:
    return funded_account


@pytest.fixture
def receiver(algorand: AlgorandClient) -> SigningAccount:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account, dispenser, AlgoAmount.from_algo(100), min_funding_increment=AlgoAmount.from_algo(1)
    )
    return new_account


@pytest.fixture
def raw_hello_world_arc32_app_spec() -> str:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "hello_world" / "app_spec.arc32.json"
    return raw_json_spec.read_text()


@pytest.fixture
def test_hello_world_arc32_app_spec() -> ApplicationSpecification:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "hello_world" / "app_spec.arc32.json"
    return ApplicationSpecification.from_json(raw_json_spec.read_text())


@pytest.fixture
def test_hello_world_arc32_app_id(
    algorand: AlgorandClient, funded_account: SigningAccount, test_hello_world_arc32_app_spec: ApplicationSpecification
) -> int:
    global_schema = test_hello_world_arc32_app_spec.global_state_schema
    local_schema = test_hello_world_arc32_app_spec.local_state_schema
    response = algorand.send.app_create(
        AppCreateParams(
            sender=funded_account.address,
            approval_program=test_hello_world_arc32_app_spec.approval_program,
            clear_state_program=test_hello_world_arc32_app_spec.clear_program,
            schema={
                "global_ints": int(global_schema.num_uints) if global_schema.num_uints else 0,
                "global_byte_slices": int(global_schema.num_byte_slices) if global_schema.num_byte_slices else 0,
                "local_ints": int(local_schema.num_uints) if local_schema.num_uints else 0,
                "local_byte_slices": int(local_schema.num_byte_slices) if local_schema.num_byte_slices else 0,
            },
        )
    )
    return response.app_id


@pytest.fixture
def transaction_sender(algorand: AlgorandClient, sender: SigningAccount) -> AlgorandClientTransactionSender:
    def new_group() -> TransactionComposer:
        return TransactionComposer(
            algod=algorand.client.algod,
            get_signer=lambda _: sender.signer,
        )

    return AlgorandClientTransactionSender(
        new_group=new_group,
        asset_manager=AssetManager(algorand.client.algod, new_group),
        app_manager=AppManager(algorand.client.algod),
        algod_client=algorand.client.algod,
    )


def test_payment(
    transaction_sender: AlgorandClientTransactionSender, sender: SigningAccount, receiver: SigningAccount
) -> None:
    amount = AlgoAmount.from_algo(1)
    result = transaction_sender.payment(
        PaymentParams(
            sender=sender.address,
            receiver=receiver.address,
            amount=amount,
        )
    )

    assert len(result.tx_ids) == 1
    assert result.confirmations[-1]["confirmed-round"] > 0  # type: ignore[call-overload]
    txn = result.transaction.payment
    assert txn
    assert txn.sender == sender.address
    assert txn.receiver == receiver.address
    assert txn.amt == amount.micro_algo


def test_asset_create(transaction_sender: AlgorandClientTransactionSender, sender: SigningAccount) -> None:
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
    txn = result.transaction.asset_config
    assert txn
    assert txn.sender == sender.address
    assert txn.total == total
    assert txn.decimals == 0
    assert txn.default_frozen is False
    assert txn.unit_name == "TEST"
    assert txn.asset_name == "Test Asset"
    assert txn.url == "https://example.com"


def test_asset_config(
    transaction_sender: AlgorandClientTransactionSender, sender: SigningAccount, receiver: SigningAccount
) -> None:
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
    assert result.transaction.asset_config
    txn = result.transaction.asset_config
    assert txn
    assert txn.sender == sender.address
    assert txn.index == asset_id
    assert txn.manager == receiver.address


def test_asset_freeze(
    transaction_sender: AlgorandClientTransactionSender,
    sender: SigningAccount,
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
    assert result.transaction.asset_freeze
    txn = result.transaction.asset_freeze
    assert txn
    assert txn.sender == sender.address
    assert txn.index == asset_id
    assert txn.target == sender.address
    assert txn.new_freeze_state is True


def test_asset_destroy(transaction_sender: AlgorandClientTransactionSender, sender: SigningAccount) -> None:
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
    txn = result.transaction.asset_config
    assert txn
    assert txn.sender == sender.address
    assert txn.index == asset_id


def test_asset_transfer(
    transaction_sender: AlgorandClientTransactionSender, sender: SigningAccount, receiver: SigningAccount
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
    txn = result.transaction.asset_transfer
    assert txn
    assert txn.sender == sender.address
    assert txn.index == asset_id
    assert txn.receiver == receiver.address
    assert txn.amount == amount


def test_asset_opt_in(
    transaction_sender: AlgorandClientTransactionSender, sender: SigningAccount, receiver: SigningAccount
) -> None:
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
    assert result.transaction.asset_transfer
    txn = result.transaction.asset_transfer
    assert txn.sender == receiver.address
    assert txn.index == asset_id
    assert txn.amount == 0
    assert txn.receiver == receiver.address


def test_asset_opt_out(
    transaction_sender: AlgorandClientTransactionSender, sender: SigningAccount, receiver: SigningAccount
) -> None:
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

    assert result.transaction.asset_transfer
    txn = result.transaction.asset_transfer
    assert txn.sender == receiver.address
    assert txn.index == asset_id
    assert txn.amount == 0
    assert txn.receiver == receiver.address
    assert txn.close_assets_to == sender.address


def test_app_create(transaction_sender: AlgorandClientTransactionSender, sender: SigningAccount) -> None:
    approval_program = "#pragma version 6\nint 1"
    clear_state_program = "#pragma version 6\nint 1"
    params = AppCreateParams(
        sender=sender.address,
        approval_program=approval_program,
        clear_state_program=clear_state_program,
        schema={"global_ints": 0, "global_byte_slices": 0, "local_ints": 0, "local_byte_slices": 0},
    )

    result = transaction_sender.app_create(params)
    assert result.app_id > 0
    assert result.app_address

    assert result.transaction.application_call
    txn = result.transaction.application_call
    assert txn.sender == sender.address
    assert txn.approval_program == b"\x06\x81\x01"
    assert txn.clear_program == b"\x06\x81\x01"


def test_app_call(
    test_hello_world_arc32_app_id: int, transaction_sender: AlgorandClientTransactionSender, sender: SigningAccount
) -> None:
    params = AppCallParams(
        app_id=test_hello_world_arc32_app_id,
        sender=sender.address,
        on_complete=OnComplete.NoOpOC,
        args=[b"\x02\xbe\xce\x11", b"test"],
    )

    result = transaction_sender.app_call(params)
    assert not result.abi_return  # TODO: improve checks


def test_app_call_method_call(
    test_hello_world_arc32_app_id: int, transaction_sender: AlgorandClientTransactionSender, sender: SigningAccount
) -> None:
    params = AppCallMethodCallParams(
        app_id=test_hello_world_arc32_app_id,
        sender=sender.address,
        method=algosdk.abi.Method.from_signature("hello(string)string"),
        args=["test"],
    )

    result = transaction_sender.app_call_method_call(params)
    assert result.abi_return
    assert result.abi_return.value == "Hello2, test"


@patch("logging.Logger.debug")
def test_payment_logging(
    mock_debug: MagicMock,
    transaction_sender: AlgorandClientTransactionSender,
    sender: SigningAccount,
    receiver: SigningAccount,
) -> None:
    amount = AlgoAmount.from_algo(1)
    transaction_sender.payment(
        PaymentParams(
            sender=sender.address,
            receiver=receiver.address,
            amount=amount,
        )
    )

    assert mock_debug.call_count == 1 if not _EXPERIMENTAL_DEPENDENCIES_INSTALLED else 2
    log_message = mock_debug.call_args_list[0][0][0]
    assert "Sending 1,000,000 µALGO" in log_message
    assert sender.address in log_message
    assert receiver.address in log_message


def test_key_registration(transaction_sender: AlgorandClientTransactionSender, sender: SigningAccount) -> None:
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

    sp = transaction_sender._algod.suggested_params()  # noqa: SLF001

    off_key_reg_params = OfflineKeyRegistrationParams(
        sender=sender.address,
        prevent_account_from_ever_participating_again=True,
    )

    result = transaction_sender.offline_key_registration(off_key_reg_params)
    assert len(result.tx_ids) == 1
    assert result.confirmations[-1]["confirmed-round"] > 0  # type: ignore[call-overload]
