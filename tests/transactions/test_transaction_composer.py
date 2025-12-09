import base64
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from algokit_abi import arc56
from algokit_transact import make_empty_transaction_signer
from algokit_transact.signer import AddressWithSigners
from algokit_utils.algorand import AlgorandClient
from algokit_utils.models.account import MultisigMetadata
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCallParams,
    AppCreateParams,
    AssetConfigParams,
    AssetCreateParams,
    AssetTransferParams,
    PaymentParams,
    SendTransactionComposerResults,
    TransactionComposer,
    TransactionComposerParams,
)


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


@pytest.fixture(autouse=True)
def mock_config() -> Generator[Mock, None, None]:
    with patch("algokit_utils.transactions.transaction_composer.config", new_callable=Mock) as mock_config:
        mock_config.debug = True
        mock_config.project_root = None
        yield mock_config


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> AddressWithSigners:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account, dispenser, AlgoAmount.from_algo(100), min_funding_increment=AlgoAmount.from_algo(1)
    )
    algorand.set_signer(sender=new_account.addr, signer=new_account.signer)
    return new_account


@pytest.fixture
def funded_secondary_account(algorand: AlgorandClient, funded_account: AddressWithSigners) -> AddressWithSigners:
    account = algorand.account.random()
    algorand.send.payment(
        PaymentParams(sender=funded_account.addr, receiver=account.addr, amount=AlgoAmount.from_algo(2))
    )
    return account


def test_add_transaction(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    composer = algorand.new_group()
    txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=funded_account.addr,
            receiver=funded_account.addr,
            amount=AlgoAmount.from_algo(1),
        )
    )
    composer.add_transaction(txn)
    built = composer.build_transactions()

    assert len(built.transactions) == 1
    assert built.transactions[0].payment
    assert built.transactions[0].sender == funded_account.addr
    assert built.transactions[0].payment.receiver == funded_account.addr
    assert built.transactions[0].payment.amount == AlgoAmount.from_algo(1).micro_algo


def test_add_asset_create(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    composer = algorand.new_group()
    expected_total = 1000
    params = AssetCreateParams(
        sender=funded_account.addr,
        total=expected_total,
        decimals=0,
        default_frozen=False,
        unit_name="TEST",
        asset_name="Test Asset",
        url="https://example.com",
    )

    composer.add_asset_create(params)
    built = composer.build_transactions()
    response = composer.send({"max_rounds_to_wait": 20})
    confirmation = response.confirmations[-1]
    asset_id = confirmation.asset_id
    assert asset_id is not None

    assert len(response.tx_ids) == 1
    assert confirmation.confirmed_round is not None
    assert confirmation.confirmed_round > 0
    assert built.transactions[0].asset_config
    txn = built.transactions[0]
    assert txn.sender == funded_account.addr
    created_asset = algorand.client.algod.get_asset_by_id(asset_id).params
    assert created_asset.creator == funded_account.addr
    assert txn.asset_config.total == created_asset.total == expected_total
    assert txn.asset_config.decimals == created_asset.decimals == 0
    assert txn.asset_config.default_frozen is False
    assert txn.asset_config.unit_name == created_asset.unit_name == "TEST"
    assert txn.asset_config.asset_name == created_asset.name == "Test Asset"


def test_add_asset_config(
    algorand: AlgorandClient, funded_account: AddressWithSigners, funded_secondary_account: AddressWithSigners
) -> None:
    created = algorand.send.asset_create(
        AssetCreateParams(
            sender=funded_account.addr,
            total=1000,
            decimals=0,
            default_frozen=False,
            unit_name="CFG",
            asset_name="Configurable Asset",
            manager=funded_account.addr,
        )
    )
    asset_id = created.asset_id

    composer = algorand.new_group()
    params = AssetConfigParams(
        sender=funded_account.addr,
        asset_id=asset_id,
        manager=funded_secondary_account.addr,
    )
    composer.add_asset_config(params)
    built = composer.build_transactions()

    assert len(built.transactions) == 1
    txn = built.transactions[0]
    assert txn.asset_config
    assert txn.asset_config.asset_id == asset_id
    assert txn.asset_config.manager == funded_secondary_account.addr

    composer.send({"max_rounds_to_wait": 20})
    updated_asset = algorand.client.algod.get_asset_by_id(asset_id).params
    assert updated_asset.manager == funded_secondary_account.addr


def test_add_app_create(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    composer = algorand.new_group()
    approval_program = "#pragma version 6\nint 1"
    clear_state_program = "#pragma version 6\nint 1"
    params = AppCreateParams(
        sender=funded_account.addr,
        approval_program=approval_program,
        clear_state_program=clear_state_program,
        schema={"global_ints": 0, "global_byte_slices": 0, "local_ints": 0, "local_byte_slices": 0},
    )
    composer.add_app_create(params)
    built = composer.build_transactions()

    assert len(built.transactions) == 1
    txn = built.transactions[0]
    assert txn.app_call
    assert txn.sender == funded_account.addr
    assert txn.app_call.approval_program
    assert txn.app_call.clear_state_program
    response = composer.send({"max_rounds_to_wait": 20})
    assert response.confirmations[-1].app_id is not None


def test_add_app_call_method_call(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    approval_program = Path(Path(__file__).parent.parent / "artifacts" / "hello_world" / "approval.teal").read_text()
    clear_state_program = Path(Path(__file__).parent.parent / "artifacts" / "hello_world" / "clear.teal").read_text()
    create_response = algorand.send.app_create(
        AppCreateParams(
            sender=funded_account.addr,
            approval_program=approval_program,
            clear_state_program=clear_state_program,
            schema={"global_ints": 0, "global_byte_slices": 0, "local_ints": 0, "local_byte_slices": 0},
        )
    )
    app_id = create_response.app_id

    composer = algorand.new_group()
    composer.add_app_call_method_call(
        AppCallMethodCallParams(
            sender=funded_account.addr,
            app_id=app_id,
            method=arc56.Method.from_signature("hello(string)string"),
            args=["world"],
        )
    )
    built = composer.build_transactions()

    assert len(built.transactions) == 1
    assert built.transactions[0].app_call
    response = composer.send({"max_rounds_to_wait": 20})
    assert response.returns[-1].value == "Hello, world"


def test_simulate(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    composer = algorand.new_group()
    composer.add_payment(
        PaymentParams(
            sender=funded_account.addr,
            receiver=funded_account.addr,
            amount=AlgoAmount.from_algo(1),
        )
    )
    composer.build()
    simulate_response = composer.simulate()
    assert simulate_response.simulate_response is not None
    assert len(simulate_response.transactions) == 1


def test_simulate_without_signer(algorand: AlgorandClient, funded_secondary_account: AddressWithSigners) -> None:
    composer = TransactionComposer(
        TransactionComposerParams(
            algod=algorand.client.algod,
            get_signer=lambda _: make_empty_transaction_signer(),
        )
    )
    composer.add_payment(
        PaymentParams(
            sender=funded_secondary_account.addr,
            receiver=funded_secondary_account.addr,
            amount=AlgoAmount.from_algo(1),
        )
    )
    composer.build()
    simulate_response = composer.simulate(skip_signatures=True)
    assert simulate_response.simulate_response is not None
    assert len(simulate_response.transactions) == 1


def test_build_fails_without_signer(algorand: AlgorandClient, funded_secondary_account: AddressWithSigners) -> None:
    composer = TransactionComposer(
        TransactionComposerParams(
            algod=algorand.client.algod,
            get_signer=lambda _: None,
        )
    )
    composer.add_payment(
        PaymentParams(
            sender=funded_secondary_account.addr,
            receiver=funded_secondary_account.addr,
            amount=AlgoAmount.from_algo(1),
        )
    )

    with pytest.raises(ValueError, match=f"No signer found for address {funded_secondary_account.addr}"):
        composer.build()


def test_send(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    composer = algorand.new_group()
    composer.add_payment(
        PaymentParams(
            sender=funded_account.addr,
            receiver=funded_account.addr,
            amount=AlgoAmount.from_algo(1),
        )
    )
    response = composer.send()
    assert isinstance(response, SendTransactionComposerResults)
    assert len(response.tx_ids) == 1
    assert response.confirmations[-1].confirmed_round is not None
    assert response.confirmations[-1].confirmed_round > 0


def test_arc2_note() -> None:
    note_data = {
        "dapp_name": "TestDApp",
        "format": "j",
        "data": '{"key":"value"}',
    }
    encoded_note = TransactionComposer.arc2_note(note_data)
    expected_note = b'TestDApp:j{"key":"value"}'
    assert encoded_note == expected_note


def test_arc2_note_validates() -> None:
    with pytest.raises(ValueError, match="dapp_name must be"):
        TransactionComposer.arc2_note({"dapp_name": "_invalid", "format": "j", "data": "x"})  # type: ignore[arg-type]


def _get_test_transaction(
    default_account: AddressWithSigners, amount: AlgoAmount | None = None, sender: AddressWithSigners | None = None
) -> dict[str, Any]:
    return {
        "sender": sender.addr if sender else default_account.addr,
        "receiver": default_account.addr,
        "amount": amount or AlgoAmount.from_algo(1),
    }


def test_transaction_is_capped_by_low_min_txn_fee(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    with pytest.raises(ValueError, match="Transaction fee 1000 µALGO is greater than max fee 1 µALGO"):
        algorand.send.payment(
            PaymentParams(**_get_test_transaction(funded_account), max_fee=AlgoAmount.from_micro_algo(1))
        )


def test_transaction_cap_is_ignored_if_higher_than_fee(
    algorand: AlgorandClient, funded_account: AddressWithSigners
) -> None:
    response = algorand.send.payment(
        PaymentParams(**_get_test_transaction(funded_account), max_fee=AlgoAmount.from_micro_algo(1_000_000))
    )
    assert response.confirmation.txn.transaction.fee == AlgoAmount.from_micro_algo(1000)


def test_transaction_fee_is_overridable(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    response = algorand.send.payment(
        PaymentParams(**_get_test_transaction(funded_account), static_fee=AlgoAmount.from_algo(1))
    )
    assert response.confirmation.txn.transaction.fee == AlgoAmount.from_algo(1)


def test_transaction_group_is_sent(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    composer = algorand.new_group()
    composer.add_payment(PaymentParams(**_get_test_transaction(funded_account, amount=AlgoAmount.from_algo(1))))
    composer.add_payment(PaymentParams(**_get_test_transaction(funded_account, amount=AlgoAmount.from_algo(2))))
    response = composer.send()

    assert response.transactions[0].group is not None
    assert response.transactions[1].group is not None
    assert len(response.confirmations) == 2
    group_bytes = response.transactions[0].group
    assert group_bytes is not None
    expected_group = base64.b64encode(group_bytes).decode()
    assert response.confirmations[0].txn.transaction.group == group_bytes
    assert response.confirmations[1].txn.transaction.group == group_bytes
    assert response.confirmations[0].txn.transaction.group == base64.b64decode(expected_group.encode())


def test_multisig_single_account(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    multisig = algorand.account.multisig(
        metadata=MultisigMetadata(
            version=1,
            threshold=1,
            addresses=[funded_account.addr],
        ),
        sub_signers=[funded_account],
    )
    algorand.send.payment(
        PaymentParams(sender=funded_account.addr, receiver=multisig.addr, amount=AlgoAmount.from_algo(1))
    )
    algorand.send.payment(
        PaymentParams(sender=multisig.addr, receiver=funded_account.addr, amount=AlgoAmount.from_micro_algo(500))
    )


def test_multisig_double_account(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    account2 = algorand.account.random()
    algorand.account.ensure_funded(account2, funded_account, AlgoAmount.from_algo(10))

    multisig = algorand.account.multisig(
        metadata=MultisigMetadata(
            version=1,
            threshold=2,
            addresses=[funded_account.addr, account2.addr],
        ),
        sub_signers=[funded_account, account2],
    )

    algorand.send.payment(
        PaymentParams(sender=funded_account.addr, receiver=multisig.addr, amount=AlgoAmount.from_algo(1))
    )
    algorand.send.payment(
        PaymentParams(sender=multisig.addr, receiver=funded_account.addr, amount=AlgoAmount.from_micro_algo(500))
    )


def test_error_transformers_chaining(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    def error_transformer_1(error: Exception) -> Exception:
        if "missing from" in str(error):
            return Exception("ASSET MISSING???")
        return error

    def error_transformer_2(error: Exception) -> Exception:
        if str(error) == "ASSET MISSING???":
            return Exception("ASSET MISSING!")
        return error

    composer = algorand.new_group()
    composer.register_error_transformer(error_transformer_1)
    composer.register_error_transformer(error_transformer_2)

    composer.add_asset_transfer(
        AssetTransferParams(
            sender=funded_account.addr,
            receiver=funded_account.addr,
            amount=1,
            asset_id=1337,
        )
    )

    with pytest.raises(Exception, match="ASSET MISSING!"):
        composer.simulate()


def test_error_transformers_applied_on_send(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    def transformer(error: Exception) -> Exception:
        if "missing from" in str(error):
            return Exception("ASSET MISSING ON SEND")
        return error

    composer = algorand.new_group()
    composer.register_error_transformer(transformer)
    composer.add_asset_transfer(
        AssetTransferParams(
            sender=funded_account.addr,
            receiver=funded_account.addr,
            amount=1,
            asset_id=9999999,
        )
    )

    with pytest.raises(Exception, match="ASSET MISSING ON SEND"):
        composer.send({"max_rounds_to_wait": 0})


def test_simulate_does_not_throw_when_disabled(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    composer = algorand.new_group()
    composer.add_asset_transfer(
        AssetTransferParams(
            sender=funded_account.addr,
            receiver=funded_account.addr,
            amount=1,
            asset_id=9999999,
        )
    )

    result = composer.simulate(result_on_failure=True)
    assert result.simulate_response is not None


def test_clone_keeps_groups_independent(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    payment_txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=funded_account.addr,
            receiver=funded_account.addr,
            amount=AlgoAmount.from_algo(1),
        )
    )

    composer1 = algorand.new_group()
    composer1.add_transaction(payment_txn)
    composer1.add_payment(
        PaymentParams(sender=funded_account.addr, receiver=funded_account.addr, amount=AlgoAmount.from_algo(1))
    )

    composer2 = composer1.clone()
    composer2.add_payment(
        PaymentParams(sender=funded_account.addr, receiver=funded_account.addr, amount=AlgoAmount.from_algo(2))
    )

    group1 = composer1.build().transactions[0].group
    group2 = composer2.build().transactions[0].group

    assert group1 is not None
    assert group2 is not None
    assert group1 != group2
