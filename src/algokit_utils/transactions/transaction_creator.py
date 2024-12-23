from collections.abc import Callable
from typing import TypeVar

from algosdk.transaction import Transaction

from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCallParams,
    AppCallParams,
    AppCreateMethodCallParams,
    AppCreateParams,
    AppDeleteMethodCallParams,
    AppDeleteParams,
    AppUpdateMethodCallParams,
    AppUpdateParams,
    AssetConfigParams,
    AssetCreateParams,
    AssetDestroyParams,
    AssetFreezeParams,
    AssetOptInParams,
    AssetOptOutParams,
    AssetTransferParams,
    BuiltTransactions,
    OfflineKeyRegistrationParams,
    OnlineKeyRegistrationParams,
    PaymentParams,
    TransactionComposer,
)

__all__ = [
    "AlgorandClientTransactionCreator",
]

TxnParam = TypeVar("TxnParam")
TxnResult = TypeVar("TxnResult")


class AlgorandClientTransactionCreator:
    """A creator for Algorand transactions."""

    def __init__(self, new_group: Callable[[], TransactionComposer]) -> None:
        """
        Creates a new `AlgorandClientTransactionCreator`.

        Args:
            new_group: A lambda that starts a new `TransactionComposer` transaction group
        """
        self._new_group = new_group

    def _transaction(
        self, c: Callable[[TransactionComposer], Callable[[TxnParam], TransactionComposer]]
    ) -> Callable[[TxnParam], Transaction]:
        """Generic method to create a single transaction."""

        def create_transaction(params: TxnParam) -> Transaction:
            composer = self._new_group()
            result = c(composer)(params).build_transactions()
            return result.transactions[-1]

        return create_transaction

    def _transactions(
        self, c: Callable[[TransactionComposer], Callable[[TxnParam], TransactionComposer]]
    ) -> Callable[[TxnParam], BuiltTransactions]:
        """Generic method to create multiple transactions."""

        def create_transactions(params: TxnParam) -> BuiltTransactions:
            composer = self._new_group()
            return c(composer)(params).build_transactions()

        return create_transactions

    @property
    def payment(self) -> Callable[[PaymentParams], Transaction]:
        """Create a payment transaction to transfer Algo between accounts."""
        return self._transaction(lambda c: c.add_payment)

    @property
    def asset_create(self) -> Callable[[AssetCreateParams], Transaction]:
        """Create a create Algorand Standard Asset transaction."""
        return self._transaction(lambda c: c.add_asset_create)

    @property
    def asset_config(self) -> Callable[[AssetConfigParams], Transaction]:
        """Create an asset config transaction to reconfigure an existing Algorand Standard Asset."""
        return self._transaction(lambda c: c.add_asset_config)

    @property
    def asset_freeze(self) -> Callable[[AssetFreezeParams], Transaction]:
        """Create an Algorand Standard Asset freeze transaction."""
        return self._transaction(lambda c: c.add_asset_freeze)

    @property
    def asset_destroy(self) -> Callable[[AssetDestroyParams], Transaction]:
        """Create an Algorand Standard Asset destroy transaction."""
        return self._transaction(lambda c: c.add_asset_destroy)

    @property
    def asset_transfer(self) -> Callable[[AssetTransferParams], Transaction]:
        """Create an Algorand Standard Asset transfer transaction."""
        return self._transaction(lambda c: c.add_asset_transfer)

    @property
    def asset_opt_in(self) -> Callable[[AssetOptInParams], Transaction]:
        """Create an Algorand Standard Asset opt-in transaction."""
        return self._transaction(lambda c: c.add_asset_opt_in)

    @property
    def asset_opt_out(self) -> Callable[[AssetOptOutParams], Transaction]:
        """Create an asset opt-out transaction."""
        return self._transaction(lambda c: c.add_asset_opt_out)

    @property
    def app_create(self) -> Callable[[AppCreateParams], Transaction]:
        """Create an application create transaction."""
        return self._transaction(lambda c: c.add_app_create)

    @property
    def app_update(self) -> Callable[[AppUpdateParams], Transaction]:
        """Create an application update transaction."""
        return self._transaction(lambda c: c.add_app_update)

    @property
    def app_delete(self) -> Callable[[AppDeleteParams], Transaction]:
        """Create an application delete transaction."""
        return self._transaction(lambda c: c.add_app_delete)

    @property
    def app_call(self) -> Callable[[AppCallParams], Transaction]:
        """Create an application call transaction."""
        return self._transaction(lambda c: c.add_app_call)

    @property
    def app_create_method_call(self) -> Callable[[AppCreateMethodCallParams], BuiltTransactions]:
        """Create an application create call with ABI method call transaction."""
        return self._transactions(lambda c: c.add_app_create_method_call)

    @property
    def app_update_method_call(self) -> Callable[[AppUpdateMethodCallParams], BuiltTransactions]:
        """Create an application update call with ABI method call transaction."""
        return self._transactions(lambda c: c.add_app_update_method_call)

    @property
    def app_delete_method_call(self) -> Callable[[AppDeleteMethodCallParams], BuiltTransactions]:
        """Create an application delete call with ABI method call transaction."""
        return self._transactions(lambda c: c.add_app_delete_method_call)

    @property
    def app_call_method_call(self) -> Callable[[AppCallMethodCallParams], BuiltTransactions]:
        """Create an application call with ABI method call transaction."""
        return self._transactions(lambda c: c.add_app_call_method_call)

    @property
    def online_key_registration(self) -> Callable[[OnlineKeyRegistrationParams], Transaction]:
        """Create an online key registration transaction."""
        return self._transaction(lambda c: c.add_online_key_registration)

    @property
    def offline_key_registration(self) -> Callable[[OfflineKeyRegistrationParams], Transaction]:
        """Create an offline key registration transaction."""
        return self._transaction(lambda c: c.add_offline_key_registration)
