from collections.abc import Callable
from dataclasses import dataclass
from logging import getLogger
from typing import Any, TypedDict

import algosdk
import algosdk.atomic_transaction_composer
from algosdk.atomic_transaction_composer import AtomicTransactionResponse
from algosdk.transaction import Transaction

from algokit_utils.applications.app_manager import AppManager
from algokit_utils.assets.asset_manager import AssetManager
from algokit_utils.models.abi import ABIValue
from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCall,
    AppCallParams,
    AppCreateMethodCall,
    AppCreateParams,
    AppDeleteMethodCall,
    AppDeleteParams,
    AppUpdateMethodCall,
    AppUpdateParams,
    AssetConfigParams,
    AssetCreateParams,
    AssetDestroyParams,
    AssetFreezeParams,
    AssetOptInParams,
    AssetOptOutParams,
    AssetTransferParams,
    OnlineKeyRegistrationParams,
    PaymentParams,
    TransactionComposer,
    TxnParams,
)

logger = getLogger(__name__)


@dataclass
class SendSingleTransactionResult:
    tx_id: str  # Single transaction ID (last from txIds array)
    transaction: Transaction  # Last transaction
    confirmation: algosdk.v2client.algod.AlgodResponseType  # Last confirmation

    # Fields from SendAtomicTransactionComposerResults
    group_id: str
    tx_ids: list[str]  # Full array of transaction IDs
    transactions: list[Transaction]
    confirmations: list[algosdk.v2client.algod.AlgodResponseType]
    returns: list[algosdk.atomic_transaction_composer.ABIResult] | None = None


@dataclass
class SendAppTransactionResult(SendSingleTransactionResult):
    return_value: ABIValue | None = None


@dataclass
class SendAppUpdateTransactionResult(SendAppTransactionResult):
    compiled_approval: Any | None = None
    compiled_clear: Any | None = None


@dataclass
class _RequiredSendAppTransactionResult:
    app_id: int
    app_address: str


@dataclass
class SendAppCreateTransactionResult(SendAppUpdateTransactionResult, _RequiredSendAppTransactionResult):
    pass


class LogConfig(TypedDict, total=False):
    pre_log: Callable[[TxnParams, Transaction], str]
    post_log: Callable[[TxnParams, AtomicTransactionResponse], str]


class AlgorandClientTransactionSender:
    """Orchestrates sending transactions for AlgorandClient."""

    def __init__(
        self,
        new_group: Callable[[], TransactionComposer],
        asset_manager: AssetManager,
        app_manager: AppManager,
        algod_client: algosdk.v2client.algod.AlgodClient,
    ) -> None:
        self._new_group = new_group
        self._asset_manager = asset_manager
        self._app_manager = app_manager
        self._algod = algod_client

    def new_group(self) -> TransactionComposer:
        return self._new_group()

    def _send(
        self,
        c: Callable[[TransactionComposer], Callable[[TxnParams], TransactionComposer]],
        pre_log: Callable[[TxnParams, Transaction], str] | None = None,
        post_log: Callable[[TxnParams, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[TxnParams], SendSingleTransactionResult]:
        def send_transaction(params: TxnParams) -> SendSingleTransactionResult:
            composer = self._new_group()
            c(composer)(params)

            if pre_log:
                transaction = composer.build().transactions[-1].txn
                logger.debug(pre_log(params, transaction))

            raw_result = composer.send()

            result = SendSingleTransactionResult(
                **raw_result.__dict__,
                confirmation=raw_result.confirmations[-1],
                transaction=raw_result.transactions[-1],
                tx_id=raw_result.tx_ids[-1],
            )

            if post_log:
                logger.debug(post_log(params, result))

            return result

        return send_transaction

    def _send_app_call(
        self,
        c: Callable[[TransactionComposer], Callable[[TxnParams], TransactionComposer]],
        pre_log: Callable[[TxnParams, Transaction], str] | None = None,
        post_log: Callable[[TxnParams, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[TxnParams], SendAppTransactionResult]:
        def send_app_call(params: TxnParams) -> SendAppTransactionResult:
            result = self._send(c, pre_log, post_log)(params)
            return SendAppTransactionResult(
                **result.__dict__,
                return_value=AppManager.get_abi_return(result.confirmation, getattr(params, "method", None)),
            )

        return send_app_call

    def _send_app_update_call(
        self,
        c: Callable[[TransactionComposer], Callable[[TxnParams], TransactionComposer]],
        pre_log: Callable[[TxnParams, Transaction], str] | None = None,
        post_log: Callable[[TxnParams, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[TxnParams], SendAppUpdateTransactionResult]:
        def send_app_update_call(params: TxnParams) -> SendAppUpdateTransactionResult:
            result = self._send_app_call(c, pre_log, post_log)(params)

            if not isinstance(params, AppCreateParams | AppUpdateParams | AppCreateMethodCall | AppUpdateMethodCall):
                raise TypeError("Invalid parameter type")

            compiled_approval = (
                self._app_manager.get_compilation_result(params.approval_program)
                if isinstance(params.approval_program, str)
                else None
            )
            compiled_clear = (
                self._app_manager.get_compilation_result(params.clear_state_program)
                if isinstance(params.clear_state_program, str)
                else None
            )

            return SendAppUpdateTransactionResult(
                **result.__dict__,
                compiled_approval=compiled_approval,
                compiled_clear=compiled_clear,
            )

        return send_app_update_call

    def _send_app_create_call(
        self,
        c: Callable[[TransactionComposer], Callable[[TxnParams], TransactionComposer]],
        pre_log: Callable[[TxnParams, Transaction], str] | None = None,
        post_log: Callable[[TxnParams, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[TxnParams], SendAppCreateTransactionResult]:
        def send_app_create_call(params: TxnParams) -> SendAppCreateTransactionResult:
            result = self._send_app_update_call(c, pre_log, post_log)(params)
            app_id = int(result.confirmation["application-index"])  # type: ignore[call-overload]

            return SendAppCreateTransactionResult(
                **result.__dict__,
                app_id=app_id,
                app_address=algosdk.logic.get_application_address(app_id),
            )

        return send_app_create_call

    def _get_method_call_for_log(self, method: algosdk.abi.Method, args: list[Any]) -> str:
        """Helper function to format method call logs similar to TypeScript version"""
        args_str = str([str(a) if not isinstance(a, bytes | bytearray) else a.hex() for a in args])
        return f"{method.name}({args_str})"

    @property
    def payment(self) -> Callable[[PaymentParams], AtomicTransactionResponse]:
        return self._send(
            lambda c: c.add_payment,
            {
                "pre_log": lambda params, transaction: (
                    f"Sending {params.amount.micro_algos} µALGO from {params.sender} to {params.receiver} "
                    f"via transaction {transaction.get_txid()}"
                )
            },
        )

    @property
    def asset_create(self) -> Callable[[AssetCreateParams], AtomicTransactionResponse]:
        return self._send(lambda c: c.add_asset_create)

    @property
    def asset_config(self) -> Callable[[AssetConfigParams], AtomicTransactionResponse]:
        return self._send(lambda c: c.add_asset_config)

    @property
    def asset_freeze(self) -> Callable[[AssetFreezeParams], AtomicTransactionResponse]:
        return self._send(lambda c: c.add_asset_freeze)

    @property
    def asset_destroy(self) -> Callable[[AssetDestroyParams], AtomicTransactionResponse]:
        return self._send(lambda c: c.add_asset_destroy)

    @property
    def asset_transfer(self) -> Callable[[AssetTransferParams], AtomicTransactionResponse]:
        return self._send(lambda c: c.add_asset_transfer)

    @property
    def asset_opt_in(self) -> Callable[[AssetOptInParams], AtomicTransactionResponse]:
        return self._send(lambda c: c.add_asset_opt_in)

    @property
    def asset_opt_out(self) -> Callable[[AssetOptOutParams], AtomicTransactionResponse]:
        return self._send(lambda c: c.add_asset_opt_out)

    @property
    def app_create(self) -> Callable[[AppCreateParams], SendAppCreateTransactionResult]:
        return self._send_app_create_call(lambda c: c.add_app_create)  # type: ignore[return-value]

    @property
    def app_update(self) -> Callable[[AppUpdateParams], SendAppUpdateTransactionResult]:
        return self._send_app_update_call(lambda c: c.add_app_update)

    @property
    def app_delete(self) -> Callable[[AppDeleteParams], SendAppTransactionResult]:
        return self._send_app_call(lambda c: c.add_app_delete)

    @property
    def app_call(self) -> Callable[[AppCallParams], SendAppTransactionResult]:
        return self._send_app_call(lambda c: c.add_app_call)

    @property
    def app_create_method_call(self) -> Callable[[AppCreateMethodCall], SendAppCreateTransactionResult]:
        return self._send_app_create_call(lambda c: c.add_app_create_method_call)

    @property
    def app_update_method_call(self) -> Callable[[AppUpdateMethodCall], SendAppUpdateTransactionResult]:
        return self._send_app_update_call(
            lambda c: c.add_app_update_method_call,
            {
                "post_log": lambda params, result: (
                    f"App {params.app_id} updated with {self._get_method_call_for_log(params.method, params.args or [])} "
                    f"by {params.sender} via transaction {result.tx_ids[-1]}"
                )
            },
        )

    @property
    def app_delete_method_call(self) -> Callable[[AppDeleteMethodCall], SendAppTransactionResult]:
        return self._send_app_call(
            lambda c: c.add_app_delete_method_call,
            {
                "post_log": lambda params, result: (
                    f"App {params.app_id} deleted with {self._get_method_call_for_log(params.method, params.args or [])} "
                    f"by {params.sender} via transaction {result.tx_ids[-1]}"
                )
            },
        )

    @property
    def app_call_method_call(self) -> Callable[[AppCallMethodCall], SendAppTransactionResult]:
        return self._send_app_call(
            lambda c: c.add_app_call_method_call,
            {
                "post_log": lambda params, result: (
                    f"App {params.app_id} called with {self._get_method_call_for_log(params.method, params.args or [])} "
                    f"by {params.sender} via transaction {result.tx_ids[-1]}"
                )
            },
        )

    @property
    def online_key_registration(self) -> Callable[[OnlineKeyRegistrationParams], AtomicTransactionResponse]:
        return self._send(lambda c: c.add_online_key_registration)
