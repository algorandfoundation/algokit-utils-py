from typing import TYPE_CHECKING

import pytest
from algosdk.transaction import (
    ApplicationCreateTxn,
    AssetConfigTxn,
    AssetCreateTxn,
    PaymentTxn,
)

from algokit_utils._legacy_v2.account import get_account
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.models.account import Account
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import (
    AppCreateParams,
    AssetConfigParams,
    AssetCreateParams,
    PaymentParams,
    SendAtomicTransactionComposerResults,
    TransactionComposer,
)
from legacy_v2_tests.conftest import get_unique_name

if TYPE_CHECKING:
    from algokit_utils.transactions.models import Arc2TransactionNote


@pytest.fixture
def algorand(funded_account: Account) -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_signer(sender=funded_account.address, signer=funded_account.signer)
    return client


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
    response = composer.execute(max_rounds_to_wait=20)
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

    composer.execute(max_rounds_to_wait=20)
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
    assert isinstance(built.transactions[0], ApplicationCreateTxn)
    txn = built.transactions[0]
    assert txn.sender == funded_account.address
    assert txn.approval_program == b"\x06\x81\x01"
    assert txn.clear_program == b"\x06\x81\x01"
    composer.execute(max_rounds_to_wait=20)


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
