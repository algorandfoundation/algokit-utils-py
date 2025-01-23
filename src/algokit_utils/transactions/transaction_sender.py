from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

import algosdk
import algosdk.atomic_transaction_composer
from algosdk.transaction import Transaction
from typing_extensions import Self

from algokit_utils.applications.abi import ABIReturn
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.assets.asset_manager import AssetManager
from algokit_utils.config import config
from algokit_utils.models.transaction import TransactionWrapper
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
    OfflineKeyRegistrationParams,
    OnlineKeyRegistrationParams,
    PaymentParams,
    SendAtomicTransactionComposerResults,
    TransactionComposer,
    TxnParams,
)

__all__ = [
    "AlgorandClientTransactionSender",
    "SendAppCreateTransactionResult",
    "SendAppTransactionResult",
    "SendAppUpdateTransactionResult",
    "SendSingleAssetCreateTransactionResult",
    "SendSingleTransactionResult",
]

logger = config.logger


T = TypeVar("T", bound=TxnParams)


@dataclass(frozen=True, kw_only=True)
class SendSingleTransactionResult:
    """Base class for transaction results.

    Represents the result of sending a single transaction.
    """

    transaction: TransactionWrapper  # Last transaction
    confirmation: algosdk.v2client.algod.AlgodResponseType  # Last confirmation

    # Fields from SendAtomicTransactionComposerResults
    group_id: str
    tx_id: str | None = None
    tx_ids: list[str]  # Full array of transaction IDs
    transactions: list[TransactionWrapper]
    confirmations: list[algosdk.v2client.algod.AlgodResponseType]
    returns: list[ABIReturn] | None = None

    @classmethod
    def from_composer_result(cls, result: SendAtomicTransactionComposerResults, index: int = -1) -> Self:
        # Get base parameters
        base_params = {
            "transaction": result.transactions[index],
            "confirmation": result.confirmations[index],
            "group_id": result.group_id,
            "tx_id": result.tx_ids[index],
            "tx_ids": result.tx_ids,
            "transactions": [result.transactions[index]],
            "confirmations": result.confirmations,
            "returns": result.returns,
        }

        # For asset creation, extract asset_id from confirmation
        if cls is SendSingleAssetCreateTransactionResult:
            base_params["asset_id"] = result.confirmations[index]["asset-index"]  # type: ignore[call-overload]
        # For app creation, extract app_id and calculate app_address
        elif cls is SendAppCreateTransactionResult:
            app_id = result.confirmations[index]["application-index"]  # type: ignore[call-overload]
            base_params.update(
                {
                    "app_id": app_id,
                    "app_address": algosdk.logic.get_application_address(app_id),
                    "abi_return": result.returns[index] if result.returns else None,  # type: ignore[dict-item]
                }
            )
        # For regular app transactions, just add abi_return
        elif cls is SendAppTransactionResult:
            base_params["abi_return"] = result.returns[index] if result.returns else None  # type: ignore[assignment]

        return cls(**base_params)  # type: ignore[arg-type]


@dataclass(frozen=True, kw_only=True)
class SendSingleAssetCreateTransactionResult(SendSingleTransactionResult):
    """Result of creating a new ASA (Algorand Standard Asset).

    Contains the asset ID of the newly created asset.
    """

    asset_id: int


ABIReturnT = TypeVar("ABIReturnT")


@dataclass(frozen=True)
class SendAppTransactionResult(SendSingleTransactionResult, Generic[ABIReturnT]):
    """Result of an application transaction.

    Contains the ABI return value if applicable.
    """

    abi_return: ABIReturnT | None = None


@dataclass(frozen=True)
class SendAppUpdateTransactionResult(SendAppTransactionResult[ABIReturnT]):
    """Result of updating an application.

    Contains the compiled approval and clear programs.
    """

    compiled_approval: Any | None = None
    compiled_clear: Any | None = None


@dataclass(frozen=True, kw_only=True)
class SendAppCreateTransactionResult(SendAppUpdateTransactionResult[ABIReturnT]):
    """Result of creating a new application.

    Contains the app ID and address of the newly created application.
    """

    app_id: int
    app_address: str


class AlgorandClientTransactionSender:
    """Orchestrates sending transactions for AlgorandClient.

    Provides methods to send various types of transactions including payments,
    asset operations, and application calls.
    """

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
        """Create a new transaction group.

        :return: A new TransactionComposer instance
        """
        return self._new_group()

    def _send(
        self,
        c: Callable[[TransactionComposer], Callable[[T], TransactionComposer]],
        pre_log: Callable[[T, Transaction], str] | None = None,
        post_log: Callable[[T, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[T], SendSingleTransactionResult]:
        def send_transaction(params: T) -> SendSingleTransactionResult:
            composer = self.new_group()
            c(composer)(params)

            if pre_log:
                transaction = composer.build().transactions[-1].txn
                logger.debug(pre_log(params, transaction))

            raw_result = composer.send(
                populate_app_call_resources=params.populate_app_call_resources,
                max_rounds_to_wait=params.max_rounds_to_wait,
                suppress_log=params.suppress_log,
            )
            raw_result_dict = raw_result.__dict__.copy()
            raw_result_dict["transactions"] = raw_result.transactions
            del raw_result_dict["simulate_response"]

            result = SendSingleTransactionResult(
                **raw_result_dict,
                confirmation=raw_result.confirmations[-1],
                transaction=raw_result_dict["transactions"][-1],
                tx_id=raw_result.tx_ids[-1],
            )

            if post_log:
                logger.debug(post_log(params, result))

            return result

        return send_transaction

    def _send_app_call(
        self,
        c: Callable[[TransactionComposer], Callable[[T], TransactionComposer]],
        pre_log: Callable[[T, Transaction], str] | None = None,
        post_log: Callable[[T, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[T], SendAppTransactionResult[ABIReturn]]:
        def send_app_call(params: T) -> SendAppTransactionResult[ABIReturn]:
            result = self._send(c, pre_log, post_log)(params)
            return SendAppTransactionResult[ABIReturn](
                **result.__dict__,
                abi_return=AppManager.get_abi_return(result.confirmation, getattr(params, "method", None)),
            )

        return send_app_call

    def _send_app_update_call(
        self,
        c: Callable[[TransactionComposer], Callable[[T], TransactionComposer]],
        pre_log: Callable[[T, Transaction], str] | None = None,
        post_log: Callable[[T, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[T], SendAppUpdateTransactionResult[ABIReturn]]:
        def send_app_update_call(params: T) -> SendAppUpdateTransactionResult[ABIReturn]:
            result = self._send_app_call(c, pre_log, post_log)(params)

            if not isinstance(
                params, AppCreateParams | AppUpdateParams | AppCreateMethodCallParams | AppUpdateMethodCallParams
            ):
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

            return SendAppUpdateTransactionResult[ABIReturn](
                **result.__dict__,
                compiled_approval=compiled_approval,
                compiled_clear=compiled_clear,
            )

        return send_app_update_call

    def _send_app_create_call(
        self,
        c: Callable[[TransactionComposer], Callable[[T], TransactionComposer]],
        pre_log: Callable[[T, Transaction], str] | None = None,
        post_log: Callable[[T, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[T], SendAppCreateTransactionResult[ABIReturn]]:
        def send_app_create_call(params: T) -> SendAppCreateTransactionResult[ABIReturn]:
            result = self._send_app_update_call(c, pre_log, post_log)(params)
            app_id = int(result.confirmation["application-index"])  # type: ignore[call-overload]

            return SendAppCreateTransactionResult[ABIReturn](
                **result.__dict__,
                app_id=app_id,
                app_address=algosdk.logic.get_application_address(app_id),
            )

        return send_app_create_call

    def _get_method_call_for_log(self, method: algosdk.abi.Method, args: list[Any]) -> str:
        """Helper function to format method call logs similar to TypeScript version"""
        args_str = str([str(a) if not isinstance(a, bytes | bytearray) else a.hex() for a in args])
        return f"{method.name}({args_str})"

    def payment(self, params: PaymentParams) -> SendSingleTransactionResult:
        """Send a payment transaction to transfer Algo between accounts.

        :param params: Payment transaction parameters
        :return: Result of the payment transaction
        """
        return self._send(
            lambda c: c.add_payment,
            pre_log=lambda params, transaction: (
                f"Sending {params.amount} from {params.sender} to {params.receiver} "
                f"via transaction {transaction.get_txid()}"
            ),
        )(params)

    def asset_create(self, params: AssetCreateParams) -> SendSingleAssetCreateTransactionResult:
        """Create a new Algorand Standard Asset.

        :param params: Asset creation parameters
        :return: Result containing the new asset ID
        """
        result = self._send(
            lambda c: c.add_asset_create,
            post_log=lambda params, result: (
                f"Created asset{f' {params.asset_name}' if hasattr(params, 'asset_name') else ''}"
                f"{f' ({params.unit_name})' if hasattr(params, 'unit_name') else ''} with "
                f"{params.total} units and {getattr(params, 'decimals', 0)} decimals created by "
                f"{params.sender} with ID {result.confirmation['asset-index']} via transaction "  # type: ignore[call-overload]
                f"{result.tx_ids[-1]}"
            ),
        )(params)

        return SendSingleAssetCreateTransactionResult(
            **result.__dict__,
            asset_id=int(result.confirmation["asset-index"]),  # type: ignore[call-overload]
        )

    def asset_config(self, params: AssetConfigParams) -> SendSingleTransactionResult:
        """Configure an existing Algorand Standard Asset.

        :param params: Asset configuration parameters
        :return: Result of the configuration transaction
        """
        return self._send(
            lambda c: c.add_asset_config,
            pre_log=lambda params, transaction: (
                f"Configuring asset with ID {params.asset_id} via transaction {transaction.get_txid()}"
            ),
        )(params)

    def asset_freeze(self, params: AssetFreezeParams) -> SendSingleTransactionResult:
        """Freeze or unfreeze an Algorand Standard Asset for an account.

        :param params: Asset freeze parameters
        :return: Result of the freeze transaction
        """
        return self._send(
            lambda c: c.add_asset_freeze,
            pre_log=lambda params, transaction: (
                f"Freezing asset with ID {params.asset_id} via transaction {transaction.get_txid()}"
            ),
        )(params)

    def asset_destroy(self, params: AssetDestroyParams) -> SendSingleTransactionResult:
        """Destroys an Algorand Standard Asset.

        :param params: Asset destruction parameters
        :return: Result of the destroy transaction
        """
        return self._send(
            lambda c: c.add_asset_destroy,
            pre_log=lambda params, transaction: (
                f"Destroying asset with ID {params.asset_id} via transaction {transaction.get_txid()}"
            ),
        )(params)

    def asset_transfer(self, params: AssetTransferParams) -> SendSingleTransactionResult:
        """Transfer an Algorand Standard Asset.

        :param params: Asset transfer parameters
        :return: Result of the transfer transaction
        """
        return self._send(
            lambda c: c.add_asset_transfer,
            pre_log=lambda params, transaction: (
                f"Transferring {params.amount} units of asset with ID {params.asset_id} from "
                f"{params.sender} to {params.receiver} via transaction {transaction.get_txid()}"
            ),
        )(params)

    def asset_opt_in(self, params: AssetOptInParams) -> SendSingleTransactionResult:
        """Opt an account into an Algorand Standard Asset.

        :param params: Asset opt-in parameters
        :return: Result of the opt-in transaction
        """
        return self._send(
            lambda c: c.add_asset_opt_in,
            pre_log=lambda params, transaction: (
                f"Opting in {params.sender} to asset with ID {params.asset_id} via transaction "
                f"{transaction.get_txid()}"
            ),
        )(params)

    def asset_opt_out(
        self,
        *,
        params: AssetOptOutParams,
        ensure_zero_balance: bool = True,
    ) -> SendSingleTransactionResult:
        """Opt an account out of an Algorand Standard Asset.

        :param params: Asset opt-out parameters
        :param ensure_zero_balance: Check if account has zero balance before opt-out, defaults to True
        :raises ValueError: If account has non-zero balance or is not opted in
        :return: Result of the opt-out transaction
        """
        if ensure_zero_balance:
            try:
                account_asset_info = self._asset_manager.get_account_information(params.sender, params.asset_id)
                balance = account_asset_info.balance
                if balance != 0:
                    raise ValueError(
                        f"Account {params.sender} does not have a zero balance for Asset "
                        f"{params.asset_id}; can't opt-out."
                    )
            except Exception as e:
                raise ValueError(
                    f"Account {params.sender} is not opted-in to Asset {params.asset_id}; " "can't opt-out."
                ) from e

        if not hasattr(params, "creator"):
            asset_info = self._asset_manager.get_by_id(params.asset_id)
            params = AssetOptOutParams(
                **params.__dict__,
                creator=asset_info.creator,
            )

        creator = params.__dict__.get("creator")
        return self._send(
            lambda c: c.add_asset_opt_out,
            pre_log=lambda params, transaction: (
                f"Opting {params.sender} out of asset with ID {params.asset_id} to creator "
                f"{creator} via transaction {transaction.get_txid()}"
            ),
        )(params)

    def app_create(self, params: AppCreateParams) -> SendAppCreateTransactionResult[ABIReturn]:
        """Create a new application.

        :param params: Application creation parameters
        :return: Result containing the new application ID and address
        """
        return self._send_app_create_call(lambda c: c.add_app_create)(params)

    def app_update(self, params: AppUpdateParams) -> SendAppUpdateTransactionResult[ABIReturn]:
        """Update an application.

        :param params: Application update parameters
        :return: Result containing the compiled programs
        """
        return self._send_app_update_call(lambda c: c.add_app_update)(params)

    def app_delete(self, params: AppDeleteParams) -> SendAppTransactionResult[ABIReturn]:
        """Delete an application.

        :param params: Application deletion parameters
        :return: Result of the deletion transaction
        """
        return self._send_app_call(lambda c: c.add_app_delete)(params)

    def app_call(self, params: AppCallParams) -> SendAppTransactionResult[ABIReturn]:
        """Call an application.

        :param  params: Application call parameters
        :return: Result containing any ABI return value
        """
        return self._send_app_call(lambda c: c.add_app_call)(params)

    def app_create_method_call(self, params: AppCreateMethodCallParams) -> SendAppCreateTransactionResult[ABIReturn]:
        """Call an application's create method.

        :param params: Method call parameters for application creation
        :return: Result containing the new application ID and address
        """
        return self._send_app_create_call(lambda c: c.add_app_create_method_call)(params)

    def app_update_method_call(self, params: AppUpdateMethodCallParams) -> SendAppUpdateTransactionResult[ABIReturn]:
        """Call an application's update method.

        :param params: Method call parameters for application update
        :return: Result containing the compiled programs
        """
        return self._send_app_update_call(lambda c: c.add_app_update_method_call)(params)

    def app_delete_method_call(self, params: AppDeleteMethodCallParams) -> SendAppTransactionResult[ABIReturn]:
        """Call an application's delete method.

        :param params: Method call parameters for application deletion
        :return: Result of the deletion transaction
        """
        return self._send_app_call(lambda c: c.add_app_delete_method_call)(params)

    def app_call_method_call(self, params: AppCallMethodCallParams) -> SendAppTransactionResult[ABIReturn]:
        """Call an application's call method.

        :param params: Method call parameters
        :return: Result containing any ABI return value
        """
        return self._send_app_call(lambda c: c.add_app_call_method_call)(params)

    def online_key_registration(self, params: OnlineKeyRegistrationParams) -> SendSingleTransactionResult:
        """Register an online key.

        :param params: Key registration parameters
        :return: Result of the registration transaction
        """
        return self._send(
            lambda c: c.add_online_key_registration,
            pre_log=lambda params, transaction: (
                f"Registering online key for {params.sender} via transaction {transaction.get_txid()}"
            ),
        )(params)

    def offline_key_registration(self, params: OfflineKeyRegistrationParams) -> SendSingleTransactionResult:
        """Register an offline key.

        :param params: Key registration parameters
        :return: Result of the registration transaction
        """
        return self._send(
            lambda c: c.add_offline_key_registration,
            pre_log=lambda params, transaction: (
                f"Registering offline key for {params.sender} via transaction {transaction.get_txid()}"
            ),
        )(params)
