import base64
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from algokit_abi import abi, arc56
from algokit_transact import MultisigMetadata, TransactionValidationError, make_empty_transaction_signer
from algokit_transact.signer import AddressWithSigners
from algokit_utils import AssetDestroyParams
from algokit_utils.algorand import AlgorandClient
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
    TransactionComposerConfig,
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
    created_asset = algorand.client.algod.asset_by_id(asset_id).params
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
    updated_asset = algorand.client.algod.asset_by_id(asset_id).params
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
    assert txn.application_call
    assert txn.sender == funded_account.addr
    assert txn.application_call.approval_program
    assert txn.application_call.clear_state_program
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
    assert built.transactions[0].application_call
    response = composer.send({"max_rounds_to_wait": 20})
    assert response.returns[-1].value == "Hello, world"


_SINGLE_ARRAY = abi.ABIType.from_string("uint8[]").encode([1])
_TWO_ARRAYS = abi.ABIType.from_string("(uint8[],uint8[])").encode(([1], [1]))
_THREE_ARRAYS = abi.ABIType.from_string("(uint8[],uint8[],uint8[])").encode(([1], [1], [1]))


@pytest.mark.parametrize(
    ("num_abi_args", "expected_txn_args", "expected_last_arg"),
    [
        (1, 2, _SINGLE_ARRAY),
        (13, 14, _SINGLE_ARRAY),
        (14, 15, _SINGLE_ARRAY),
        (15, 16, _SINGLE_ARRAY),
        (16, 16, _TWO_ARRAYS),
        (17, 16, _THREE_ARRAYS),
    ],
)
def test_add_app_call_with_tuple_packing(
    algorand: AlgorandClient,
    funded_account: AddressWithSigners,
    num_abi_args: int,
    expected_txn_args: int,
    expected_last_arg: bytes,
) -> None:
    args_str = ",".join(["uint8[]"] * num_abi_args)
    method = arc56.Method.from_signature(f"args{num_abi_args}({args_str})void")
    app_call = algorand.create_transaction.app_call_method_call(
        AppCallMethodCallParams(
            sender=funded_account.addr,
            app_id=1234,
            method=method,
            args=[[1]] * num_abi_args,
        )
    )
    txn = app_call.transactions[0]
    assert txn.application_call is not None
    args = txn.application_call.args or []
    assert len(args) == expected_txn_args
    assert args[0] == method.selector
    assert args[-1] == expected_last_arg


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
    assert response.confirmation.txn.txn.fee == AlgoAmount.from_micro_algo(1000)


def test_transaction_fee_is_overridable(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    response = algorand.send.payment(
        PaymentParams(**_get_test_transaction(funded_account), static_fee=AlgoAmount.from_algo(1))
    )
    assert response.confirmation.txn.txn.fee == AlgoAmount.from_algo(1)


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
    assert response.confirmations[0].txn.txn.group == group_bytes
    assert response.confirmations[1].txn.txn.group == group_bytes
    assert response.confirmations[0].txn.txn.group == base64.b64decode(expected_group.encode())


def test_multisig_single_account(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    multisig = algorand.account.multisig(
        metadata=MultisigMetadata(
            version=1,
            threshold=1,
            addrs=[funded_account.addr],
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
            addrs=[funded_account.addr, account2.addr],
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


def test_validation_occurs_on_send(algorand: AlgorandClient, funded_account: AddressWithSigners) -> None:
    params = AssetDestroyParams(asset_id=0, sender=funded_account.addr)
    with pytest.raises(
        TransactionValidationError,
        match="Asset config validation failed: Total is required",
    ):
        algorand.send.asset_destroy(params)


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


def test_send_without_params_respects_composer_config(
    algorand: AlgorandClient, funded_account: AddressWithSigners
) -> None:
    """Test that send() without params respects the composer's config settings.

    This test verifies that calling send() without explicit params doesn't override
    the composer's configured populate_app_call_resources and cover_app_call_inner_transaction_fees
    settings. We verify this by using a mock to track whether simulate_transactions is called
    when building app call transactions - it should only be called if resource population is enabled.
    """
    approval_program = "#pragma version 6\nint 1"
    clear_state_program = "#pragma version 6\nint 1"

    # First, create an app to call
    create_result = algorand.send.app_create(
        AppCreateParams(
            sender=funded_account.addr,
            approval_program=approval_program,
            clear_state_program=clear_state_program,
            schema={"global_ints": 0, "global_byte_slices": 0, "local_ints": 0, "local_byte_slices": 0},
        )
    )
    app_id = create_result.app_id

    # Create a composer with populate_app_call_resources=False
    composer = TransactionComposer(
        TransactionComposerParams(
            algod=algorand.client.algod,
            get_signer=lambda addr: algorand.account.get_signer(addr),
            composer_config=TransactionComposerConfig(populate_app_call_resources=False),
        )
    )

    from algokit_utils.transactions.transaction_composer import AppCallParams

    composer.add_app_call(
        AppCallParams(
            sender=funded_account.addr,
            app_id=app_id,
        )
    )

    # Patch simulate_transactions to track calls
    with patch.object(
        algorand.client.algod, "simulate_transactions", side_effect=algorand.client.algod.simulate_transactions
    ) as patched:
        # Send without params - since populate_app_call_resources=False,
        # simulate should NOT be called during build
        composer.send()

    # simulate_transactions should not have been called because
    # populate_app_call_resources=False was respected
    assert patched.call_count == 0, (
        f"simulate_transactions was called {patched.call_count} times, "
        "but should not be called when populate_app_call_resources=False"
    )


class TestGatherSignatures:
    """Tests for the gather_signatures method."""

    def test_should_successfully_sign_a_single_transaction(
        self, algorand: AlgorandClient, funded_account: AddressWithSigners
    ) -> None:
        """Test that a single transaction is signed successfully."""
        composer = algorand.new_group()
        composer.add_payment(
            PaymentParams(
                sender=funded_account.addr,
                receiver=funded_account.addr,
                amount=AlgoAmount.from_micro_algo(1000),
            )
        )

        signed_txns = composer.gather_signatures()

        assert len(signed_txns) == 1
        assert signed_txns[0] is not None
        assert signed_txns[0].sig is not None

    def test_should_successfully_sign_multiple_transactions_with_same_signer(
        self, algorand: AlgorandClient, funded_account: AddressWithSigners
    ) -> None:
        """Test that multiple transactions from the same sender are signed correctly."""
        composer = algorand.new_group()
        composer.add_payment(
            PaymentParams(
                sender=funded_account.addr,
                receiver=funded_account.addr,
                amount=AlgoAmount.from_micro_algo(1000),
            )
        )
        composer.add_payment(
            PaymentParams(
                sender=funded_account.addr,
                receiver=funded_account.addr,
                amount=AlgoAmount.from_micro_algo(2000),
            )
        )

        signed_txns = composer.gather_signatures()

        assert len(signed_txns) == 2
        assert signed_txns[0].sig is not None
        assert signed_txns[1].sig is not None

    def test_should_successfully_sign_transactions_with_multiple_different_signers(
        self, algorand: AlgorandClient, funded_account: AddressWithSigners
    ) -> None:
        """Test that transactions from different senders are each signed correctly."""
        # Create and fund a second account
        sender2 = algorand.account.random()
        algorand.send.payment(
            PaymentParams(
                sender=funded_account.addr,
                receiver=sender2.addr,
                amount=AlgoAmount.from_algo(10),
            )
        )

        composer = algorand.new_group()
        composer.add_payment(
            PaymentParams(
                sender=funded_account.addr,
                receiver=sender2.addr,
                amount=AlgoAmount.from_micro_algo(1000),
            )
        )
        composer.add_payment(
            PaymentParams(
                sender=sender2.addr,
                receiver=funded_account.addr,
                amount=AlgoAmount.from_micro_algo(1000),
                signer=sender2.signer,
            )
        )

        signed_txns = composer.gather_signatures()

        assert len(signed_txns) == 2
        assert signed_txns[0].sig is not None
        assert signed_txns[1].sig is not None

    def test_should_throw_error_when_no_transactions_to_sign(self, algorand: AlgorandClient) -> None:
        """Test that an error is thrown when there are no transactions to sign."""
        composer = algorand.new_group()

        with pytest.raises(ValueError, match="Cannot build an empty transaction group"):
            composer.gather_signatures()

    def test_should_throw_error_when_signer_returns_fewer_signed_transactions_than_expected(
        self, algorand: AlgorandClient, funded_account: AddressWithSigners
    ) -> None:
        """Test error handling when a signer returns fewer signed transactions than requested."""
        from collections.abc import Sequence

        from algokit_transact.models.transaction import Transaction

        real_signer = algorand.account.get_signer(funded_account.addr)

        # Create a faulty signer that returns fewer signed transactions than requested
        def faulty_signer(txns: Sequence[Transaction], indexes: Sequence[int]) -> list[bytes]:
            # Only return one signed transaction even if multiple are requested
            return real_signer(txns, [indexes[0]])

        composer = algorand.new_group()
        composer.add_payment(
            PaymentParams(
                sender=funded_account.addr,
                receiver=funded_account.addr,
                amount=AlgoAmount.from_micro_algo(1000),
                signer=faulty_signer,
            )
        )
        composer.add_payment(
            PaymentParams(
                sender=funded_account.addr,
                receiver=funded_account.addr,
                amount=AlgoAmount.from_micro_algo(2000),
                signer=faulty_signer,
            )
        )

        with pytest.raises(ValueError, match=r"Transactions at indexes \[1\] were not signed"):
            composer.gather_signatures()

    def test_should_throw_error_when_signer_returns_none_signed_transaction(
        self, algorand: AlgorandClient, funded_account: AddressWithSigners
    ) -> None:
        """Test error handling when a signer returns None values."""
        from collections.abc import Sequence

        from algokit_transact.models.transaction import Transaction

        # Create a faulty signer that returns array of Nones
        def faulty_signer(_txns: Sequence[Transaction], indexes: Sequence[int]) -> list[bytes]:
            return [None] * len(indexes)  # type: ignore[list-item]

        composer = algorand.new_group()
        composer.add_payment(
            PaymentParams(
                sender=funded_account.addr,
                receiver=funded_account.addr,
                amount=AlgoAmount.from_micro_algo(1000),
                signer=faulty_signer,
            )
        )

        # Should provide a clear error message indicating which transaction was not signed
        with pytest.raises(ValueError, match=r"Transactions at indexes \[0\] were not signed"):
            composer.gather_signatures()

    def test_should_throw_error_when_signer_returns_empty_array(
        self, algorand: AlgorandClient, funded_account: AddressWithSigners
    ) -> None:
        """Test error handling when a signer returns an empty array."""
        from collections.abc import Sequence

        from algokit_transact.models.transaction import Transaction

        # Create a faulty signer that returns empty array
        def faulty_signer(_txns: Sequence[Transaction], _indexes: Sequence[int]) -> list[bytes]:
            return []

        composer = algorand.new_group()
        composer.add_payment(
            PaymentParams(
                sender=funded_account.addr,
                receiver=funded_account.addr,
                amount=AlgoAmount.from_micro_algo(1000),
                signer=faulty_signer,
            )
        )

        with pytest.raises(ValueError, match=r"Transactions at indexes \[0\] were not signed"):
            composer.gather_signatures()

    def test_should_throw_error_when_signer_returns_invalid_signed_transaction_data(
        self, algorand: AlgorandClient, funded_account: AddressWithSigners
    ) -> None:
        """Test error handling when a signer returns malformed signed transaction data."""
        from collections.abc import Sequence

        from algokit_transact.models.transaction import Transaction

        # Create a faulty signer that returns invalid data
        def faulty_signer(_txns: Sequence[Transaction], indexes: Sequence[int]) -> list[bytes]:
            return [bytes([1, 2, 3]) for _ in indexes]

        composer = algorand.new_group()
        composer.add_payment(
            PaymentParams(
                sender=funded_account.addr,
                receiver=funded_account.addr,
                amount=AlgoAmount.from_micro_algo(1000),
                signer=faulty_signer,
            )
        )

        # Should provide a clear error message indicating which transaction had invalid data
        with pytest.raises(ValueError, match="Invalid signed transaction at index 0"):
            composer.gather_signatures()
