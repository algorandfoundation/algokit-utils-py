from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

from typing_extensions import Self

from algokit_abi import arc56
from algokit_algod_client import AlgodClient
from algokit_algod_client import models as algod_models
from algokit_common import get_application_address
from algokit_transact import Transaction
from algokit_utils.applications.abi import ABIReturn
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.assets.asset_manager import AssetManager
from algokit_utils.config import config
from algokit_utils.models.application import CompiledTeal
from algokit_utils.models.transaction import SendParams
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
    SendTransactionComposerResults,
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


TxnParamsT = TypeVar("TxnParamsT", bound=TxnParams)


@dataclass(frozen=True, kw_only=True)
class SendSingleTransactionResult:
    """Base class for transaction results.

    Represents the result of sending a single transaction.
    """

    transaction: Transaction  # Last transaction
    """The last transaction"""

    confirmation: algod_models.PendingTransactionResponse  # Last confirmation
    """The last confirmation"""

    # Fields from SendTransactionComposerResults
    group_id: str
    """The group ID"""

    tx_id: str | None = None
    """The transaction ID"""

    tx_ids: list[str]  # Full array of transaction IDs
    """The full array of transaction IDs"""
    transactions: list[Transaction]
    """The full array of transactions"""

    confirmations: list[algod_models.PendingTransactionResponse]
    """The full array of confirmations"""

    returns: list[ABIReturn] | None = None
    """The ABI return value if applicable"""

    @classmethod
    def from_composer_result(
        cls, result: SendTransactionComposerResults, *, is_abi: bool = False, index: int = -1
    ) -> Self:
        wrapped_transactions = result.transactions

        # Get base parameters
        base_params = {
            "transaction": wrapped_transactions[index],
            "confirmation": result.confirmations[index],
            "group_id": result.group_id or "",
            "tx_id": result.tx_ids[index],
            "tx_ids": result.tx_ids,
            "transactions": [wrapped_transactions[index]],
            "confirmations": result.confirmations,
            "returns": result.returns,
        }

        # For asset creation, extract asset_id from confirmation
        if cls is SendSingleAssetCreateTransactionResult:
            confirmation = result.confirmations[index]
            asset_id = confirmation.asset_id
            if asset_id is None:
                raise ValueError("Could not extract asset_id from confirmation")
            base_params["asset_id"] = int(asset_id)
        # For app creation, extract app_id and calculate app_address
        elif cls is SendAppCreateTransactionResult:
            confirmation = result.confirmations[index]
            app_id_raw = confirmation.app_id
            if app_id_raw is None:
                raise ValueError("Could not extract app_id from confirmation")
            app_id = int(app_id_raw)
            base_params.update(
                {
                    "app_id": app_id,
                    "app_address": get_application_address(app_id),
                    "abi_return": result.returns[index] if result.returns and is_abi else None,
                }
            )
        # For regular app transactions, just add abi_return
        elif cls is SendAppTransactionResult:
            base_params["abi_return"] = result.returns[index] if result.returns and is_abi else None

        return cls(**cast(dict[str, Any], base_params))


@dataclass(frozen=True, kw_only=True)
class SendSingleAssetCreateTransactionResult(SendSingleTransactionResult):
    """Result of creating a new ASA (Algorand Standard Asset).

    Contains the asset ID of the newly created asset.
    """

    asset_id: int
    """The ID of the newly created asset"""


ABIReturnT = TypeVar("ABIReturnT")


@dataclass(frozen=True)
class SendAppTransactionResult(SendSingleTransactionResult, Generic[ABIReturnT]):
    """Result of an application transaction.

    Contains the ABI return value if applicable.
    """

    abi_return: ABIReturnT | None = None
    """The ABI return value if applicable"""


@dataclass(frozen=True)
class SendAppUpdateTransactionResult(SendAppTransactionResult[ABIReturnT]):
    """Result of updating an application.

    Contains the compiled approval and clear programs.
    """

    compiled_approval: CompiledTeal | bytes | None = None
    """The compiled approval program"""

    compiled_clear: CompiledTeal | bytes | None = None
    """The compiled clear state program"""


@dataclass(frozen=True, kw_only=True)
class SendAppCreateTransactionResult(SendAppUpdateTransactionResult[ABIReturnT]):
    """Result of creating a new application.

    Contains the app ID and address of the newly created application.
    """

    app_id: int
    """The ID of the newly created application"""

    app_address: str
    """The address of the newly created application"""


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
        algod_client: AlgodClient,
    ) -> None:
        self._new_group = new_group
        self._asset_manager = asset_manager
        self._app_manager = app_manager
        self._algod = algod_client

    def new_group(self) -> TransactionComposer:
        """Create a new transaction group.

        :return: A new TransactionComposer instance

        :example:
            >>> sender = AlgorandClientTransactionSender(new_group, asset_manager, app_manager, algod_client)
            >>> composer = sender.new_group()
            >>> composer(PaymentParams(sender="sender", receiver="receiver", amount=AlgoAmount(algo=1)))
            >>> composer.send()
        """
        return self._new_group()

    def _send(
        self,
        c: Callable[[TransactionComposer], Callable[[TxnParamsT], TransactionComposer]],
        pre_log: Callable[[TxnParamsT, Transaction], str] | None = None,
        post_log: Callable[[TxnParamsT, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[TxnParamsT, SendParams | None], SendSingleTransactionResult]:
        def send_transaction(params: TxnParamsT, send_params: SendParams | None = None) -> SendSingleTransactionResult:
            composer = self.new_group()
            c(composer)(params)

            if pre_log:
                built = composer.build()
                last_txn = built.transactions[-1]
                config.logger.debug(pre_log(params, last_txn))

            raw_result = composer.send(
                send_params,
            )
            transactions = raw_result.transactions
            confirmations = list(raw_result.confirmations)
            result = SendSingleTransactionResult(
                transaction=transactions[-1],
                confirmation=confirmations[-1],
                group_id=raw_result.group_id or "",
                tx_id=raw_result.tx_ids[-1],
                tx_ids=raw_result.tx_ids,
                transactions=transactions,
                confirmations=confirmations,
                returns=raw_result.returns,
            )

            if post_log:
                config.logger.debug(post_log(params, result))

            return result

        return send_transaction

    def _send_app_call(
        self,
        c: Callable[[TransactionComposer], Callable[[TxnParamsT], TransactionComposer]],
        pre_log: Callable[[TxnParamsT, Transaction], str] | None = None,
        post_log: Callable[[TxnParamsT, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[TxnParamsT, SendParams | None], SendAppTransactionResult[ABIReturn]]:
        def send_app_call(
            params: TxnParamsT, send_params: SendParams | None = None
        ) -> SendAppTransactionResult[ABIReturn]:
            result = self._send(c, pre_log, post_log)(params, send_params)
            return SendAppTransactionResult[ABIReturn](
                **result.__dict__,
                abi_return=AppManager.get_abi_return(result.confirmation, getattr(params, "method", None)),
            )

        return send_app_call

    def _send_app_update_call(
        self,
        c: Callable[[TransactionComposer], Callable[[TxnParamsT], TransactionComposer]],
        pre_log: Callable[[TxnParamsT, Transaction], str] | None = None,
        post_log: Callable[[TxnParamsT, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[TxnParamsT, SendParams | None], SendAppUpdateTransactionResult[ABIReturn]]:
        def send_app_update_call(
            params: TxnParamsT, send_params: SendParams | None = None
        ) -> SendAppUpdateTransactionResult[ABIReturn]:
            result = self._send_app_call(c, pre_log, post_log)(params, send_params)

            if not isinstance(
                params, AppCreateParams | AppUpdateParams | AppCreateMethodCallParams | AppUpdateMethodCallParams
            ):
                raise TypeError("Invalid parameter type")

            compiled_approval = (
                self._app_manager.get_compilation_result(params.approval_program)
                if isinstance(params.approval_program, str)
                else params.approval_program
            )
            compiled_clear = (
                self._app_manager.get_compilation_result(params.clear_state_program)
                if isinstance(params.clear_state_program, str)
                else params.clear_state_program
            )

            return SendAppUpdateTransactionResult[ABIReturn](
                **result.__dict__,
                compiled_approval=compiled_approval,
                compiled_clear=compiled_clear,
            )

        return send_app_update_call

    def _send_app_create_call(
        self,
        c: Callable[[TransactionComposer], Callable[[TxnParamsT], TransactionComposer]],
        pre_log: Callable[[TxnParamsT, Transaction], str] | None = None,
        post_log: Callable[[TxnParamsT, SendSingleTransactionResult], str] | None = None,
    ) -> Callable[[TxnParamsT, SendParams | None], SendAppCreateTransactionResult[ABIReturn]]:
        def send_app_create_call(
            params: TxnParamsT, send_params: SendParams | None = None
        ) -> SendAppCreateTransactionResult[ABIReturn]:
            result = self._send_app_update_call(c, pre_log, post_log)(params, send_params)
            app_id_raw = result.confirmation.app_id
            if app_id_raw is None:
                raise ValueError("Could not extract app_id from confirmation")
            app_id = int(app_id_raw)

            return SendAppCreateTransactionResult[ABIReturn](
                **result.__dict__,
                app_id=app_id,
                app_address=get_application_address(app_id),
            )

        return send_app_create_call

    def _get_method_call_for_log(self, method: arc56.Method, args: list[Any]) -> str:
        """Helper function to format method call logs similar to TypeScript version"""
        args_str = str([str(a) if not isinstance(a, bytes | bytearray) else a.hex() for a in args])
        return f"{method.name}({args_str})"

    def payment(self, params: PaymentParams, send_params: SendParams | None = None) -> SendSingleTransactionResult:
        """Send a payment transaction to transfer Algo between accounts.

        :param params: Payment transaction parameters
        :param send_params: Send parameters
        :return: Result of the payment transaction

        :example:
            >>> result = algorand.send.payment(PaymentParams(
            >>>  sender="SENDERADDRESS",
            >>>  receiver="RECEIVERADDRESS",
            >>>  amount=AlgoAmount(algo=4),
            >>> ))

            >>> # Advanced example
            >>> result =  algorand.send.payment(PaymentParams(
            >>>  amount=AlgoAmount(algo=4),
            >>>  receiver="RECEIVERADDRESS",
            >>>  sender="SENDERADDRESS",
            >>>  close_remainder_to="CLOSEREMAINDERTOADDRESS",
            >>>  lease="lease",
            >>>  note="note",
            >>>  rekey_to="REKEYTOADDRESS",
            >>>  first_valid_round=1000,
            >>>  validity_window=10,
            >>>  extra_fee=AlgoAmount(micro_algo=1000),
            >>>  static_fee=AlgoAmount(micro_algo=1000),
            >>>  max_fee=AlgoAmount(micro_algo=3000),
            >>>  signer=transactionSigner
            >>> ), send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
        """
        return self._send(
            lambda c: c.add_payment,
            pre_log=lambda params, transaction: (
                f"Sending {params.amount} from {params.sender} to {params.receiver} "
                f"via transaction {transaction.tx_id()}"
            ),
        )(params, send_params)

    def asset_create(
        self, params: AssetCreateParams, send_params: SendParams | None = None
    ) -> SendSingleAssetCreateTransactionResult:
        """Create a new Algorand Standard Asset.

        :param params: Asset creation parameters
        :param send_params: Send parameters
        :return: Result containing the new asset ID
        :raises ValueError: If the confirmation payload does not include an asset_id

        :example:
            >>> result = algorand.send.asset_create(AssetCreateParams(
            >>>  sender="SENDERADDRESS",
            >>>  asset_name="ASSETNAME",
            >>>  unit_name="UNITNAME",
            >>>  total=1000,
            >>> ))

            >>> # Advanced example
            >>> result = algorand.send.asset_create(AssetCreateParams(
            >>>  sender="CREATORADDRESS",
            >>>  total=100,
            >>>  decimals=2,
            >>>  asset_name="asset",
            >>>  unit_name="unit",
            >>>  url="url",
            >>>  metadata_hash="metadataHash",
            >>>  default_frozen=False,
            >>>  manager="MANAGERADDRESS",
            >>>  reserve="RESERVEADDRESS",
            >>>  freeze="FREEZEADDRESS",
            >>>  clawback="CLAWBACKADDRESS",
            >>>  lease="lease",
            >>>  note="note",
            >>>  # You wouldn't normally set this field
            >>>  first_valid_round=1000,
            >>>  validity_window=10,
            >>>  extra_fee=AlgoAmount(micro_algo=1000),
            >>>  static_fee=AlgoAmount(micro_algo=1000),
            >>>  # Max fee doesn't make sense with extraFee AND staticFee
            >>>  #  already specified, but here for completeness
            >>>  max_fee=AlgoAmount(micro_algo=3000),
            >>>  # Signer only needed if you want to provide one,
            >>>  #  generally you'd register it with AlgorandClient
            >>>  #  against the sender and not need to pass it in
            >>>  signer=transactionSigner
            >>> ), send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
        """
        result = self._send(
            lambda c: c.add_asset_create,
            post_log=lambda params, result: (
                f"Created asset{f' {params.asset_name}' if hasattr(params, 'asset_name') else ''}"
                f"{f' ({params.unit_name})' if hasattr(params, 'unit_name') else ''} with "
                f"{params.total} units and {getattr(params, 'decimals', 0)} decimals created by "
                f"{params.sender} with ID {result.confirmation.asset_id} "
                f"via transaction {result.tx_ids[-1]}"
            ),
        )(params, send_params)

        asset_id_raw = result.confirmation.asset_id
        if asset_id_raw is None:
            raise ValueError("Could not extract asset_id from confirmation")
        return SendSingleAssetCreateTransactionResult(
            **result.__dict__,
            asset_id=int(asset_id_raw),
        )

    def asset_config(
        self, params: AssetConfigParams, send_params: SendParams | None = None
    ) -> SendSingleTransactionResult:
        """Configure an existing Algorand Standard Asset.

        :param params: Asset configuration parameters
        :param send_params: Send parameters
        :return: Result of the configuration transaction

        :example:
            >>> result = algorand.send.asset_config(AssetConfigParams(
            >>>  sender="MANAGERADDRESS",
            >>>  asset_id=123456,
            >>>  manager="MANAGERADDRESS",
            >>>  reserve="RESERVEADDRESS",
            >>>  freeze="FREEZEADDRESS",
            >>>  clawback="CLAWBACKADDRESS",
            >>>  lease="lease",
            >>>  note="note",
            >>>  # You wouldn't normally set this field
            >>>  first_valid_round=1000,
            >>>  validity_window=10,
            >>>  extra_fee=AlgoAmount(micro_algo=1000),
            >>>  static_fee=AlgoAmount(micro_algo=1000),
            >>>  # Max fee doesn't make sense with extraFee AND staticFee
            >>>  #  already specified, but here for completeness
            >>>  max_fee=AlgoAmount(micro_algo=3000),
            >>>  # Signer only needed if you want to provide one,
            >>>  #  generally you'd register it with AlgorandClient
            >>>  #  against the sender and not need to pass it in
            >>>  signer=transactionSigner
            >>> ), send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
        """
        return self._send(
            lambda c: c.add_asset_config,
            pre_log=lambda params, transaction: (
                f"Configuring asset with ID {params.asset_id} via transaction {transaction.tx_id()}"
            ),
        )(params, send_params)

    def asset_freeze(
        self, params: AssetFreezeParams, send_params: SendParams | None = None
    ) -> SendSingleTransactionResult:
        """Freeze or unfreeze an Algorand Standard Asset for an account.

        :param params: Asset freeze parameters
        :param send_params: Send parameters
        :return: Result of the freeze transaction

        :example:
            >>> result = algorand.send.asset_freeze(AssetFreezeParams(
            >>>  sender="MANAGERADDRESS",
            >>>  asset_id=123456,
            >>>  account="ACCOUNTADDRESS",
            >>>  frozen=True,
            >>> ))

            >>> # Advanced example
            >>> result = algorand.send.asset_freeze(AssetFreezeParams(
            >>>  sender="MANAGERADDRESS",
            >>>  asset_id=123456,
            >>>  account="ACCOUNTADDRESS",
            >>>  frozen=True,
            >>>  lease="lease",
            >>>  note="note",
            >>>  # You wouldn't normally set this field
            >>>  first_valid_round=1000,
            >>>  validity_window=10,
            >>>  extra_fee=AlgoAmount(micro_algo=1000),
            >>>  static_fee=AlgoAmount(micro_algo=1000),
            >>>  # Max fee doesn't make sense with extraFee AND staticFee
            >>>  #  already specified, but here for completeness
            >>>  max_fee=AlgoAmount(micro_algo=3000),
            >>>  # Signer only needed if you want to provide one,
            >>>  #  generally you'd register it with AlgorandClient
            >>>  #  against the sender and not need to pass it in
            >>>  signer=transactionSigner
            >>> ), send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
        """
        return self._send(
            lambda c: c.add_asset_freeze,
            pre_log=lambda params, transaction: (
                f"Freezing asset with ID {params.asset_id} via transaction {transaction.tx_id()}"
            ),
        )(params, send_params)

    def asset_destroy(
        self, params: AssetDestroyParams, send_params: SendParams | None = None
    ) -> SendSingleTransactionResult:
        """Destroys an Algorand Standard Asset.

        :param params: Asset destruction parameters
        :param send_params: Send parameters
        :return: Result of the destroy transaction

        :example:
            >>> result = algorand.send.asset_destroy(AssetDestroyParams(
            >>>  sender="MANAGERADDRESS",
            >>>  asset_id=123456,
            >>> ))

            >>> # Advanced example
            >>> result = algorand.send.asset_destroy(AssetDestroyParams(
            >>>  sender="MANAGERADDRESS",
            >>>  asset_id=123456,
            >>>  lease="lease",
            >>>  note="note",
            >>>  # You wouldn't normally set this field
            >>>  first_valid_round=1000,
            >>>  validity_window=10,
            >>>  extra_fee=AlgoAmount(micro_algo=1000),
            >>>  static_fee=AlgoAmount(micro_algo=1000),
            >>>  # Max fee doesn't make sense with extraFee AND staticFee
            >>>  #  already specified, but here for completeness
            >>>  max_fee=AlgoAmount(micro_algo=3000),
            >>>  # Signer only needed if you want to provide one,
            >>>  #  generally you'd register it with AlgorandClient
            >>>  #  against the sender and not need to pass it in
            >>>  signer=transactionSigner
            >>> ), send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
        """
        return self._send(
            lambda c: c.add_asset_destroy,
            pre_log=lambda params, transaction: (
                f"Destroying asset with ID {params.asset_id} via transaction {transaction.tx_id()}"
            ),
        )(params, send_params)

    def asset_transfer(
        self, params: AssetTransferParams, send_params: SendParams | None = None
    ) -> SendSingleTransactionResult:
        """Transfer an Algorand Standard Asset.

        :param params: Asset transfer parameters
        :param send_params: Send parameters
        :return: Result of the transfer transaction

        :example:
            >>> result = algorand.send.asset_transfer(AssetTransferParams(
            >>>  sender="HOLDERADDRESS",
            >>>  asset_id=123456,
            >>>  amount=1,
            >>>  receiver="RECEIVERADDRESS",
            >>> ))

            >>> # Advanced example (with clawback)
            >>> result = algorand.send.asset_transfer(AssetTransferParams(
            >>>  sender="CLAWBACKADDRESS",
            >>>  asset_id=123456,
            >>>  amount=1,
            >>>  receiver="RECEIVERADDRESS",
            >>>  clawback_target="HOLDERADDRESS",
            >>>  # This field needs to be used with caution
            >>>  close_asset_to="ADDRESSTOCLOSETO",
            >>>  lease="lease",
            >>>  note="note",
            >>>  # You wouldn't normally set this field
            >>>  first_valid_round=1000,
            >>>  validity_window=10,
            >>>  extra_fee=AlgoAmount(micro_algo=1000),
            >>>  static_fee=AlgoAmount(micro_algo=1000),
            >>>  # Max fee doesn't make sense with extraFee AND staticFee
            >>>  #  already specified, but here for completeness
            >>>  max_fee=AlgoAmount(micro_algo=3000),
            >>>  # Signer only needed if you want to provide one,
            >>>  #  generally you'd register it with AlgorandClient
            >>>  #  against the sender and not need to pass it in
            >>>  signer=transactionSigner
            >>> ), send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
        """
        return self._send(
            lambda c: c.add_asset_transfer,
            pre_log=lambda params, transaction: (
                f"Transferring {params.amount} units of asset with ID {params.asset_id} from "
                f"{params.sender} to {params.receiver} via transaction {transaction.tx_id()}"
            ),
        )(params, send_params)

    def asset_opt_in(
        self, params: AssetOptInParams, send_params: SendParams | None = None
    ) -> SendSingleTransactionResult:
        """Opt an account into an Algorand Standard Asset.

        :param params: Asset opt-in parameters
        :param send_params: Send parameters
        :return: Result of the opt-in transaction

        :example:
            >>> result = algorand.send.asset_opt_in(AssetOptInParams(
            >>>  sender="SENDERADDRESS",
            >>>  asset_id=123456,
            >>> ))

            >>> # Advanced example
            >>> result = algorand.send.asset_opt_in(AssetOptInParams(
            >>>  sender="SENDERADDRESS",
            >>>  asset_id=123456,
            >>>  lease="lease",
            >>>  note="note",
            >>>  # You wouldn't normally set this field
            >>>  first_valid_round=1000,
            >>>  validity_window=10,
            >>>  extra_fee=AlgoAmount(micro_algo=1000),
            >>>  static_fee=AlgoAmount(micro_algo=1000),
            >>>  # Max fee doesn't make sense with extraFee AND staticFee
            >>>  #  already specified, but here for completeness
            >>>  max_fee=AlgoAmount(micro_algo=3000),
            >>>  # Signer only needed if you want to provide one,
            >>>  #  generally you'd register it with AlgorandClient
            >>>  #  against the sender and not need to pass it in
            >>>  signer=transactionSigner
            >>> ), send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
        """
        return self._send(
            lambda c: c.add_asset_opt_in,
            pre_log=lambda params, transaction: (
                f"Opting in {params.sender} to asset with ID {params.asset_id} via transaction {transaction.tx_id()}"
            ),
        )(params, send_params)

    def asset_opt_out(
        self,
        params: AssetOptOutParams,
        send_params: SendParams | None = None,
        *,
        ensure_zero_balance: bool = True,
    ) -> SendSingleTransactionResult:
        """Opt an account out of an Algorand Standard Asset.

        :param params: Asset opt-out parameters
        :param send_params: Send parameters
        :param ensure_zero_balance: Check if account has zero balance before opt-out, defaults to True
        :raises ValueError: If account has non-zero balance or is not opted in
        :return: Result of the opt-out transaction

        :example:
            >>> result = algorand.send.asset_opt_out(AssetOptOutParams(
            >>>  sender="SENDERADDRESS",
            >>>  creator="CREATORADDRESS",
            >>>  asset_id=123456,
            >>>  ensure_zero_balance=True,
            >>> ))

            >>> # Advanced example
            >>> result = algorand.send.asset_opt_out(AssetOptOutParams(
            >>>  sender="SENDERADDRESS",
            >>>  asset_id=123456,
            >>>  creator="CREATORADDRESS",
            >>>  ensure_zero_balance=True,
            >>>  lease="lease",
            >>>  note="note",
            >>>  # You wouldn't normally set this field
            >>>  first_valid_round=1000,
            >>>  validity_window=10,
            >>>  extra_fee=AlgoAmount(micro_algo=1000),
            >>>  static_fee=AlgoAmount(micro_algo=1000),
            >>>  # Max fee doesn't make sense with extraFee AND staticFee
            >>>  #  already specified, but here for completeness
            >>>  max_fee=AlgoAmount(micro_algo=3000),
            >>>  # Signer only needed if you want to provide one,
            >>>  #  generally you'd register it with AlgorandClient
            >>>  #  against the sender and not need to pass it in
            >>>  signer=transactionSigner
            >>> ), send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
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
                    f"Account {params.sender} is not opted-in to Asset {params.asset_id}; can't opt-out."
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
                f"{creator} via transaction {transaction.tx_id()}"
            ),
        )(params, send_params)

    def app_create(
        self, params: AppCreateParams, send_params: SendParams | None = None
    ) -> SendAppCreateTransactionResult[ABIReturn]:
        """Create a new application.

        :param params: Application creation parameters
        :param send_params: Send parameters
        :return: Result containing the new application ID and address

        :example:
            >>> result = algorand.send.app_create(AppCreateParams(
            >>>  sender="CREATORADDRESS",
            >>>  approval_program="TEALCODE",
            >>>  clear_state_program="TEALCODE",
            >>> ))

            >>> # Advanced example
            >>> result = algorand.send.app_create(AppCreateParams(
            >>>  sender="CREATORADDRESS",
            >>>  approval_program="TEALCODE",
            >>>  clear_state_program="TEALCODE",
            >>> ))
            >>> # algorand.send.appCreate(AppCreateParams(
            >>> #  sender='CREATORADDRESS',
            >>> #  approval_program="TEALCODE",
            >>> #  clear_state_program="TEALCODE",
            >>> #  schema={
            >>> #    "global_ints": 1,
            >>> #    "global_byte_slices": 2,
            >>> #    "local_ints": 3,
            >>> #    "local_byte_slices": 4
            >>> #  },
            >>> #  extra_program_pages: 1,
            >>> #  on_complete: algosdk.transaction.OnApplicationComplete.OptInOC,
            >>> #  args: [b'some_bytes']
            >>> #  account_references: ["ACCOUNT_1"]
            >>> #  app_references: [123, 1234]
            >>> #  asset_references: [12345]
            >>> #  box_references: ["box1", {app_id: 1234, name: "box2"}]
            >>> #  lease: 'lease',
            >>> #  note: 'note',
            >>> #  # You wouldn't normally set this field
            >>> #  first_valid_round: 1000,
            >>> #  validity_window: 10,
            >>> #  extra_fee: AlgoAmount(micro_algo=1000),
            >>> #  static_fee: AlgoAmount(micro_algo=1000),
            >>> #  # Max fee doesn't make sense with extraFee AND staticFee
            >>> #  #  already specified, but here for completeness
            >>> #  max_fee: AlgoAmount(micro_algo=3000),
            >>> #  # Signer only needed if you want to provide one,
            >>> #  #  generally you'd register it with AlgorandClient
            >>> #  #  against the sender and not need to pass it in
            >>> #  signer: transactionSigner
            >>> #}, send_params=SendParams(
            >>> #  max_rounds_to_wait_for_confirmation=5,
            >>> #  suppress_log=True,
            >>> #))
        """
        return self._send_app_create_call(lambda c: c.add_app_create)(params, send_params)

    def app_update(
        self, params: AppUpdateParams, send_params: SendParams | None = None
    ) -> SendAppUpdateTransactionResult[ABIReturn]:
        """Update an application.

        :param params: Application update parameters
        :param send_params: Send parameters
        :return: Result containing the compiled programs

        :example:
            >>> # Basic example
            >>> algorand.send.app_update(AppUpdateParams(
            >>>  sender="CREATORADDRESS",
            >>>  approval_program="TEALCODE",
            >>>  clear_state_program="TEALCODE",
            >>> ))
            >>> # Advanced example
            >>> algorand.send.app_update(AppUpdateParams(
            >>>  sender="CREATORADDRESS",
            >>>  approval_program="TEALCODE",
            >>>  clear_state_program="TEALCODE",
            >>>  on_complete=OnApplicationComplete.UpdateApplication,
            >>>  args=[b'some_bytes'],
            >>>  account_references=["ACCOUNT_1"],
            >>>  app_references=[123, 1234],
            >>>  asset_references=[12345],
            >>>  box_references=[...],
            >>>  lease="lease",
            >>>  note="note",
            >>>  # You wouldn't normally set this field
            >>>  first_valid_round=1000,
            >>>  validity_window=10,
            >>>  extra_fee=AlgoAmount(micro_algo=1000),
            >>>  static_fee=AlgoAmount(micro_algo=1000),
            >>>  # Max fee doesn't make sense with extraFee AND staticFee
            >>>  #  already specified, but here for completeness
            >>>  max_fee=AlgoAmount(micro_algo=3000),
            >>>  # Signer only needed if you want to provide one,
            >>>  #  generally you'd register it with AlgorandClient
            >>>  #  against the sender and not need to pass it in
            >>>  signer=transactionSigner
            >>> ), send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
        """
        return self._send_app_update_call(lambda c: c.add_app_update)(params, send_params)

    def app_delete(
        self, params: AppDeleteParams, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[ABIReturn]:
        """Delete an application.

        :param params: Application deletion parameters
        :param send_params: Send parameters
        :return: Result of the deletion transaction

        :example:
            >>> # Basic example
            >>> algorand.send.app_delete(AppDeleteParams(
            >>>  sender="CREATORADDRESS",
            >>>  app_id=123456,
            >>> ))
            >>> # Advanced example
            >>> algorand.send.app_delete(AppDeleteParams(
            >>>  sender="CREATORADDRESS",
            >>>  on_complete=OnApplicationComplete.DeleteApplication,
            >>>  args=[b'some_bytes'],
            >>>  account_references=["ACCOUNT_1"],
            >>>  app_references=[123, 1234],
            >>>  asset_references=[12345],
            >>>  box_references=[...],
            >>>  lease="lease",
            >>>  note="note",
            >>>  # You wouldn't normally set this field
            >>>  first_valid_round=1000,
            >>>  validity_window=10,
            >>>  extra_fee=AlgoAmount(micro_algo=1000),
            >>>  static_fee=AlgoAmount(micro_algo=1000),
            >>>  # Max fee doesn't make sense with extraFee AND staticFee
            >>>  #  already specified, but here for completeness
            >>>  max_fee=AlgoAmount(micro_algo=3000),
            >>>  # Signer only needed if you want to provide one,
            >>>  #  generally you'd register it with AlgorandClient
            >>>  #  against the sender and not need to pass it in
            >>>  signer=transactionSigner,
            >>> ), send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
        """
        return self._send_app_call(lambda c: c.add_app_delete)(params, send_params)

    def app_call(
        self, params: AppCallParams, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[ABIReturn]:
        """Call an application.

        :param params: Application call parameters
        :param send_params: Send parameters
        :return: Result containing any ABI return value

        :example:
            >>> # Basic example
            >>> algorand.send.app_call(AppCallParams(
            >>>  sender="CREATORADDRESS",
            >>>  app_id=123456,
            >>> ))
            >>> # Advanced example
            >>> algorand.send.app_call(AppCallParams(
            >>>  sender="CREATORADDRESS",
            >>>  on_complete=OnApplicationComplete.OptInOC,
            >>>  args=[b'some_bytes'],
            >>>  account_references=["ACCOUNT_1"],
            >>>  app_references=[123, 1234],
            >>>  asset_references=[12345],
            >>>  box_references=[...],
            >>>  lease="lease",
            >>>  note="note",
            >>>  # You wouldn't normally set this field
            >>>  first_valid_round=1000,
            >>>  validity_window=10,
            >>>  extra_fee=AlgoAmount(micro_algo=1000),
            >>>  static_fee=AlgoAmount(micro_algo=1000),
            >>>  # Max fee doesn't make sense with extraFee AND staticFee
            >>>  #  already specified, but here for completeness
            >>>  max_fee=AlgoAmount(micro_algo=3000),
            >>>  # Signer only needed if you want to provide one,
            >>>  #  generally you'd register it with AlgorandClient
            >>>  #  against the sender and not need to pass it in
            >>>  signer=transactionSigner,
            >>> ), send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
        """
        return self._send_app_call(lambda c: c.add_app_call)(params, send_params)

    def app_create_method_call(
        self, params: AppCreateMethodCallParams, send_params: SendParams | None = None
    ) -> SendAppCreateTransactionResult[ABIReturn]:
        """Call an application's create method.

        :param params: Method call parameters for application creation
        :param send_params: Send parameters
        :return: Result containing the new application ID and address

        :example:
            >>> # Note: you may prefer to use `algorand.client` to get an app client for more advanced functionality.
            >>> #
            >>> # @param params The parameters for the app creation transaction
            >>> # Basic example
            >>> method = algorand.abi.Method(
            >>>   name='method',
            >>>   args=[b'arg1'],
            >>>   returns='string'
            >>> )
            >>> result = algorand.send.app_create_method_call({ sender: 'CREATORADDRESS',
            >>>   approval_program: 'TEALCODE',
            >>>   clear_state_program: 'TEALCODE',
            >>>   method: method,
            >>>   args: ["arg1_value"] })
            >>> created_app_id = result.app_id
            >>> ...
            >>> # Advanced example
            >>> method = algorand.abi.Method(
            >>>   name='method',
            >>>   args=[b'arg1'],
            >>>   returns='string'
            >>> )
            >>> result = algorand.send.app_create_method_call({
            >>>  sender: 'CREATORADDRESS',
            >>>  method: method,
            >>>  args: ["arg1_value"],
            >>>  approval_program: "TEALCODE",
            >>>  clear_state_program: "TEALCODE",
            >>>  schema: {
            >>>    "global_ints": 1,
            >>>    "global_byte_slices": 2,
            >>>    "local_ints": 3,
            >>>    "local_byte_slices": 4
            >>>  },
            >>>  extra_program_pages: 1,
            >>>  on_complete: algosdk.transaction.OnApplicationComplete.OptInOC,
            >>>  args: [new Uint8Array(1, 2, 3, 4)],
            >>>  account_references: ["ACCOUNT_1"],
            >>>  app_references: [123, 1234],
            >>>  asset_references: [12345],
            >>>  box_references: [...],
            >>>  lease: 'lease',
            >>>  note: 'note',
            >>>  # You wouldn't normally set this field
            >>>  first_valid_round: 1000,
            >>>  validity_window: 10,
            >>>  extra_fee: AlgoAmount(micro_algo=1000),
            >>>  static_fee: AlgoAmount(micro_algo=1000),
            >>>  # Max fee doesn't make sense with extraFee AND staticFee
            >>>  #  already specified, but here for completeness
            >>>  max_fee: AlgoAmount(micro_algo=3000),
            >>>  # Signer only needed if you want to provide one,
            >>>  #  generally you'd register it with AlgorandClient
            >>>  #  against the sender and not need to pass it in
            >>>  signer: transactionSigner,
            >>> }, send_params=SendParams(
            >>>  max_rounds_to_wait_for_confirmation=5,
            >>>  suppress_log=True,
            >>> ))
        """
        return self._send_app_create_call(lambda c: c.add_app_create_method_call)(params, send_params)

    def app_update_method_call(
        self, params: AppUpdateMethodCallParams, send_params: SendParams | None = None
    ) -> SendAppUpdateTransactionResult[ABIReturn]:
        """Call an application's update method.

        :param params: Method call parameters for application update
        :param send_params: Send parameters
        :return: Result containing the compiled programs

        :example:
            # Basic example:
            >>> method = algorand.abi.Method(
            ...     name="updateMethod",
            ...     args=[{"type": "string", "name": "arg1"}],
            ...     returns="string"
            ... )
            >>> params = AppUpdateMethodCallParams(
            ...     sender="CREATORADDRESS",
            ...     app_id=123,
            ...     method=method,
            ...     args=["new_value"],
            ...     approval_program="TEALCODE",
            ...     clear_state_program="TEALCODE"
            ... )
            >>> result = algorand.send.app_update_method_call(params)
            >>> print(result.compiled_approval, result.compiled_clear)

            # Advanced example:
            >>> method = algorand.abi.Method(
            ...     name="updateMethod",
            ...     args=[{"type": "string", "name": "arg1"}, {"type": "uint64", "name": "arg2"}],
            ...     returns="string"
            ... )
            >>> params = AppUpdateMethodCallParams(
            ...     sender="CREATORADDRESS",
            ...     app_id=456,
            ...     method=method,
            ...     args=["new_value", 42],
            ...     approval_program="TEALCODE_ADVANCED",
            ...     clear_state_program="TEALCLEAR_ADVANCED",
            ...     account_references=["ACCOUNT1", "ACCOUNT2"],
            ...     app_references=[789],
            ...     asset_references=[101112]
            ... )
            >>> result = algorand.send.app_update_method_call(params)
            >>> print(result.compiled_approval, result.compiled_clear)
        """
        return self._send_app_update_call(lambda c: c.add_app_update_method_call)(params, send_params)

    def app_delete_method_call(
        self, params: AppDeleteMethodCallParams, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[ABIReturn]:
        """Call an application's delete method.

        :param params: Method call parameters for application deletion
        :param send_params: Send parameters
        :return: Result of the deletion transaction

        :example:
            # Basic example:
            >>> method = algorand.abi.Method(
            ...     name="deleteMethod",
            ...     args=[],
            ...     returns="void"
            ... )
            >>> params = AppDeleteMethodCallParams(
            ...     sender="CREATORADDRESS",
            ...     app_id=123,
            ...     method=method
            ... )
            >>> result = algorand.send.app_delete_method_call(params)
            >>> print(result.tx_id)

            # Advanced example:
            >>> method = algorand.abi.Method(
            ...     name="deleteMethod",
            ...     args=[{"type": "uint64", "name": "confirmation"}],
            ...     returns="void"
            ... )
            >>> params = AppDeleteMethodCallParams(
            ...     sender="CREATORADDRESS",
            ...     app_id=123,
            ...     method=method,
            ...     args=[1],
            ...     account_references=["ACCOUNT1"],
            ...     app_references=[456]
            ... )
            >>> result = algorand.send.app_delete_method_call(params)
            >>> print(result.tx_id)
        """
        return self._send_app_call(lambda c: c.add_app_delete_method_call)(params, send_params)

    def app_call_method_call(
        self, params: AppCallMethodCallParams, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[ABIReturn]:
        """Call an application's call method.

        :param params: Method call parameters
        :param send_params: Send parameters
        :return: Result containing any ABI return value

        :example:
            # Basic example:
            >>> method = algorand.abi.Method(
            ...     name="callMethod",
            ...     args=[{"type": "uint64", "name": "arg1"}],
            ...     returns="uint64"
            ... )
            >>> params = AppCallMethodCallParams(
            ...     sender="CALLERADDRESS",
            ...     app_id=123,
            ...     method=method,
            ...     args=[12345]
            ... )
            >>> result = algorand.send.app_call_method_call(params)
            >>> print(result.abi_return)

            # Advanced example:
            >>> method = algorand.abi.Method(
            ...     name="callMethod",
            ...     args=[{"type": "uint64", "name": "arg1"}, {"type": "string", "name": "arg2"}],
            ...     returns="uint64"
            ... )
            >>> params = AppCallMethodCallParams(
            ...     sender="CALLERADDRESS",
            ...     app_id=123,
            ...     method=method,
            ...     args=[12345, "extra"],
            ...     account_references=["ACCOUNT1"],
            ...     asset_references=[101112],
            ...     app_references=[789]
            ... )
            >>> result = algorand.send.app_call_method_call(params)
            >>> print(result.abi_return)
        """
        return self._send_app_call(lambda c: c.add_app_call_method_call)(params, send_params)

    def online_key_registration(
        self, params: OnlineKeyRegistrationParams, send_params: SendParams | None = None
    ) -> SendSingleTransactionResult:
        """Register an online key.

        :param params: Key registration parameters
        :param send_params: Send parameters
        :return: Result of the registration transaction

        :example:
            # Basic example:
            >>> params = OnlineKeyRegistrationParams(
            ...     sender="ACCOUNTADDRESS",
            ...     vote_key="VOTEKEY",
            ...     selection_key="SELECTIONKEY",
            ...     vote_first=1000,
            ...     vote_last=2000,
            ...     vote_key_dilution=10
            ... )
            >>> result = algorand.send.online_key_registration(params)
            >>> print(result.tx_id)

            # Advanced example:
            >>> params = OnlineKeyRegistrationParams(
            ...     sender="ACCOUNTADDRESS",
            ...     vote_key="VOTEKEY",
            ...     selection_key="SELECTIONKEY",
            ...     vote_first=1000,
            ...     vote_last=2100,
            ...     vote_key_dilution=10,
            ...     state_proof_key=b'\x01' * 64
            ... )
            >>> result = algorand.send.online_key_registration(params)
            >>> print(result.tx_id)
        """
        return self._send(
            lambda c: c.add_online_key_registration,
            pre_log=lambda params, transaction: (
                f"Registering online key for {params.sender} via transaction {transaction.tx_id()}"
            ),
        )(params, send_params)

    def offline_key_registration(
        self, params: OfflineKeyRegistrationParams, send_params: SendParams | None = None
    ) -> SendSingleTransactionResult:
        """Register an offline key.

        :param params: Key registration parameters
        :param send_params: Send parameters
        :return: Result of the registration transaction

        :example:
            # Basic example:
            >>> params = OfflineKeyRegistrationParams(
            ...     sender="ACCOUNTADDRESS",
            ...     prevent_account_from_ever_participating_again=True
            ... )
            >>> result = algorand.send.offline_key_registration(params)
            >>> print(result.tx_id)

            # Advanced example:
            >>> params = OfflineKeyRegistrationParams(
            ...     sender="ACCOUNTADDRESS",
            ...     prevent_account_from_ever_participating_again=True,
            ...     note=b'Offline registration'
            ... )
            >>> result = algorand.send.offline_key_registration(params)
            >>> print(result.tx_id)
        """
        return self._send(
            lambda c: c.add_offline_key_registration,
            pre_log=lambda params, transaction: (
                f"Registering offline key for {params.sender} via transaction {transaction.tx_id()}"
            ),
        )(params, send_params)
