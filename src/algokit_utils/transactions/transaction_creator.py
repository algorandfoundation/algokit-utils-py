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
    """A creator for Algorand transactions.

    Provides methods to create various types of Algorand transactions including payments,
    asset operations, application calls and key registrations.

    :param new_group: A lambda that starts a new TransactionComposer transaction group

    :example:
        >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
        >>> creator.payment(PaymentParams(sender="sender", receiver="receiver", amount=AlgoAmount.from_algo(1)))
    """

    def __init__(self, new_group: Callable[[], TransactionComposer]) -> None:
        self._new_group = new_group

    def _transaction(
        self, c: Callable[[TransactionComposer], Callable[[TxnParam], TransactionComposer]]
    ) -> Callable[[TxnParam], Transaction]:
        def create_transaction(params: TxnParam) -> Transaction:
            composer = self._new_group()
            result = c(composer)(params).build_transactions()
            return result.transactions[-1]

        return create_transaction

    def _transactions(
        self, c: Callable[[TransactionComposer], Callable[[TxnParam], TransactionComposer]]
    ) -> Callable[[TxnParam], BuiltTransactions]:
        def create_transactions(params: TxnParam) -> BuiltTransactions:
            composer = self._new_group()
            return c(composer)(params).build_transactions()

        return create_transactions

    @property
    def payment(self) -> Callable[[PaymentParams], Transaction]:
        """Create a payment transaction to transfer Algo between accounts.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> creator.payment(PaymentParams(sender="sender", receiver="receiver", amount=AlgoAmount.from_algo(4)))
        :example:
            >>> #Advanced example
            >>> creator.payment(PaymentParams(
                    sender="SENDERADDRESS",
                    receiver="RECEIVERADDRESS",
                    amount=AlgoAmount.from_algo(4),
                    close_remainder_to="CLOSEREMAINDERTOADDRESS",
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
                ))
        """
        return self._transaction(lambda c: c.add_payment)

    @property
    def asset_create(self) -> Callable[[AssetCreateParams], Transaction]:
        """Create a create Algorand Standard Asset transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AssetCreateParams(sender="SENDER_ADDRESS", total=1000)
            >>> txn = creator.asset_create(params)
        :example:
            >>> #Advanced example
            >>> creator.asset_create(AssetCreateParams(
                    sender="SENDER_ADDRESS",
                    total=1000,
                    asset_name="MyAsset",
                    unit_name="MA",
                    url="https://example.com/asset",
                    decimals=0,
                    default_frozen=False,
                    manager="MANAGER_ADDRESS",
                    reserve="RESERVE_ADDRESS",
                    freeze="FREEZE_ADDRESS",
                    clawback="CLAWBACK_ADDRESS",
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_asset_create)

    @property
    def asset_config(self) -> Callable[[AssetConfigParams], Transaction]:
        """Create an asset config transaction to reconfigure an existing Algorand Standard Asset.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AssetConfigParams(sender="SENDER_ADDRESS", asset_id=123456, manager="NEW_MANAGER_ADDRESS")
            >>> txn = creator.asset_config(params)
        :example:
            >>> #Advanced example
            >>> creator.asset_config(AssetConfigParams(
                    sender="SENDER_ADDRESS",
                    asset_id=123456,
                    manager="NEW_MANAGER_ADDRESS",
                    reserve="NEW_RESERVE_ADDRESS",
                    freeze="NEW_FREEZE_ADDRESS",
                    clawback="NEW_CLAWBACK_ADDRESS",
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_asset_config)

    @property
    def asset_freeze(self) -> Callable[[AssetFreezeParams], Transaction]:
        """Create an Algorand Standard Asset freeze transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AssetFreezeParams(sender="SENDER_ADDRESS",
                asset_id=123456,
                account="ACCOUNT_TO_FREEZE",
                frozen=True)
            >>> txn = creator.asset_freeze(params)

        :example:
            >>> #Advanced example
            >>> creator.asset_freeze(AssetFreezeParams(
                    sender="SENDER_ADDRESS",
                    asset_id=123456,
                    account="ACCOUNT_TO_FREEZE",
                    frozen=True,
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_asset_freeze)

    @property
    def asset_destroy(self) -> Callable[[AssetDestroyParams], Transaction]:
        """Create an Algorand Standard Asset destroy transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AssetDestroyParams(sender="SENDER_ADDRESS", asset_id=123456)
            >>> txn = creator.asset_destroy(params)

        :example:
            >>> #Advanced example
            >>> creator.asset_destroy(AssetDestroyParams(
                    sender="SENDER_ADDRESS",
                    asset_id=123456,
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_asset_destroy)

    @property
    def asset_transfer(self) -> Callable[[AssetTransferParams], Transaction]:
        """Create an Algorand Standard Asset transfer transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AssetTransferParams(sender="SENDER_ADDRESS",
                asset_id=123456,
                amount=10,
                receiver="RECEIVER_ADDRESS")
            >>> txn = creator.asset_transfer(params)

        :example:
            >>> #Advanced example
            >>> creator.asset_transfer(AssetTransferParams(
                    sender="SENDER_ADDRESS",
                    asset_id=123456,
                    amount=10,
                    receiver="RECEIVER_ADDRESS",
                    clawback_target="CLAWBACK_TARGET_ADDRESS",
                    close_asset_to="CLOSE_ASSET_TO_ADDRESS",
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_asset_transfer)

    @property
    def asset_opt_in(self) -> Callable[[AssetOptInParams], Transaction]:
        """Create an Algorand Standard Asset opt-in transaction.

        :example:
            >>> # Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AssetOptInParams(sender="SENDER_ADDRESS", asset_id=123456)
            >>> txn = creator.asset_opt_in(params)

        :example:
            >>> # Advanced example
            >>> creator.asset_opt_in(AssetOptInParams(
                    sender="SENDER_ADDRESS",
                    asset_id=123456,
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_asset_opt_in)

    @property
    def asset_opt_out(self) -> Callable[[AssetOptOutParams], Transaction]:
        """Create an asset opt-out transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AssetOptOutParams(sender="SENDER_ADDRESS", asset_id=123456, creator="CREATOR_ADDRESS")
            >>> txn = creator.asset_opt_out(params)

        :example:
            >>> #Advanced example
            >>> creator.asset_opt_out(AssetOptOutParams(
                    sender="SENDER_ADDRESS",
                    asset_id=123456,
                    creator="CREATOR_ADDRESS",
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_asset_opt_out)

    @property
    def app_create(self) -> Callable[[AppCreateParams], Transaction]:
        """Create an application create transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AppCreateParams(
            ...     sender="SENDER_ADDRESS",
            ...     approval_program="TEAL_APPROVAL_CODE",
            ...     clear_state_program="TEAL_CLEAR_CODE",
            ...     schema={
            ...         'global_ints': 1,
            ...         'global_byte_slices': 1,
            ...         'local_ints': 1,
            ...         'local_byte_slices': 1
            ...     }
            ... )
            >>> txn = creator.app_create(params)

        :example:
            >>> #Advanced example
            >>> creator.app_create(AppCreateParams(
                    sender="SENDER_ADDRESS",
                    approval_program="TEAL_APPROVAL_CODE",
                    clear_state_program="TEAL_CLEAR_CODE",
                    schema={'global_ints': 1, 'global_byte_slices': 1, 'local_ints': 1, 'local_byte_slices': 1},
                    on_complete=OnComplete.NoOpOC,
                    args=[b'arg1', b'arg2'],
                    account_references=["ACCOUNT1"],
                    app_references=[789],
                    asset_references=[123],
                    box_references=[],
                    extra_program_pages=0,
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_app_create)

    @property
    def app_update(self) -> Callable[[AppUpdateParams], Transaction]:
        """Create an application update transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> txn = creator.app_update(AppUpdateParams(sender="SENDER_ADDRESS",
                app_id=789,
                approval_program="TEAL_NEW_APPROVAL_CODE",
                clear_state_program="TEAL_NEW_CLEAR_CODE",
                args=[b'new_arg1', b'new_arg2']))

        :example:
            >>> #Advanced example
            >>> creator.app_update(AppUpdateParams(
                    sender="SENDER_ADDRESS",
                    app_id=789,
                    approval_program="TEAL_NEW_APPROVAL_CODE",
                    clear_state_program="TEAL_NEW_CLEAR_CODE",
                    args=[b'new_arg1', b'new_arg2'],
                    account_references=["ACCOUNT1"],
                    app_references=[789],
                    asset_references=[123],
                    box_references=[],
                    on_complete=OnComplete.UpdateApplicationOC,
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_app_update)

    @property
    def app_delete(self) -> Callable[[AppDeleteParams], Transaction]:
        """Create an application delete transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AppDeleteParams(sender="SENDER_ADDRESS", app_id=789, args=[b'delete_arg'])
            >>> txn = creator.app_delete(params)

        :example:
            >>> #Advanced example
            >>> creator.app_delete(AppDeleteParams(
                    sender="SENDER_ADDRESS",
                    app_id=789,
                    args=[b'delete_arg'],
                    account_references=["ACCOUNT1"],
                    app_references=[789],
                    asset_references=[123],
                    box_references=[],
                    on_complete=OnComplete.DeleteApplicationOC,
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_app_delete)

    @property
    def app_call(self) -> Callable[[AppCallParams], Transaction]:
        """Create an application call transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AppCallParams(
            ...     sender="SENDER_ADDRESS",
            ...     on_complete=OnComplete.NoOpOC,
            ...     app_id=789,
            ...     approval_program="TEAL_APPROVAL_CODE",
            ...     clear_state_program="TEAL_CLEAR_CODE",
            ...     schema={
            ...         'global_ints': 1,
            ...         'global_byte_slices': 1,
            ...         'local_ints': 1,
            ...         'local_byte_slices': 1
            ...     },
            ...     args=[b'arg1', b'arg2'],
            ...     account_references=["ACCOUNT1"],
            ...     app_references=[789],
            ...     asset_references=[123],
            ...     extra_pages=0,
            ...     box_references=[]
            ... )
            >>> txn = creator.app_call(params)

        :example:
            >>> #Advanced example
            >>> creator.app_call(AppCallParams(
                    sender="SENDER_ADDRESS",
                    on_complete=OnComplete.NoOpOC,
                    app_id=789,
                    approval_program="TEAL_APPROVAL_CODE",
                    clear_state_program="TEAL_CLEAR_CODE",
                    schema={'global_ints': 1, 'global_byte_slices': 1, 'local_ints': 1, 'local_byte_slices': 1},
                    args=[b'arg1', b'arg2'],
                    account_references=["ACCOUNT1"],
                    app_references=[789],
                    asset_references=[123],
                    extra_pages=0,
                    box_references=[],
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_app_call)

    @property
    def app_create_method_call(self) -> Callable[[AppCreateMethodCallParams], BuiltTransactions]:
        """Create an application create call with ABI method call transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AppCreateMethodCallParams(sender="SENDER_ADDRESS", app_id=0, method=some_abi_method_object)
            >>> built_txns = creator.app_create_method_call(params)

        :example:
            >>> #Advanced example
            >>> creator.app_create_method_call(AppCreateMethodCallParams(
                    sender="SENDER_ADDRESS",
                    app_id=0,
                    method=some_abi_method_object,
                    args=[b'method_arg'],
                    account_references=["ACCOUNT1"],
                    app_references=[789],
                    asset_references=[123],
                    box_references=[],
                    schema={'global_ints': 1, 'global_byte_slices': 1, 'local_ints': 1, 'local_byte_slices': 1},
                    approval_program="TEAL_APPROVAL_CODE",
                    clear_state_program="TEAL_CLEAR_CODE",
                    on_complete=OnComplete.NoOpOC,
                    extra_program_pages=0,
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transactions(lambda c: c.add_app_create_method_call)

    @property
    def app_update_method_call(self) -> Callable[[AppUpdateMethodCallParams], BuiltTransactions]:
        """Create an application update call with ABI method call transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AppUpdateMethodCallParams(sender="SENDER_ADDRESS", app_id=789, method=some_abi_method_object)
            >>> built_txns = creator.app_update_method_call(params)

        :example:
            >>> #Advanced example
            >>> creator.app_update_method_call(AppUpdateMethodCallParams(
                    sender="SENDER_ADDRESS",
                    app_id=789,
                    method=some_abi_method_object,
                    args=[b'method_arg'],
                    account_references=["ACCOUNT1"],
                    app_references=[789],
                    asset_references=[123],
                    box_references=[],
                    schema={'global_ints': 1, 'global_byte_slices': 1, 'local_ints': 1, 'local_byte_slices': 1},
                    approval_program="TEAL_NEW_APPROVAL_CODE",
                    clear_state_program="TEAL_NEW_CLEAR_CODE",
                    on_complete=OnComplete.UpdateApplicationOC,
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transactions(lambda c: c.add_app_update_method_call)

    @property
    def app_delete_method_call(self) -> Callable[[AppDeleteMethodCallParams], BuiltTransactions]:
        """Create an application delete call with ABI method call transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AppDeleteMethodCallParams(sender="SENDER_ADDRESS", app_id=789, method=some_abi_method_object)
            >>> built_txns = creator.app_delete_method_call(params)

        :example:
            >>> #Advanced example
            >>> creator.app_delete_method_call(AppDeleteMethodCallParams(
                    sender="SENDER_ADDRESS",
                    app_id=789,
                    method=some_abi_method_object,
                    args=[b'method_arg'],
                    account_references=["ACCOUNT1"],
                    app_references=[789],
                    asset_references=[123],
                    box_references=[],
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transactions(lambda c: c.add_app_delete_method_call)

    @property
    def app_call_method_call(self) -> Callable[[AppCallMethodCallParams], BuiltTransactions]:
        """Create an application call with ABI method call transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = AppCallMethodCallParams(sender="SENDER_ADDRESS", app_id=789, method=some_abi_method_object)
            >>> built_txns = creator.app_call_method_call(params)
        :example: Advanced example
            >>> creator.app_call_method_call(AppCallMethodCallParams(
                    sender="SENDER_ADDRESS",
                    app_id=789,
                    method=some_abi_method_object,
                    args=[b'method_arg'],
                    account_references=["ACCOUNT1"],
                    app_references=[789],
                    asset_references=[123],
                    box_references=[],
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transactions(lambda c: c.add_app_call_method_call)

    @property
    def online_key_registration(self) -> Callable[[OnlineKeyRegistrationParams], Transaction]:
        """Create an online key registration transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> params = OnlineKeyRegistrationParams(
                    sender="SENDER_ADDRESS",
                    vote_key="VOTE_KEY",
                    selection_key="SELECTION_KEY",
                    vote_first=1000,
                    vote_last=2000,
                    vote_key_dilution=10,
                    state_proof_key=b"state_proof_key_bytes"
            )
            >>> txn = creator.online_key_registration(params)

        :example:
            >>> #Advanced example
            >>> creator.online_key_registration(OnlineKeyRegistrationParams(
                    sender="SENDER_ADDRESS",
                    vote_key="VOTE_KEY",
                    selection_key="SELECTION_KEY",
                    vote_first=1000,
                    vote_last=2000,
                    vote_key_dilution=10,
                    state_proof_key=b"state_proof_key_bytes",
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_online_key_registration)

    @property
    def offline_key_registration(self) -> Callable[[OfflineKeyRegistrationParams], Transaction]:
        """Create an offline key registration transaction.

        :example:
            >>> #Basic example
            >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
            >>> txn = creator.offline_key_registration(OfflineKeyRegistrationParams(sender="SENDER_ADDRESS",
                prevent_account_from_ever_participating_again=True))

        :example:
            >>> #Advanced example
            >>> creator.offline_key_registration(OfflineKeyRegistrationParams(
                    sender="SENDER_ADDRESS",
                    prevent_account_from_ever_participating_again=True,
                    lease="lease",
                    note=b"note",
                    rekey_to="REKEYTOADDRESS",
                    first_valid_round=1000,
                    validity_window=10,
                    extra_fee=AlgoAmount.from_micro_algo(1000),
                    static_fee=AlgoAmount.from_micro_algo(1000),
                    max_fee=AlgoAmount.from_micro_algo(3000)
            ))
        """
        return self._transaction(lambda c: c.add_offline_key_registration)
