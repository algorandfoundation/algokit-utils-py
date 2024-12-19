import base64
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import algosdk
import pytest
from algosdk.transaction import (
    ApplicationCallTxn,
    AssetConfigTxn,
    AssetCreateTxn,
    PaymentTxn,
)

from algokit_utils._legacy_v2.account import get_account
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.models.account import Account
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.models.transaction import SendAtomicTransactionComposerResults
from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCallParams,
    AppCreateParams,
    AssetConfigParams,
    AssetCreateParams,
    PaymentParams,
    TransactionComposer,
)
from legacy_v2_tests.conftest import get_unique_name

if TYPE_CHECKING:
    from algokit_utils.models.transaction import Arc2TransactionNote


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_local_net()


@pytest.fixture(autouse=True)
def mock_config() -> Generator[Mock, None, None]:
    with patch("algokit_utils.transactions.transaction_composer.config", new_callable=Mock) as mock_config:
        mock_config.debug = True
        mock_config.project_root = None
        yield mock_config


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> Account:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account, dispenser, AlgoAmount.from_algos(100), min_funding_increment=AlgoAmount.from_algos(1)
    )
    algorand.set_signer(sender=new_account.address, signer=new_account.signer)
    return new_account


@pytest.fixture
def funded_secondary_account(algorand: AlgorandClient) -> Account:
    secondary_name = get_unique_name()
    return get_account(algorand.client.algod, secondary_name)


def test_add_transaction(algorand: AlgorandClient, funded_account: Account) -> None:
    composer = TransactionComposer(
        algod=algorand.client.algod,
        get_signer=lambda _: funded_account.signer,
    )
    txn = PaymentTxn(
        sender=funded_account.address,
        sp=algorand.client.algod.suggested_params(),
        receiver=funded_account.address,
        amt=AlgoAmount.from_algos(1).micro_algos,
    )
    composer.add_transaction(txn)
    built = composer.build_transactions()

    assert len(built.transactions) == 1
    assert isinstance(built.transactions[0], PaymentTxn)
    assert built.transactions[0].sender == funded_account.address
    assert built.transactions[0].receiver == funded_account.address
    assert built.transactions[0].amt == AlgoAmount.from_algos(1).micro_algos


def test_add_asset_create(algorand: AlgorandClient, funded_account: Account) -> None:
    composer = TransactionComposer(
        algod=algorand.client.algod,
        get_signer=lambda _: funded_account.signer,
    )
    expected_total = 1000
    params = AssetCreateParams(
        sender=funded_account.address,
        total=expected_total,
        decimals=0,
        default_frozen=False,
        unit_name="TEST",
        asset_name="Test Asset",
        url="https://example.com",
    )

    composer.add_asset_create(params)
    built = composer.build_transactions()
    response = composer.send(max_rounds_to_wait=20)
    created_asset = algorand.client.algod.asset_info(
        algorand.client.algod.pending_transaction_info(response.tx_ids[0])["asset-index"]  # type: ignore[call-overload]
    )["params"]

    assert len(response.tx_ids) == 1
    assert response.confirmations[-1]["confirmed-round"] > 0  # type: ignore[call-overload]
    assert isinstance(built.transactions[0], AssetCreateTxn)
    txn = built.transactions[0]
    assert txn.sender == funded_account.address
    assert created_asset["creator"] == funded_account.address
    assert txn.total == created_asset["total"] == expected_total
    assert txn.decimals == created_asset["decimals"] == 0
    assert txn.default_frozen == created_asset["default-frozen"] is False
    assert txn.unit_name == created_asset["unit-name"] == "TEST"
    assert txn.asset_name == created_asset["name"] == "Test Asset"


def test_add_asset_config(algorand: AlgorandClient, funded_account: Account, funded_secondary_account: Account) -> None:
    # First create an asset
    asset_txn = AssetCreateTxn(
        sender=funded_account.address,
        sp=algorand.client.algod.suggested_params(),
        total=1000,
        decimals=0,
        default_frozen=False,
        unit_name="CFG",
        asset_name="Configurable Asset",
        manager=funded_account.address,
    )
    signed_asset_txn = asset_txn.sign(funded_account.signer.private_key)
    tx_id = algorand.client.algod.send_transaction(signed_asset_txn)
    asset_before_config = algorand.client.algod.asset_info(
        algorand.client.algod.pending_transaction_info(tx_id)["asset-index"]  # type: ignore[call-overload]
    )
    asset_before_config_index = asset_before_config["index"]  # type: ignore[call-overload]

    composer = TransactionComposer(
        algod=algorand.client.algod,
        get_signer=lambda _: funded_account.signer,
    )
    params = AssetConfigParams(
        sender=funded_account.address,
        asset_id=asset_before_config_index,
        manager=funded_secondary_account.address,
    )
    composer.add_asset_config(params)
    built = composer.build_transactions()

    assert len(built.transactions) == 1
    assert isinstance(built.transactions[0], AssetConfigTxn)
    txn = built.transactions[0]
    assert txn.sender == funded_account.address
    assert txn.index == asset_before_config_index
    assert txn.manager == funded_secondary_account.address

    composer.send(max_rounds_to_wait=20)
    updated_asset = algorand.client.algod.asset_info(asset_id=asset_before_config_index)["params"]  # type: ignore[call-overload]
    assert updated_asset["manager"] == funded_secondary_account.address


def test_add_app_create(algorand: AlgorandClient, funded_account: Account) -> None:
    composer = TransactionComposer(
        algod=algorand.client.algod,
        get_signer=lambda _: funded_account.signer,
    )
    approval_program = "#pragma version 6\nint 1"
    clear_state_program = "#pragma version 6\nint 1"
    params = AppCreateParams(
        sender=funded_account.address,
        approval_program=approval_program,
        clear_state_program=clear_state_program,
        schema={"global_ints": 0, "global_bytes": 0, "local_ints": 0, "local_bytes": 0},
    )
    composer.add_app_create(params)
    built = composer.build_transactions()

    assert len(built.transactions) == 1
    assert isinstance(built.transactions[0], ApplicationCallTxn)
    txn = built.transactions[0]
    assert txn.sender == funded_account.address
    assert txn.approval_program == b"\x06\x81\x01"
    assert txn.clear_program == b"\x06\x81\x01"
    composer.send(max_rounds_to_wait=20)


def test_add_app_call_method_call(algorand: AlgorandClient, funded_account: Account) -> None:
    composer = TransactionComposer(
        algod=algorand.client.algod,
        get_signer=lambda _: funded_account.signer,
    )
    approval_program = Path(Path(__file__).parent.parent / "artifacts" / "hello_world" / "approval.teal").read_text()
    clear_state_program = Path(Path(__file__).parent.parent / "artifacts" / "hello_world" / "clear.teal").read_text()
    composer.add_app_create(
        AppCreateParams(
            sender=funded_account.address,
            approval_program=approval_program,
            clear_state_program=clear_state_program,
            schema={"global_ints": 0, "global_bytes": 0, "local_ints": 0, "local_bytes": 0},
        )
    )
    response = composer.send()
    app_id = algorand.client.algod.pending_transaction_info(response.tx_ids[0])["application-index"]  # type: ignore[call-overload]

    composer = TransactionComposer(
        algod=algorand.client.algod,
        get_signer=lambda _: funded_account.signer,
    )
    composer.add_app_call_method_call(
        AppCallMethodCallParams(
            sender=funded_account.address,
            app_id=app_id,
            method=algosdk.abi.Method.from_signature("hello(string)string"),
            args=["world"],
        )
    )
    built = composer.build_transactions()

    assert len(built.transactions) == 1
    assert isinstance(built.transactions[0], ApplicationCallTxn)
    txn = built.transactions[0]
    assert txn.sender == funded_account.address
    response = composer.send(max_rounds_to_wait=20)
    assert response.returns[-1].value == "Hello, world"


def test_simulate(algorand: AlgorandClient, funded_account: Account) -> None:
    composer = TransactionComposer(
        algod=algorand.client.algod,
        get_signer=lambda _: funded_account.signer,
    )
    composer.add_payment(
        PaymentParams(
            sender=funded_account.address,
            receiver=funded_account.address,
            amount=AlgoAmount.from_algos(1),
        )
    )
    composer.build()
    simulate_response = composer.simulate()
    assert simulate_response


def test_send(algorand: AlgorandClient, funded_account: Account) -> None:
    composer = TransactionComposer(
        algod=algorand.client.algod,
        get_signer=lambda _: funded_account.signer,
    )
    composer.add_payment(
        PaymentParams(
            sender=funded_account.address,
            receiver=funded_account.address,
            amount=AlgoAmount.from_algos(1),
        )
    )
    response = composer.send()
    assert isinstance(response, SendAtomicTransactionComposerResults)
    assert len(response.tx_ids) == 1
    assert response.confirmations[-1]["confirmed-round"] > 0  # type: ignore[call-overload]


def test_arc2_note() -> None:
    note_data: Arc2TransactionNote = {
        "dapp_name": "TestDApp",
        "format": "j",
        "data": '{"key":"value"}',
    }
    encoded_note = TransactionComposer.arc2_note(note_data)
    expected_note = b'TestDApp:j{"key":"value"}'
    assert encoded_note == expected_note


def _get_test_transaction(
    default_account: Account, amount: AlgoAmount | None = None, sender: Account | None = None
) -> dict[str, Any]:
    return {
        "sender": sender.address if sender else default_account.address,
        "receiver": default_account.address,
        "amount": amount or AlgoAmount.from_algos(1),
    }


def test_transaction_is_capped_by_low_min_txn_fee(algorand: AlgorandClient, funded_account: Account) -> None:
    with pytest.raises(ValueError, match="Transaction fee 1000 is greater than max_fee 1 µALGO"):
        algorand.send.payment(
            PaymentParams(**_get_test_transaction(funded_account), max_fee=AlgoAmount.from_micro_algo(1))
        )


def test_transaction_cap_is_ignored_if_higher_than_fee(algorand: AlgorandClient, funded_account: Account) -> None:
    response = algorand.send.payment(
        PaymentParams(**_get_test_transaction(funded_account), max_fee=AlgoAmount.from_micro_algo(1_000_000))
    )
    assert response.confirmation["txn"]["txn"]["fee"] == AlgoAmount.from_micro_algo(1000)


def test_transaction_fee_is_overridable(algorand: AlgorandClient, funded_account: Account) -> None:
    response = algorand.send.payment(
        PaymentParams(**_get_test_transaction(funded_account), static_fee=AlgoAmount.from_algos(1))
    )
    assert response.confirmation["txn"]["txn"]["fee"] == AlgoAmount.from_algos(1)


def test_transaction_group_is_sent(algorand: AlgorandClient, funded_account: Account) -> None:
    composer = TransactionComposer(
        algod=algorand.client.algod,
        get_signer=lambda _: funded_account.signer,
    )
    composer.add_payment(PaymentParams(**_get_test_transaction(funded_account, amount=AlgoAmount.from_algos(1))))
    composer.add_payment(PaymentParams(**_get_test_transaction(funded_account, amount=AlgoAmount.from_algos(2))))
    response = composer.send()

    assert response.confirmations[0]["txn"]["txn"]["grp"] is not None
    assert response.confirmations[1]["txn"]["txn"]["grp"] is not None
    assert response.transactions[0].payment.group is not None
    assert response.transactions[1].payment.group is not None
    assert len(response.confirmations) == 2
    assert response.confirmations[0]["confirmed-round"] >= response.transactions[0].payment.first_valid_round
    assert response.confirmations[1]["confirmed-round"] >= response.transactions[1].payment.first_valid_round
    assert (
        response.confirmations[0]["txn"]["txn"]["grp"]
        == base64.b64encode(response.transactions[0].payment.group).decode()
    )
    assert (
        response.confirmations[1]["txn"]["txn"]["grp"]
        == base64.b64encode(response.transactions[1].payment.group).decode()
    )


def test_multisig_single_account(algorand: AlgorandClient, funded_account: Account) -> None:
    multisig = algorand.account.multi_sig(
        version=1, threshold=1, addrs=[funded_account.address], signing_accounts=[funded_account]
    )
    algorand.send.payment(
        PaymentParams(sender=funded_account.address, receiver=multisig.address, amount=AlgoAmount.from_algos(1))
    )
    algorand.send.payment(
        PaymentParams(sender=multisig.address, receiver=funded_account.address, amount=AlgoAmount.from_micro_algo(500))
    )


def test_multisig_double_account(algorand: AlgorandClient, funded_account: Account) -> None:
    account2 = algorand.account.random()
    algorand.account.ensure_funded(account2, funded_account, AlgoAmount.from_algos(10))

    # Setup multisig
    multisig = algorand.account.multi_sig(
        version=1,
        threshold=2,
        addrs=[funded_account.address, account2.address],
        signing_accounts=[funded_account, account2],
    )

    # Fund multisig
    algorand.send.payment(
        PaymentParams(sender=funded_account.address, receiver=multisig.address, amount=AlgoAmount.from_algos(1))
    )

    # Use multisig
    algorand.send.payment(
        PaymentParams(sender=multisig.address, receiver=funded_account.address, amount=AlgoAmount.from_micro_algo(500))
    )


@pytest.mark.usefixtures("mock_config")
def test_transactions_fails_in_debug_mode(algorand: AlgorandClient, funded_account: Account) -> None:
    txn1 = algorand.create_transaction.payment(PaymentParams(**_get_test_transaction(funded_account)))
    txn2 = algorand.create_transaction.payment(
        PaymentParams(**_get_test_transaction(funded_account, amount=AlgoAmount.from_micro_algo(9999999999999)))
    )
    composer = TransactionComposer(
        algod=algorand.client.algod,
        get_signer=lambda _: funded_account.signer,
    )
    composer.add_transaction(txn1)
    composer.add_transaction(txn2)

    with pytest.raises(Exception) as e:  # noqa: PT011
        composer.send()

    assert f"transaction {txn2.get_txid()}: overspend" in e.value.traces[0]["failure_message"]  # type: ignore[attr-defined]
