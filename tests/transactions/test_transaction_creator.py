import base64
from pathlib import Path

import pytest

from algokit_utils.algorand import AlgorandClient
from algokit_utils.applications.app_spec import arc56
from algokit_utils.models.account import SigningAccount
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
def funded_secondary_account(algorand: AlgorandClient, funded_account: SigningAccount) -> SigningAccount:
    account = algorand.account.random()
    algorand.send.payment(
        PaymentParams(sender=funded_account.address, receiver=account.address, amount=AlgoAmount.from_algo(1))
    )
    return account


def test_create_payment_transaction(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=funded_account.address,
            receiver=funded_account.address,
            amount=AlgoAmount.from_algo(1),
        )
    )

    assert txn.payment
    assert txn.sender == funded_account.address
    assert txn.payment.receiver == funded_account.address
    assert txn.payment.amount == AlgoAmount.from_algo(1).micro_algo


def test_create_asset_create_transaction(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
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

    assert txn.asset_config
    assert txn.sender == funded_account.address
    assert txn.asset_config.total == expected_total
    assert txn.asset_config.decimals == 0
    assert txn.asset_config.default_frozen is False
    assert txn.asset_config.unit_name == "TEST"
    assert txn.asset_config.asset_name == "Test Asset"
    assert txn.asset_config.url == "https://example.com"


def test_create_asset_config_transaction(
    algorand: AlgorandClient, funded_account: SigningAccount, funded_secondary_account: SigningAccount
) -> None:
    txn = algorand.create_transaction.asset_config(
        AssetConfigParams(
            sender=funded_account.address,
            asset_id=1,
            manager=funded_secondary_account.address,
        )
    )

    assert txn.asset_config
    assert txn.sender == funded_account.address
    assert txn.asset_config.asset_id == 1
    assert txn.asset_config.manager == funded_secondary_account.address


def test_create_asset_freeze_transaction(
    algorand: AlgorandClient, funded_account: SigningAccount, funded_secondary_account: SigningAccount
) -> None:
    txn = algorand.create_transaction.asset_freeze(
        AssetFreezeParams(
            sender=funded_account.address,
            asset_id=1,
            account=funded_secondary_account.address,
            frozen=True,
        )
    )

    assert txn.asset_freeze
    assert txn.sender == funded_account.address
    assert txn.asset_freeze.asset_id == 1
    assert txn.asset_freeze.freeze_target == funded_secondary_account.address
    assert txn.asset_freeze.frozen is True


def test_create_asset_destroy_transaction(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    txn = algorand.create_transaction.asset_destroy(
        AssetDestroyParams(
            sender=funded_account.address,
            asset_id=1,
        )
    )

    assert txn.asset_config
    assert txn.sender == funded_account.address
    assert txn.asset_config.asset_id == 1


def test_create_asset_transfer_transaction(
    algorand: AlgorandClient, funded_account: SigningAccount, funded_secondary_account: SigningAccount
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

    assert txn.asset_transfer
    assert txn.sender == funded_account.address
    assert txn.asset_transfer.asset_id == 1
    assert txn.asset_transfer.amount == expected_amount
    assert txn.asset_transfer.receiver == funded_secondary_account.address


def test_created_transactions_have_no_group(
    algorand: AlgorandClient, funded_account: SigningAccount, funded_secondary_account: SigningAccount
) -> None:
    txn = algorand.create_transaction.asset_transfer(
        AssetTransferParams(
            sender=funded_account.address,
            asset_id=1,
            amount=10,
            receiver=funded_secondary_account.address,
        )
    )

    assert txn.group is None


def test_create_asset_opt_in_transaction(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    txn = algorand.create_transaction.asset_opt_in(
        AssetOptInParams(
            sender=funded_account.address,
            asset_id=1,
        )
    )

    assert txn.asset_transfer
    assert txn.sender == funded_account.address
    assert txn.asset_transfer.asset_id == 1
    assert txn.asset_transfer.amount == 0
    assert txn.asset_transfer.receiver == funded_account.address


def test_create_asset_opt_out_transaction(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    txn = algorand.create_transaction.asset_opt_out(
        AssetOptOutParams(
            sender=funded_account.address,
            asset_id=1,
            creator=funded_account.address,
        )
    )

    assert txn.asset_transfer
    assert txn.sender == funded_account.address
    assert txn.asset_transfer.asset_id == 1
    assert txn.asset_transfer.amount == 0
    assert txn.asset_transfer.receiver == funded_account.address
    assert txn.asset_transfer.close_remainder_to == funded_account.address


def test_create_app_create_transaction(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
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

    assert txn.app_call
    assert txn.sender == funded_account.address
    assert txn.app_call.approval_program == b"\x06\x81\x01"
    assert txn.app_call.clear_state_program == b"\x06\x81\x01"


def test_create_app_call_method_call_transaction(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
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
    confirmation = algorand.client.algod.pending_transaction_information(create_result.tx_ids[0])
    assert confirmation.app_id is not None
    app_id = confirmation.app_id

    # Then test creating a method call transaction
    result = algorand.create_transaction.app_call_method_call(
        AppCallMethodCallParams(
            sender=funded_account.address,
            app_id=app_id,
                method=arc56.Method.from_signature("hello(string)string"),
            args=["world"],
        )
    )

    assert len(result.transactions) == 1
    transactions = result.transactions[0]
    assert transactions.app_call
    assert transactions.sender == funded_account.address
    assert transactions.app_call.app_id == app_id


def test_create_online_key_registration_transaction(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    sp = algorand.get_suggested_params()
    expected_dilution = 100
    expected_first = sp.first_valid
    expected_last = sp.first_valid + int(10e6)

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

    assert txn.key_registration
    assert txn.sender == funded_account.address
    assert txn.key_registration.selection_key == base64.b64decode("LrpLhvzr+QpN/bivh6IPpOaKGbGzTTB5lJtVfixmmgk=")
    assert txn.key_registration.state_proof_key == base64.b64decode(
        "RpUpNWfZMjZ1zOOjv3MF2tjO714jsBt0GKnNsw0ihJ4HSZwci+d9zvUi3i67LwFUJgjQ5Dz4zZgHgGduElnmSA=="
    )
    assert txn.key_registration.vote_first == expected_first
    assert txn.key_registration.vote_last == expected_last
    assert txn.key_registration.vote_key_dilution == expected_dilution
