from pathlib import Path

import algosdk
import pytest
from algosdk.transaction import (
    ApplicationCallTxn,
    AssetConfigTxn,
    AssetCreateTxn,
    AssetDestroyTxn,
    AssetFreezeTxn,
    AssetTransferTxn,
    KeyregTxn,
    PaymentTxn,
)

from algokit_utils._legacy_v2.account import get_account
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.models.account import Account
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCallParams,
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
)
from legacy_v2_tests.conftest import get_unique_name


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


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
def funded_secondary_account(algorand: AlgorandClient, funded_account: Account) -> Account:
    secondary_name = get_unique_name()
    account = get_account(algorand.client.algod, secondary_name)
    algorand.send.payment(
        PaymentParams(sender=funded_account.address, receiver=account.address, amount=AlgoAmount.from_algos(1))
    )
    return account


def test_create_payment_transaction(algorand: AlgorandClient, funded_account: Account) -> None:
    txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=funded_account.address,
            receiver=funded_account.address,
            amount=AlgoAmount.from_algos(1),
        )
    )

    assert isinstance(txn, PaymentTxn)
    assert txn.sender == funded_account.address
    assert txn.receiver == funded_account.address
    assert txn.amt == AlgoAmount.from_algos(1).micro_algos


def test_create_asset_create_transaction(algorand: AlgorandClient, funded_account: Account) -> None:
    expected_total = 1000
    txn = algorand.create_transaction.asset_create(
        AssetCreateParams(
            sender=funded_account.address,
            total=expected_total,
            decimals=0,
            default_frozen=False,
            unit_name="TEST",
            asset_name="Test Asset",
            url="https://example.com",
        )
    )

    assert isinstance(txn, AssetCreateTxn)
    assert txn.sender == funded_account.address
    assert txn.total == expected_total
    assert txn.decimals == 0
    assert txn.default_frozen is False
    assert txn.unit_name == "TEST"
    assert txn.asset_name == "Test Asset"
    assert txn.url == "https://example.com"


def test_create_asset_config_transaction(
    algorand: AlgorandClient, funded_account: Account, funded_secondary_account: Account
) -> None:
    txn = algorand.create_transaction.asset_config(
        AssetConfigParams(
            sender=funded_account.address,
            asset_id=1,
            manager=funded_secondary_account.address,
        )
    )

    assert isinstance(txn, AssetConfigTxn)
    assert txn.sender == funded_account.address
    assert txn.index == 1
    assert txn.manager == funded_secondary_account.address


def test_create_asset_freeze_transaction(
    algorand: AlgorandClient, funded_account: Account, funded_secondary_account: Account
) -> None:
    txn = algorand.create_transaction.asset_freeze(
        AssetFreezeParams(
            sender=funded_account.address,
            asset_id=1,
            account=funded_secondary_account.address,
            frozen=True,
        )
    )

    assert isinstance(txn, AssetFreezeTxn)
    assert txn.sender == funded_account.address
    assert txn.index == 1
    assert txn.target == funded_secondary_account.address
    assert txn.new_freeze_state is True


def test_create_asset_destroy_transaction(algorand: AlgorandClient, funded_account: Account) -> None:
    txn = algorand.create_transaction.asset_destroy(
        AssetDestroyParams(
            sender=funded_account.address,
            asset_id=1,
        )
    )

    assert isinstance(txn, AssetDestroyTxn)
    assert txn.sender == funded_account.address
    assert txn.index == 1


def test_create_asset_transfer_transaction(
    algorand: AlgorandClient, funded_account: Account, funded_secondary_account: Account
) -> None:
    expected_amount = 100
    txn = algorand.create_transaction.asset_transfer(
        AssetTransferParams(
            sender=funded_account.address,
            asset_id=1,
            amount=expected_amount,
            receiver=funded_secondary_account.address,
        )
    )

    assert isinstance(txn, AssetTransferTxn)
    assert txn.sender == funded_account.address
    assert txn.index == 1
    assert txn.amount == expected_amount
    assert txn.receiver == funded_secondary_account.address


def test_create_asset_opt_in_transaction(algorand: AlgorandClient, funded_account: Account) -> None:
    txn = algorand.create_transaction.asset_opt_in(
        AssetOptInParams(
            sender=funded_account.address,
            asset_id=1,
        )
    )

    assert isinstance(txn, AssetTransferTxn)
    assert txn.sender == funded_account.address
    assert txn.index == 1
    assert txn.amount == 0
    assert txn.receiver == funded_account.address


def test_create_asset_opt_out_transaction(algorand: AlgorandClient, funded_account: Account) -> None:
    txn = algorand.create_transaction.asset_opt_out(
        AssetOptOutParams(
            sender=funded_account.address,
            asset_id=1,
            creator=funded_account.address,
        )
    )

    assert isinstance(txn, AssetTransferTxn)
    assert txn.sender == funded_account.address
    assert txn.index == 1
    assert txn.amount == 0
    assert txn.receiver == funded_account.address
    assert txn.close_assets_to == funded_account.address


def test_create_app_create_transaction(algorand: AlgorandClient, funded_account: Account) -> None:
    approval_program = "#pragma version 6\nint 1"
    clear_state_program = "#pragma version 6\nint 1"
    txn = algorand.create_transaction.app_create(
        AppCreateParams(
            sender=funded_account.address,
            approval_program=approval_program,
            clear_state_program=clear_state_program,
            schema={"global_ints": 0, "global_byte_slices": 0, "local_ints": 0, "local_byte_slices": 0},
        )
    )

    assert isinstance(txn, ApplicationCallTxn)
    assert txn.sender == funded_account.address
    assert txn.approval_program == b"\x06\x81\x01"
    assert txn.clear_program == b"\x06\x81\x01"


def test_create_app_call_method_call_transaction(algorand: AlgorandClient, funded_account: Account) -> None:
    approval_program = Path(Path(__file__).parent.parent / "artifacts" / "hello_world" / "approval.teal").read_text()
    clear_state_program = Path(Path(__file__).parent.parent / "artifacts" / "hello_world" / "clear.teal").read_text()

    # First create the app
    create_result = algorand.send.app_create(
        AppCreateParams(
            sender=funded_account.address,
            approval_program=approval_program,
            clear_state_program=clear_state_program,
            schema={"global_ints": 0, "global_byte_slices": 0, "local_ints": 0, "local_byte_slices": 0},
        )
    )
    app_id = algorand.client.algod.pending_transaction_info(create_result.tx_ids[0])["application-index"]  # type: ignore[call-overload]

    # Then test creating a method call transaction
    result = algorand.create_transaction.app_call_method_call(
        AppCallMethodCallParams(
            sender=funded_account.address,
            app_id=app_id,
            method=algosdk.abi.Method.from_signature("hello(string)string"),
            args=["world"],
        )
    )

    assert len(result.transactions) == 1
    assert isinstance(result.transactions[0], ApplicationCallTxn)
    assert result.transactions[0].sender == funded_account.address
    assert result.transactions[0].index == app_id


def test_create_online_key_registration_transaction(algorand: AlgorandClient, funded_account: Account) -> None:
    sp = algorand.get_suggested_params()
    expected_dilution = 100
    expected_first = sp.first
    expected_last = sp.first + int(10e6)

    txn = algorand.create_transaction.online_key_registration(
        OnlineKeyRegistrationParams(
            sender=funded_account.address,
            vote_key="G/lqTV6MKspW6J8wH2d8ZliZ5XZVZsruqSBJMwLwlmo=",
            selection_key="LrpLhvzr+QpN/bivh6IPpOaKGbGzTTB5lJtVfixmmgk=",
            state_proof_key=b"RpUpNWfZMjZ1zOOjv3MF2tjO714jsBt0GKnNsw0ihJ4HSZwci+d9zvUi3i67LwFUJgjQ5Dz4zZgHgGduElnmSA==",
            vote_first=expected_first,
            vote_last=expected_last,
            vote_key_dilution=expected_dilution,
        )
    )

    assert isinstance(txn, KeyregTxn)
    assert txn.sender == funded_account.address
    assert txn.selkey == "LrpLhvzr+QpN/bivh6IPpOaKGbGzTTB5lJtVfixmmgk="
    assert txn.sprfkey == b"RpUpNWfZMjZ1zOOjv3MF2tjO714jsBt0GKnNsw0ihJ4HSZwci+d9zvUi3i67LwFUJgjQ5Dz4zZgHgGduElnmSA=="
    assert txn.votefst == expected_first
    assert txn.votelst == expected_last
    assert txn.votekd == expected_dilution
