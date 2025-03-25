import base64
import dataclasses
import json
from pathlib import Path

import pytest

from algokit_utils import SigningAccount
from algokit_utils.algorand import AlgorandClient
from algokit_utils.applications.app_client import AppClient, AppClientMethodCallParams, FundAppAccountParams
from algokit_utils.applications.app_factory import AppFactoryCreateMethodCallParams, AppFactoryCreateParams
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import PaymentParams


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> SigningAccount:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(new_account, dispenser, AlgoAmount.from_algo(100))
    return new_account


class TestCoverAppCallInnerFees:
    """Test covering app call inner transaction fees"""

    @pytest.fixture(autouse=True)
    def setup(self, algorand: AlgorandClient, funded_account: SigningAccount) -> None:
        # Load inner fee contract spec
        spec_path = Path(__file__).parent.parent / "artifacts" / "inner-fee" / "application.json"
        inner_fee_spec = json.loads(spec_path.read_text())

        # Create app factory
        factory = algorand.client.get_app_factory(app_spec=inner_fee_spec, default_sender=funded_account.address)

        # Create 3 app instances
        self.app_client1, _ = factory.send.bare.create(params=AppFactoryCreateParams(note=b"app1"))
        self.app_client2, _ = factory.send.bare.create(params=AppFactoryCreateParams(note=b"app2"))
        self.app_client3, _ = factory.send.bare.create(params=AppFactoryCreateParams(note=b"app3"))

        # Fund app accounts
        for client in [self.app_client1, self.app_client2, self.app_client3]:
            client.fund_app_account(FundAppAccountParams(amount=AlgoAmount.from_algo(2)))

    def test_throws_when_no_max_fee(self) -> None:
        """Test that error is thrown when no max fee is supplied"""
        with pytest.raises(ValueError, match="Please provide a `max_fee` for each app call transaction"):
            self.app_client1.send.call(
                AppClientMethodCallParams(
                    method="no_op",
                ),
                send_params={
                    "cover_app_call_inner_transaction_fees": True,
                },
            )

    def test_throws_when_inner_fees_not_covered(self) -> None:
        """Test that error is thrown when inner transaction fees are not covered"""

        expected_fee = 7000
        params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0]]],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )

        with pytest.raises(Exception, match="fee too small"):
            self.app_client1.send.call(
                params,
                send_params={
                    "cover_app_call_inner_transaction_fees": False,
                },
            )

    def test_does_not_alter_fee_without_inners(self) -> None:
        """Test that fee is not altered when app call has no inner transactions"""

        expected_fee = 1000
        params = AppClientMethodCallParams(
            method="no_op",
            max_fee=AlgoAmount.from_micro_algo(2000),
        )
        result = self.app_client1.send.call(
            params,
            send_params={
                "cover_app_call_inner_transaction_fees": True,
            },
        )

        assert result.transaction.raw.fee == expected_fee
        self._assert_min_fee(self.app_client1, params, expected_fee)

    def test_throws_when_max_fee_too_small(self) -> None:
        """Test that error is thrown when max fee is too small to cover inner fees"""

        expected_fee = 7000
        params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0]]],
            max_fee=AlgoAmount.from_micro_algo(expected_fee - 1),
        )

        with pytest.raises(ValueError, match="Fees were too small to resolve execution info"):
            self.app_client1.send.call(
                params,
                send_params={
                    "cover_app_call_inner_transaction_fees": True,
                },
            )

    def test_throws_when_static_fee_too_small_for_inner_fees(self) -> None:
        """Test that error is thrown when static fee is too small for inner transaction fees"""

        expected_fee = 7000
        params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0]]],
            static_fee=AlgoAmount.from_micro_algo(expected_fee - 1),
        )

        with pytest.raises(ValueError, match="Fees were too small to resolve execution info"):
            self.app_client1.send.call(
                params,
                send_params={
                    "cover_app_call_inner_transaction_fees": True,
                },
            )

    def test_alters_fee_handling_when_no_itxns_covered(self) -> None:
        """Test that fee handling is altered when no inner transaction fees are covered"""

        expected_fee = 7000
        params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0]]],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )
        result = self.app_client1.send.call(
            params,
            send_params={
                "cover_app_call_inner_transaction_fees": True,
            },
        )

        assert result.transaction.raw.fee == expected_fee
        self._assert_min_fee(self.app_client1, params, expected_fee)

    def test_alters_fee_handling_when_all_inners_covered(self) -> None:
        """Test that fee handling is altered when all inner transaction fees are covered"""

        expected_fee = 1000
        params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [1000, 1000, 1000, 1000, [1000, 1000]]],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )
        result = self.app_client1.send.call(
            params,
            send_params={
                "cover_app_call_inner_transaction_fees": True,
            },
        )

        assert result.transaction.raw.fee == expected_fee
        self._assert_min_fee(self.app_client1, params, expected_fee)

    def test_alters_fee_handling_when_some_inners_covered(self) -> None:
        """Test that fee handling is altered when some inner transaction fees are covered"""

        expected_fee = 5300
        params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [1000, 0, 200, 0, [500, 0]]],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )
        result = self.app_client1.send.call(
            params,
            send_params={
                "cover_app_call_inner_transaction_fees": True,
            },
        )

        assert result.transaction.raw.fee == expected_fee
        self._assert_min_fee(self.app_client1, params, expected_fee)

    def test_alters_fee_when_some_inners_have_surplus(self) -> None:
        """Test that fee handling is altered when some inner transaction fees are covered"""

        expected_fee = 2000
        params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 1000, 5000, 0, [0, 50]]],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )
        result = self.app_client1.send.call(
            params,
            send_params={
                "cover_app_call_inner_transaction_fees": True,
            },
        )
        assert result.transaction.raw.fee == expected_fee
        self._assert_min_fee(self.app_client1, params, expected_fee)

    def test_alters_handling_multiple_app_calls_in_group_with_inners_with_varying_fees(self) -> None:
        """Test that fee handling is altered when multiple app calls are in a group with inners with varying fees"""
        txn_1_expected_fee = 5800
        txn_2_expected_fee = 6000

        txn_1_params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 1000, 0, 0, [200, 0]]],
            static_fee=AlgoAmount.from_micro_algo(txn_1_expected_fee),
            note=b"txn_1",
        )

        txn_2_params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [1000, 0, 0, 0, [0, 0]]],
            max_fee=AlgoAmount.from_micro_algo(txn_2_expected_fee),
            note=b"txn_2",
        )

        result = (
            self.app_client1.algorand.new_group()
            .add_app_call_method_call(self.app_client1.params.call(txn_1_params))
            .add_app_call_method_call(self.app_client1.params.call(txn_2_params))
            .send({"cover_app_call_inner_transaction_fees": True})
        )

        assert result.transactions[0].raw.fee == txn_1_expected_fee
        self._assert_min_fee(self.app_client1, txn_1_params, txn_1_expected_fee)
        assert result.transactions[1].raw.fee == txn_2_expected_fee
        self._assert_min_fee(self.app_client1, txn_2_params, txn_2_expected_fee)

    def test_does_not_alter_static_fee_with_surplus(self) -> None:
        """Test that a static fee with surplus is not altered"""

        expected_fee = 6000
        params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [1000, 0, 200, 0, [500, 0]]],
            static_fee=AlgoAmount.from_micro_algo(expected_fee),
        )
        result = self.app_client1.send.call(
            params,
            send_params={
                "cover_app_call_inner_transaction_fees": True,
            },
        )

        assert result.transaction.raw.fee == expected_fee

    def test_alters_fee_with_large_inner_surplus_pooling(self) -> None:
        """Test fee handling with large inner fee surplus pooling to lower siblings"""

        expected_fee = 7000
        params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0, 20_000, 0, 0, 0]]],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )
        result = self.app_client1.send.call(
            params,
            send_params={
                "cover_app_call_inner_transaction_fees": True,
            },
        )

        assert result.transaction.raw.fee == expected_fee
        self._assert_min_fee(self.app_client1, params, expected_fee)

    def test_alters_fee_with_partial_inner_surplus_pooling(self) -> None:
        """Test fee handling with inner fee surplus pooling to some lower siblings"""

        expected_fee = 6300
        params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 2200, 0, [0, 0, 2500, 0, 0, 0]]],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )
        result = self.app_client1.send.call(
            params,
            send_params={
                "cover_app_call_inner_transaction_fees": True,
            },
        )

        assert result.transaction.raw.fee == expected_fee
        self._assert_min_fee(self.app_client1, params, expected_fee)

    def test_alters_fee_with_large_inner_surplus_no_pooling(self) -> None:
        """Test fee handling with large inner fee surplus but no pooling"""

        expected_fee = 10_000
        params = AppClientMethodCallParams(
            method="send_inners_with_fees",
            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0, 0, 0, 0, 20_000]]],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )
        result = self.app_client1.send.call(
            params,
            send_params={
                "cover_app_call_inner_transaction_fees": True,
            },
        )

        assert result.transaction.raw.fee == expected_fee
        self._assert_min_fee(self.app_client1, params, expected_fee)

    def test_alters_fee_with_multiple_inner_surplus_poolings_to_lower_siblings(self) -> None:
        """Test fee handling with multiple inner fee surplus poolings to lower siblings"""

        expected_fee = 7100
        params = AppClientMethodCallParams(
            method="send_inners_with_fees_2",
            args=[
                self.app_client2.app_id,
                self.app_client3.app_id,
                [0, 1200, [0, 0, 4900, 0, 0, 0], 200, 1100, [0, 0, 2500, 0, 0, 0]],
            ],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )
        result = self.app_client1.send.call(params, send_params={"cover_app_call_inner_transaction_fees": True})

        assert result.transaction.raw.fee == expected_fee
        self._assert_min_fee(self.app_client1, params, expected_fee)

    def test_does_not_alter_fee_when_group_covers_inner_fees(self, funded_account: SigningAccount) -> None:
        """Test that fee is not altered when another transaction in group covers inner fees"""

        expected_fee = 8000

        result = (
            self.app_client1.algorand.new_group()
            .add_payment(
                params=PaymentParams(
                    sender=funded_account.address,
                    receiver=funded_account.address,
                    amount=AlgoAmount.from_micro_algo(0),
                    static_fee=AlgoAmount.from_micro_algo(expected_fee),
                )
            )
            .add_app_call_method_call(
                self.app_client1.params.call(
                    AppClientMethodCallParams(
                        method="send_inners_with_fees",
                        args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0]]],
                        max_fee=AlgoAmount.from_micro_algo(expected_fee),
                    )
                )
            )
            .send({"cover_app_call_inner_transaction_fees": True})
        )

        assert result.transactions[0].raw.fee == expected_fee
        # We could technically reduce the below to 0, however it adds more complexity
        # and is probably unlikely to be a common use case
        assert result.transactions[1].raw.fee == 1000

    def test_allocates_surplus_fees_to_most_constrained_first(self, funded_account: SigningAccount) -> None:
        """Test that surplus fees are allocated to the most fee constrained transaction first"""

        result = (
            self.app_client1.algorand.new_group()
            .add_app_call_method_call(
                self.app_client1.params.call(
                    AppClientMethodCallParams(
                        method="send_inners_with_fees",
                        args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0]]],
                        max_fee=AlgoAmount.from_micro_algo(2000),
                    )
                )
            )
            .add_payment(
                params=PaymentParams(
                    sender=funded_account.address,
                    receiver=funded_account.address,
                    amount=AlgoAmount.from_micro_algo(0),
                    static_fee=AlgoAmount.from_micro_algo(7500),
                )
            )
            .add_payment(
                params=PaymentParams(
                    sender=funded_account.address,
                    receiver=funded_account.address,
                    amount=AlgoAmount.from_micro_algo(0),
                    static_fee=AlgoAmount.from_micro_algo(0),
                )
            )
            .send({"cover_app_call_inner_transaction_fees": True})
        )

        assert result.transactions[0].raw.fee == 1500
        assert result.transactions[1].raw.fee == 7500
        assert result.transactions[2].raw.fee == 0
        assert result.group_id != ""
        for txn in result.transactions:
            assert txn.raw.group is not None
            assert base64.b64encode(txn.raw.group).decode("utf-8") == result.group_id

    def test_handles_nested_abi_method_calls(self, funded_account: SigningAccount) -> None:
        """Test fee handling with nested ABI method calls"""

        # Create nested contract app
        app_spec = (Path(__file__).parent.parent / "artifacts" / "nested_contract" / "application.json").read_text()
        nested_factory = self.app_client1.algorand.client.get_app_factory(
            app_spec=app_spec,
            default_sender=funded_account.address,
        )
        nested_client, _ = nested_factory.send.create(
            params=AppFactoryCreateMethodCallParams(method="createApplication")
        )

        # Setup transaction parameters
        txn_arg_call = self.app_client1.params.call(
            AppClientMethodCallParams(
                method="send_inners_with_fees",
                args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 2000, 0, [0, 0]]],
                max_fee=AlgoAmount.from_micro_algo(4000),
            )
        )

        payment_params = PaymentParams(
            sender=funded_account.address,
            receiver=funded_account.address,
            amount=AlgoAmount.from_micro_algo(0),
            static_fee=AlgoAmount.from_micro_algo(1500),
        )

        expected_fee = 2000
        params = AppClientMethodCallParams(
            method="nestedTxnArg",
            args=[
                self.app_client1.algorand.create_transaction.payment(payment_params),
                txn_arg_call,
            ],
            static_fee=AlgoAmount.from_micro_algo(expected_fee),
        )
        result = nested_client.send.call(params, send_params={"cover_app_call_inner_transaction_fees": True})

        assert len(result.transactions) == 3
        assert result.transactions[0].raw.fee == 1500
        assert result.transactions[1].raw.fee == 3500
        assert result.transactions[2].raw.fee == expected_fee

        self._assert_min_fee(
            nested_client,
            dataclasses.replace(
                params,
                args=[self.app_client1.algorand.create_transaction.payment(payment_params), txn_arg_call],
            ),
            expected_fee,
        )

    def test_throws_when_max_fee_below_calculated(self) -> None:
        """Test that error is thrown when max fee is below calculated fee"""

        with pytest.raises(
            ValueError, match="Calculated transaction fee 7000 µALGO is greater than max of 1200 for transaction 0"
        ):
            (
                self.app_client1.algorand.new_group()
                .add_app_call_method_call(
                    self.app_client1.params.call(
                        AppClientMethodCallParams(
                            method="send_inners_with_fees",
                            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0]]],
                            max_fee=AlgoAmount.from_micro_algo(1200),
                        )
                    )
                )
                # This transaction allows this state to be possible, without it the simulate call
                # to get the execution info would fail
                .add_app_call_method_call(
                    self.app_client1.params.call(
                        AppClientMethodCallParams(
                            method="no_op",
                            max_fee=AlgoAmount.from_micro_algo(10_000),
                        )
                    )
                )
                .send({"cover_app_call_inner_transaction_fees": True})
            )

    def test_throws_when_nested_max_fee_below_calculated(self, funded_account: SigningAccount) -> None:
        """Test that error is thrown when nested max fee is below calculated fee"""

        # Create nested contract app
        app_spec = (Path(__file__).parent.parent / "artifacts" / "nested_contract" / "application.json").read_text()
        nested_factory = self.app_client1.algorand.client.get_app_factory(
            app_spec=app_spec,
            default_sender=funded_account.address,
        )
        nested_client, _ = nested_factory.send.create(
            params=AppFactoryCreateMethodCallParams(method="createApplication")
        )

        txn_arg_call = self.app_client1.params.call(
            AppClientMethodCallParams(
                method="send_inners_with_fees",
                args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 2000, 0, [0, 0]]],
                max_fee=AlgoAmount.from_micro_algo(2000),
            )
        )

        with pytest.raises(
            ValueError, match="Calculated transaction fee 5000 µALGO is greater than max of 2000 for transaction 1"
        ):
            nested_client.send.call(
                AppClientMethodCallParams(
                    method="nestedTxnArg",
                    args=[
                        self.app_client1.algorand.create_transaction.payment(
                            PaymentParams(
                                sender=funded_account.address,
                                receiver=funded_account.address,
                                amount=AlgoAmount.from_micro_algo(0),
                            )
                        ),
                        txn_arg_call,
                    ],
                    max_fee=AlgoAmount.from_micro_algo(10_000),
                ),
                send_params={
                    "cover_app_call_inner_transaction_fees": True,
                },
            )

    def test_throws_when_static_fee_below_calculated(self) -> None:
        """Test that error is thrown when static fee is below calculated fee"""

        with pytest.raises(
            ValueError, match="Calculated transaction fee 7000 µALGO is greater than max of 5000 for transaction 0"
        ):
            (
                self.app_client1.algorand.new_group()
                .add_app_call_method_call(
                    self.app_client1.params.call(
                        AppClientMethodCallParams(
                            method="send_inners_with_fees",
                            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0]]],
                            static_fee=AlgoAmount.from_micro_algo(5000),
                        )
                    )
                )
                # This transaction allows this state to be possible, without it the simulate call
                # to get the execution info would fail
                .add_app_call_method_call(
                    self.app_client1.params.call(
                        AppClientMethodCallParams(
                            method="no_op",
                            max_fee=AlgoAmount.from_micro_algo(10_000),
                        )
                    )
                )
                .send({"cover_app_call_inner_transaction_fees": True})
            )

    def test_throws_when_non_app_call_static_fee_too_low(self, funded_account: SigningAccount) -> None:
        """Test that error is thrown when static fee for non-app-call transaction is too low"""

        with pytest.raises(
            ValueError, match="An additional fee of 500 µALGO is required for non app call transaction 2"
        ):
            (
                self.app_client1.algorand.new_group()
                .add_app_call_method_call(
                    self.app_client1.params.call(
                        AppClientMethodCallParams(
                            method="send_inners_with_fees",
                            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0]]],
                            static_fee=AlgoAmount.from_micro_algo(13_000),
                            max_fee=AlgoAmount.from_micro_algo(14_000),
                        )
                    )
                )
                .add_app_call_method_call(
                    self.app_client1.params.call(
                        AppClientMethodCallParams(
                            method="send_inners_with_fees",
                            args=[self.app_client2.app_id, self.app_client3.app_id, [0, 0, 0, 0, [0, 0]]],
                            static_fee=AlgoAmount.from_micro_algo(1000),
                        )
                    )
                )
                .add_payment(
                    params=PaymentParams(
                        sender=funded_account.address,
                        receiver=funded_account.address,
                        amount=AlgoAmount.from_micro_algo(0),
                        static_fee=AlgoAmount.from_micro_algo(500),
                    )
                )
                .send({"cover_app_call_inner_transaction_fees": True})
            )

    def test_handles_expensive_abi_calls_with_ensure_budget(self) -> None:
        """Test fee handling with expensive ABI method calls that use ensure_budget to op-up"""

        expected_fee = 10_000
        params = AppClientMethodCallParams(
            method="burn_ops",
            args=[6200],
            max_fee=AlgoAmount.from_micro_algo(12_000),
        )
        result = self.app_client1.send.call(params, send_params={"cover_app_call_inner_transaction_fees": True})

        assert result.transaction.raw.fee == expected_fee
        assert len(result.confirmation.get("inner-txns", [])) == 9  # type: ignore[union-attr]
        self._assert_min_fee(self.app_client1, params, expected_fee)

    def test_readonly_handles_expensive_abi_calls_with_ensure_budget(self) -> None:
        """Test fee handling with expensive readonly ABI method calls that use ensure_budget to op-up"""

        expected_fee = 12_000
        params = AppClientMethodCallParams(
            method="burn_ops_readonly",
            args=[6200],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )
        result = self.app_client1.send.call(params, send_params={"cover_app_call_inner_transaction_fees": True})

        assert result.transaction.raw.fee == expected_fee
        assert len(result.confirmation.get("inner-txns", [])) == 9  # type: ignore[union-attr]

    def test_readonly_throws_when_no_max_fee(self) -> None:
        """Test that error is thrown when no max fee is supplied for a readonly method call"""
        with pytest.raises(
            ValueError,
            match="Please provide a `max_fee` for the transaction when `cover_app_call_inner_transaction_fees` is enabled",  # noqa: E501
        ):
            self.app_client1.send.call(
                AppClientMethodCallParams(
                    method="burn_ops_readonly",
                    args=[6200],
                ),
                send_params={
                    "cover_app_call_inner_transaction_fees": True,
                },
            )

    def test_readonly_throws_when_inner_fees_not_covered(self) -> None:
        """Test that error is thrown when a readonly method call inner transaction fees are not covered"""

        expected_fee = 7000
        params = AppClientMethodCallParams(
            method="burn_ops_readonly",
            args=[6200],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )

        with pytest.raises(Exception, match="fee too small"):
            self.app_client1.send.call(
                params,
                send_params={
                    "cover_app_call_inner_transaction_fees": False,
                },
            )

    def test_readonly_throws_when_max_fee_too_small(self) -> None:
        """Test that error is thrown when readonly method call max fee is too small to cover inner transaction fees"""

        expected_fee = 7000
        params = AppClientMethodCallParams(
            method="burn_ops_readonly",
            args=[6200],
            max_fee=AlgoAmount.from_micro_algo(expected_fee),
        )

        with pytest.raises(ValueError, match="Fees were too small. You may need to increase the transaction `maxFee`."):
            self.app_client1.send.call(
                params,
                send_params={
                    "cover_app_call_inner_transaction_fees": True,
                },
            )

    def _assert_min_fee(self, app_client: AppClient, params: AppClientMethodCallParams, fee: int) -> None:
        """Helper to assert minimum required fee"""
        if fee == 1000:
            return
        params_copy = dataclasses.replace(
            params,
            static_fee=AlgoAmount.from_micro_algo(fee - 1),
            extra_fee=None,
        )

        with pytest.raises(Exception, match="fee too small"):
            app_client.send.call(params_copy)
