from __future__ import annotations

import base64
import json
import math
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypedDict, Union

import algosdk
import algosdk.atomic_transaction_composer
import algosdk.v2client.models
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    SimulateAtomicTransactionResponse,
    TransactionSigner,
    TransactionWithSigner,
)
from algosdk.transaction import OnComplete
from algosdk.v2client.algod import AlgodClient
from typing_extensions import deprecated

from algokit_utils._debugging import simulate_and_persist_response, simulate_response
from algokit_utils.applications.abi import ABIReturn
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.applications.app_spec.arc56 import Method as Arc56Method
from algokit_utils.config import config
from algokit_utils.models.transaction import SendParams, TransactionWrapper
from algokit_utils.transactions.utils import encode_lease, populate_app_call_resources

if TYPE_CHECKING:
    from collections.abc import Callable

    from algosdk.abi import Method
    from algosdk.v2client.algod import AlgodClient
    from algosdk.v2client.models import SimulateTraceConfig

    from algokit_utils.applications.abi import ABIValue
    from algokit_utils.models.amount import AlgoAmount
    from algokit_utils.models.state import BoxIdentifier, BoxReference
    from algokit_utils.models.transaction import Arc2TransactionNote


__all__ = [
    "AppCallMethodCallParams",
    "AppCallParams",
    "AppCreateMethodCallParams",
    "AppCreateParams",
    "AppCreateSchema",
    "AppDeleteMethodCallParams",
    "AppDeleteParams",
    "AppMethodCallTransactionArgument",
    "AppUpdateMethodCallParams",
    "AppUpdateParams",
    "AssetConfigParams",
    "AssetCreateParams",
    "AssetDestroyParams",
    "AssetFreezeParams",
    "AssetOptInParams",
    "AssetOptOutParams",
    "AssetTransferParams",
    "BuiltTransactions",
    "MethodCallParams",
    "OfflineKeyRegistrationParams",
    "OnlineKeyRegistrationParams",
    "PaymentParams",
    "SendAtomicTransactionComposerResults",
    "TransactionComposer",
    "TransactionComposerBuildResult",
    "TxnParams",
    "send_atomic_transaction_composer",
]


logger = config.logger


@dataclass(kw_only=True, frozen=True)
class _CommonTxnParams:
    sender: str
    signer: TransactionSigner | None = None
    rekey_to: str | None = None
    note: bytes | None = None
    lease: bytes | None = None
    static_fee: AlgoAmount | None = None
    extra_fee: AlgoAmount | None = None
    max_fee: AlgoAmount | None = None
    validity_window: int | None = None
    first_valid_round: int | None = None
    last_valid_round: int | None = None


@dataclass(kw_only=True, frozen=True)
class _CommonTxnWithSendParams(_CommonTxnParams, SendParams):
    pass


@dataclass(kw_only=True, frozen=True)
class PaymentParams(_CommonTxnWithSendParams):
    """Parameters for a payment transaction.

    :ivar receiver: The account that will receive the ALGO
    :ivar amount: Amount to send
    :ivar close_remainder_to: If given, close the sender account and send the remaining balance to this address,
    defaults to None
    """

    receiver: str
    amount: AlgoAmount
    close_remainder_to: str | None = None


@dataclass(kw_only=True, frozen=True)
class AssetCreateParams(_CommonTxnWithSendParams):
    """Parameters for creating a new asset.

    :ivar total: The total amount of the smallest divisible unit to create
    :ivar decimals: The amount of decimal places the asset should have, defaults to None
    :ivar default_frozen: Whether the asset is frozen by default in the creator address, defaults to None
    :ivar manager: The address that can change the manager, reserve, clawback, and freeze addresses, defaults to None
    :ivar reserve: The address that holds the uncirculated supply, defaults to None
    :ivar freeze: The address that can freeze the asset in any account, defaults to None
    :ivar clawback: The address that can clawback the asset from any account, defaults to None
    :ivar unit_name: The short ticker name for the asset, defaults to None
    :ivar asset_name: The full name of the asset, defaults to None
    :ivar url: The metadata URL for the asset, defaults to None
    :ivar metadata_hash: Hash of the metadata contained in the metadata URL, defaults to None
    """

    total: int
    asset_name: str | None = None
    unit_name: str | None = None
    url: str | None = None
    decimals: int | None = None
    default_frozen: bool | None = None
    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None
    metadata_hash: bytes | None = None


@dataclass(kw_only=True, frozen=True)
class AssetConfigParams(_CommonTxnWithSendParams):
    """Parameters for configuring an existing asset.

    :ivar asset_id: ID of the asset
    :ivar manager: The address that can change the manager, reserve, clawback, and freeze addresses, defaults to None
    :ivar reserve: The address that holds the uncirculated supply, defaults to None
    :ivar freeze: The address that can freeze the asset in any account, defaults to None
    :ivar clawback: The address that can clawback the asset from any account, defaults to None
    """

    asset_id: int
    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None


@dataclass(kw_only=True, frozen=True)
class AssetFreezeParams(_CommonTxnWithSendParams):
    """Parameters for freezing an asset.

    :ivar asset_id: The ID of the asset
    :ivar account: The account to freeze or unfreeze
    :ivar frozen: Whether the assets in the account should be frozen
    """

    asset_id: int
    account: str
    frozen: bool


@dataclass(kw_only=True, frozen=True)
class AssetDestroyParams(_CommonTxnWithSendParams):
    """Parameters for destroying an asset.

    :ivar asset_id: ID of the asset
    """

    asset_id: int


@dataclass(kw_only=True, frozen=True)
class OnlineKeyRegistrationParams(_CommonTxnWithSendParams):
    """Parameters for online key registration.

    :ivar vote_key: The root participation public key
    :ivar selection_key: The VRF public key
    :ivar vote_first: The first round that the participation key is valid
    :ivar vote_last: The last round that the participation key is valid
    :ivar vote_key_dilution: The dilution for the 2-level participation key
    :ivar state_proof_key: The 64 byte state proof public key commitment, defaults to None
    """

    vote_key: str
    selection_key: str
    vote_first: int
    vote_last: int
    vote_key_dilution: int
    state_proof_key: bytes | None = None


@dataclass(kw_only=True, frozen=True)
class OfflineKeyRegistrationParams(_CommonTxnWithSendParams):
    """Parameters for offline key registration.

    :ivar prevent_account_from_ever_participating_again: Whether to prevent the account from ever participating again
    """

    prevent_account_from_ever_participating_again: bool


@dataclass(kw_only=True, frozen=True)
class AssetTransferParams(_CommonTxnWithSendParams):
    """Parameters for transferring an asset.

    :ivar asset_id: ID of the asset
    :ivar amount: Amount of the asset to transfer (smallest divisible unit)
    :ivar receiver: The account to send the asset to
    :ivar clawback_target: The account to take the asset from, defaults to None
    :ivar close_asset_to: The account to close the asset to, defaults to None
    """

    asset_id: int
    amount: int
    receiver: str
    clawback_target: str | None = None
    close_asset_to: str | None = None


@dataclass(kw_only=True, frozen=True)
class AssetOptInParams(_CommonTxnWithSendParams):
    """Parameters for opting into an asset.

    :ivar asset_id: ID of the asset
    """

    asset_id: int


@dataclass(kw_only=True, frozen=True)
class AssetOptOutParams(_CommonTxnWithSendParams):
    """Parameters for opting out of an asset.

    :ivar asset_id: ID of the asset
    :ivar creator: The creator address of the asset
    """

    asset_id: int
    creator: str


@dataclass(kw_only=True, frozen=True)
class AppCallParams(_CommonTxnWithSendParams):
    """Parameters for calling an application.

    :ivar on_complete: The OnComplete action
    :ivar app_id: ID of the application, defaults to None
    :ivar approval_program: The program to execute for all OnCompletes other than ClearState, defaults to None
    :ivar clear_state_program: The program to execute for ClearState OnComplete, defaults to None
    :ivar schema: The state schema for the app. This is immutable, defaults to None
    :ivar args: Application arguments, defaults to None
    :ivar account_references: Account references, defaults to None
    :ivar app_references: App references, defaults to None
    :ivar asset_references: Asset references, defaults to None
    :ivar extra_pages: Number of extra pages required for the programs, defaults to None
    :ivar box_references: Box references, defaults to None
    """

    on_complete: OnComplete
    app_id: int | None = None
    approval_program: str | bytes | None = None
    clear_state_program: str | bytes | None = None
    schema: dict[str, int] | None = None
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    extra_pages: int | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None


class AppCreateSchema(TypedDict):
    global_ints: int
    global_byte_slices: int
    local_ints: int
    local_byte_slices: int


@dataclass(kw_only=True, frozen=True)
class AppCreateParams(_CommonTxnWithSendParams):
    """Parameters for creating an application.

    :ivar approval_program: The program to execute for all OnCompletes other than ClearState as raw teal (string)
    or compiled teal (bytes)
    :ivar clear_state_program: The program to execute for ClearState OnComplete as raw teal (string)
    or compiled teal (bytes)
    :ivar schema: The state schema for the app. This is immutable, defaults to None
    :ivar on_complete: The OnComplete action (cannot be ClearState), defaults to None
    :ivar args: Application arguments, defaults to None
    :ivar account_references: Account references, defaults to None
    :ivar app_references: App references, defaults to None
    :ivar asset_references: Asset references, defaults to None
    :ivar box_references: Box references, defaults to None
    :ivar extra_program_pages: Number of extra pages required for the programs, defaults to None
    """

    approval_program: str | bytes
    clear_state_program: str | bytes
    schema: AppCreateSchema | None = None
    on_complete: OnComplete | None = None
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None
    extra_program_pages: int | None = None


@dataclass(kw_only=True, frozen=True)
class AppUpdateParams(_CommonTxnWithSendParams):
    """Parameters for updating an application.

    :ivar app_id: ID of the application
    :ivar approval_program: The program to execute for all OnCompletes other than ClearState as raw teal (string)
    or compiled teal (bytes)
    :ivar clear_state_program: The program to execute for ClearState OnComplete as raw teal (string)
    or compiled teal (bytes)
    :ivar args: Application arguments, defaults to None
    :ivar account_references: Account references, defaults to None
    :ivar app_references: App references, defaults to None
    :ivar asset_references: Asset references, defaults to None
    :ivar box_references: Box references, defaults to None
    :ivar on_complete: The OnComplete action, defaults to None
    """

    app_id: int
    approval_program: str | bytes
    clear_state_program: str | bytes
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None
    on_complete: OnComplete | None = None


@dataclass(kw_only=True, frozen=True)
class AppDeleteParams(_CommonTxnWithSendParams):
    """Parameters for deleting an application.

    :ivar app_id: ID of the application
    :ivar args: Application arguments, defaults to None
    :ivar account_references: Account references, defaults to None
    :ivar app_references: App references, defaults to None
    :ivar asset_references: Asset references, defaults to None
    :ivar box_references: Box references, defaults to None
    :ivar on_complete: The OnComplete action, defaults to DeleteApplicationOC
    """

    app_id: int
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None
    on_complete: OnComplete = OnComplete.DeleteApplicationOC


@dataclass(kw_only=True, frozen=True)
class _BaseAppMethodCall(_CommonTxnWithSendParams):
    app_id: int
    method: Method
    args: list | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None
    schema: AppCreateSchema | None = None


@dataclass(kw_only=True, frozen=True)
class AppMethodCallParams(_CommonTxnWithSendParams):
    """Parameters for calling an application method.

    :ivar app_id: ID of the application
    :ivar method: The ABI method to call
    :ivar args: Arguments to the ABI method, defaults to None
    :ivar on_complete: The OnComplete action (cannot be UpdateApplication or ClearState), defaults to None
    :ivar account_references: Account references, defaults to None
    :ivar app_references: App references, defaults to None
    :ivar asset_references: Asset references, defaults to None
    :ivar box_references: Box references, defaults to None
    """

    app_id: int
    method: Method
    args: list[bytes] | None = None
    on_complete: OnComplete | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None


@dataclass(kw_only=True, frozen=True)
class AppCallMethodCallParams(_BaseAppMethodCall):
    """Parameters for a regular ABI method call.

    :ivar app_id: ID of the application
    :ivar method: The ABI method to call
    :ivar args: Arguments to the ABI method, either an ABI value, transaction with explicit signer,
    transaction, another method call, or None
    :ivar on_complete: The OnComplete action (cannot be UpdateApplication or ClearState), defaults to None
    """

    app_id: int
    on_complete: OnComplete | None = None


@dataclass(kw_only=True, frozen=True)
class AppCreateMethodCallParams(_BaseAppMethodCall):
    """Parameters for an ABI method call that creates an application.

    :ivar approval_program: The program to execute for all OnCompletes other than ClearState
    :ivar clear_state_program: The program to execute for ClearState OnComplete
    :ivar schema: The state schema for the app, defaults to None
    :ivar on_complete: The OnComplete action (cannot be ClearState), defaults to None
    :ivar extra_program_pages: Number of extra pages required for the programs, defaults to None
    """

    approval_program: str | bytes
    clear_state_program: str | bytes
    schema: AppCreateSchema | None = None
    on_complete: OnComplete | None = None
    extra_program_pages: int | None = None


@dataclass(kw_only=True, frozen=True)
class AppUpdateMethodCallParams(_BaseAppMethodCall):
    """Parameters for an ABI method call that updates an application.

    :ivar app_id: ID of the application
    :ivar approval_program: The program to execute for all OnCompletes other than ClearState
    :ivar clear_state_program: The program to execute for ClearState OnComplete
    :ivar on_complete: The OnComplete action, defaults to UpdateApplicationOC
    """

    app_id: int
    approval_program: str | bytes
    clear_state_program: str | bytes
    on_complete: OnComplete = OnComplete.UpdateApplicationOC


@dataclass(kw_only=True, frozen=True)
class AppDeleteMethodCallParams(_BaseAppMethodCall):
    """Parameters for an ABI method call that deletes an application.

    :ivar app_id: ID of the application
    :ivar on_complete: The OnComplete action, defaults to DeleteApplicationOC
    """

    app_id: int
    on_complete: OnComplete = OnComplete.DeleteApplicationOC


MethodCallParams = (
    AppCallMethodCallParams | AppCreateMethodCallParams | AppUpdateMethodCallParams | AppDeleteMethodCallParams
)


AppMethodCallTransactionArgument = (
    TransactionWithSigner
    | algosdk.transaction.Transaction
    | AppCreateMethodCallParams
    | AppUpdateMethodCallParams
    | AppCallMethodCallParams
)


TxnParams = Union[  # noqa: UP007
    PaymentParams,
    AssetCreateParams,
    AssetConfigParams,
    AssetFreezeParams,
    AssetDestroyParams,
    OnlineKeyRegistrationParams,
    AssetTransferParams,
    AssetOptInParams,
    AssetOptOutParams,
    AppCallParams,
    AppCreateParams,
    AppUpdateParams,
    AppDeleteParams,
    MethodCallParams,
    OfflineKeyRegistrationParams,
]


@dataclass(frozen=True)
class BuiltTransactions:
    """Set of transactions built by TransactionComposer.

    :ivar transactions: The built transactions
    :ivar method_calls: Any ABIMethod objects associated with any of the transactions in a map keyed by txn id
    :ivar signers: Any TransactionSigner objects associated with any of the transactions in a map keyed by txn id
    """

    transactions: list[algosdk.transaction.Transaction]
    method_calls: dict[int, Method]
    signers: dict[int, TransactionSigner]


@dataclass
class TransactionComposerBuildResult:
    """Result of building transactions with TransactionComposer.

    :ivar atc: The AtomicTransactionComposer instance
    :ivar transactions: The list of transactions with signers
    :ivar method_calls: Map of transaction index to ABI method
    """

    atc: AtomicTransactionComposer
    transactions: list[TransactionWithSigner]
    method_calls: dict[int, Method]


@dataclass
class SendAtomicTransactionComposerResults:
    """Results from sending an AtomicTransactionComposer transaction group.

    :ivar group_id: The group ID if this was a transaction group
    :ivar confirmations: The confirmation info for each transaction
    :ivar tx_ids: The transaction IDs that were sent
    :ivar transactions: The transactions that were sent
    :ivar returns: The ABI return values from any ABI method calls
    :ivar simulate_response: The simulation response if simulation was performed, defaults to None
    """

    group_id: str
    confirmations: list[algosdk.v2client.algod.AlgodResponseType]
    tx_ids: list[str]
    transactions: list[TransactionWrapper]
    returns: list[ABIReturn]
    simulate_response: dict[str, Any] | None = None


def send_atomic_transaction_composer(  # noqa: C901, PLR0912
    atc: AtomicTransactionComposer,
    algod: AlgodClient,
    *,
    max_rounds_to_wait: int | None = 5,
    skip_waiting: bool = False,
    suppress_log: bool | None = None,
    populate_resources: bool | None = None,
) -> SendAtomicTransactionComposerResults:
    """Send an AtomicTransactionComposer transaction group.

    Executes a group of transactions atomically using the AtomicTransactionComposer.

    :param atc: The AtomicTransactionComposer instance containing the transaction group to send
    :param algod: The Algod client to use for sending the transactions
    :param max_rounds_to_wait: Maximum number of rounds to wait for confirmation, defaults to 5
    :param skip_waiting: If True, don't wait for transaction confirmation, defaults to False
    :param suppress_log: If True, suppress logging, defaults to None
    :param populate_resources: If True, populate app call resources, defaults to None
    :return: Results from sending the transaction group
    :raises Exception: If there is an error sending the transactions
    :raises error: If there is an error from the Algorand node
    """

    try:
        # Build transactions
        transactions_with_signer = atc.build_group()

        if populate_resources or (
            populate_resources is None
            and config.populate_app_call_resource
            and any(isinstance(t.txn, algosdk.transaction.ApplicationCallTxn) for t in transactions_with_signer)
        ):
            atc = populate_app_call_resources(atc, algod)

        transactions_to_send = [t.txn for t in transactions_with_signer]

        # Get group ID if multiple transactions
        group_id = None
        if len(transactions_to_send) > 1:
            group_id = (
                base64.b64encode(transactions_to_send[0].group).decode("utf-8") if transactions_to_send[0].group else ""
            )

            if not suppress_log:
                logger.info(f"Sending group of {len(transactions_to_send)} transactions ({group_id})")
                logger.debug(f"Transaction IDs ({group_id}): {[t.get_txid() for t in transactions_to_send]}")

        # Simulate if debug enabled
        if config.debug and config.trace_all and config.project_root:
            simulate_and_persist_response(
                atc,
                config.project_root,
                algod,
                config.trace_buffer_size_mb,
            )

        # Execute transactions
        result = atc.execute(algod, wait_rounds=max_rounds_to_wait or 5)

        # Log results
        if not suppress_log:
            if len(transactions_to_send) > 1:
                logger.info(f"Group transaction ({group_id}) sent with {len(transactions_to_send)} transactions")
            else:
                logger.info(f"Sent transaction ID {transactions_to_send[0].get_txid()}")

        # Get confirmations if not skipping
        confirmations = None
        if not skip_waiting:
            confirmations = [algod.pending_transaction_info(t.get_txid()) for t in transactions_to_send]

        # Return results
        return SendAtomicTransactionComposerResults(
            group_id=group_id or "",
            confirmations=confirmations or [],
            tx_ids=[t.get_txid() for t in transactions_to_send],
            transactions=[TransactionWrapper(t) for t in transactions_to_send],
            returns=[ABIReturn(r) for r in result.abi_results],
        )

    except Exception as e:
        # Handle error with debug info if enabled
        if config.debug:
            logger.error(
                "Received error executing Atomic Transaction Composer and debug flag enabled; "
                "attempting simulation to get more information"
            )

            simulate = None
            if config.project_root and not config.trace_all:
                # Only simulate if trace_all is disabled and project_root is set
                simulate = simulate_and_persist_response(atc, config.project_root, algod, config.trace_buffer_size_mb)
            else:
                simulate = simulate_response(atc, algod)

            traces = []
            if simulate and simulate.failed_at:
                for txn_group in simulate.simulate_response["txn-groups"]:
                    app_budget = txn_group.get("app-budget-added")
                    app_budget_consumed = txn_group.get("app-budget-consumed")
                    failure_message = txn_group.get("failure-message")
                    txn_result = txn_group.get("txn-results", [{}])[0]
                    exec_trace = txn_result.get("exec-trace", {})

                    traces.append(
                        {
                            "trace": exec_trace,
                            "app_budget": app_budget,
                            "app_budget_consumed": app_budget_consumed,
                            "failure_message": failure_message,
                        }
                    )

            error = Exception(f"Transaction failed: {e}")
            error.traces = traces  # type: ignore[attr-defined]
            raise error from e

        logger.error("Received error executing Atomic Transaction Composer, for more information enable the debug flag")
        raise e


class TransactionComposer:
    """A class for composing and managing Algorand transactions.

    Provides a high-level interface for building and executing transaction groups using the Algosdk library.
    Supports various transaction types including payments, asset operations, application calls, and key registrations.

    :cvar _NULL_SIGNER: A constant TransactionSigner representing an empty signer
    :vartype _NULL_SIGNER: TransactionSigner
    :param algod: An instance of AlgodClient used to get suggested params and send transactions
    :param get_signer: A function that takes an address and returns a TransactionSigner for that address
    :param get_suggested_params: Optional function to get suggested transaction parameters,
    defaults to using algod.suggested_params()
    :param default_validity_window: Optional default validity window for transactions in rounds, defaults to 10
    :param app_manager: Optional AppManager instance for compiling TEAL programs, defaults to None
    """

    _NULL_SIGNER: TransactionSigner = algosdk.atomic_transaction_composer.EmptySigner()

    def __init__(
        self,
        algod: AlgodClient,
        get_signer: Callable[[str], TransactionSigner],
        get_suggested_params: Callable[[], algosdk.transaction.SuggestedParams] | None = None,
        default_validity_window: int | None = None,
        app_manager: AppManager | None = None,
    ):
        self._txn_method_map: dict[str, algosdk.abi.Method] = {}
        self._txns: list[TransactionWithSigner | TxnParams | AtomicTransactionComposer] = []
        self._atc: AtomicTransactionComposer = AtomicTransactionComposer()
        self._algod: AlgodClient = algod
        self._default_get_send_params = lambda: self._algod.suggested_params()
        self._get_suggested_params = get_suggested_params or self._default_get_send_params
        self._get_signer: Callable[[str], TransactionSigner] = get_signer
        self._default_validity_window: int = default_validity_window or 10
        self._app_manager = app_manager or AppManager(algod)

    def add_transaction(
        self, transaction: algosdk.transaction.Transaction, signer: TransactionSigner | None = None
    ) -> TransactionComposer:
        """Add a raw transaction to the composer.

        :param transaction: The transaction to add
        :param signer: Optional transaction signer, defaults to getting signer from transaction sender
        :return: The transaction composer instance for chaining
        """
        self._txns.append(TransactionWithSigner(txn=transaction, signer=signer or self._get_signer(transaction.sender)))
        return self

    def add_payment(self, params: PaymentParams) -> TransactionComposer:
        """Add a payment transaction.

        :param params: The payment transaction parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_asset_create(self, params: AssetCreateParams) -> TransactionComposer:
        """Add an asset creation transaction.

        :param params: The asset creation parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_asset_config(self, params: AssetConfigParams) -> TransactionComposer:
        """Add an asset configuration transaction.

        :param params: The asset configuration parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_asset_freeze(self, params: AssetFreezeParams) -> TransactionComposer:
        """Add an asset freeze transaction.

        :param params: The asset freeze parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_asset_destroy(self, params: AssetDestroyParams) -> TransactionComposer:
        """Add an asset destruction transaction.

        :param params: The asset destruction parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_asset_transfer(self, params: AssetTransferParams) -> TransactionComposer:
        """Add an asset transfer transaction.

        :param params: The asset transfer parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_asset_opt_in(self, params: AssetOptInParams) -> TransactionComposer:
        """Add an asset opt-in transaction.

        :param params: The asset opt-in parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_asset_opt_out(self, params: AssetOptOutParams) -> TransactionComposer:
        """Add an asset opt-out transaction.

        :param params: The asset opt-out parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_app_create(self, params: AppCreateParams) -> TransactionComposer:
        """Add an application creation transaction.

        :param params: The application creation parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_app_update(self, params: AppUpdateParams) -> TransactionComposer:
        """Add an application update transaction.

        :param params: The application update parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_app_delete(self, params: AppDeleteParams) -> TransactionComposer:
        """Add an application deletion transaction.

        :param params: The application deletion parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_app_call(self, params: AppCallParams) -> TransactionComposer:
        """Add an application call transaction.

        :param params: The application call parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_app_create_method_call(self, params: AppCreateMethodCallParams) -> TransactionComposer:
        """Add an application creation method call transaction.

        :param params: The application creation method call parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_app_update_method_call(self, params: AppUpdateMethodCallParams) -> TransactionComposer:
        """Add an application update method call transaction.

        :param params: The application update method call parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_app_delete_method_call(self, params: AppDeleteMethodCallParams) -> TransactionComposer:
        """Add an application deletion method call transaction.

        :param params: The application deletion method call parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_app_call_method_call(self, params: AppCallMethodCallParams) -> TransactionComposer:
        """Add an application call method call transaction.

        :param params: The application call method call parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_online_key_registration(self, params: OnlineKeyRegistrationParams) -> TransactionComposer:
        """Add an online key registration transaction.

        :param params: The online key registration parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_offline_key_registration(self, params: OfflineKeyRegistrationParams) -> TransactionComposer:
        """Add an offline key registration transaction.

        :param params: The offline key registration parameters
        :return: The transaction composer instance for chaining
        """
        self._txns.append(params)
        return self

    def add_atc(self, atc: AtomicTransactionComposer) -> TransactionComposer:
        """Add an existing AtomicTransactionComposer's transactions.

        :param atc: The AtomicTransactionComposer to add
        :return: The transaction composer instance for chaining
        """
        self._txns.append(atc)
        return self

    def count(self) -> int:
        """Get the total number of transactions.

        :return: The number of transactions
        """
        return len(self.build_transactions().transactions)

    def build(self) -> TransactionComposerBuildResult:
        """Build the transaction group.

        :return: The built transaction group result
        """
        if self._atc.get_status() == algosdk.atomic_transaction_composer.AtomicTransactionComposerStatus.BUILDING:
            suggested_params = self._get_suggested_params()
            txn_with_signers: list[TransactionWithSigner] = []

            for txn in self._txns:
                txn_with_signers.extend(self._build_txn(txn, suggested_params))

            for ts in txn_with_signers:
                self._atc.add_transaction(ts)
                method = self._txn_method_map.get(ts.txn.get_txid())
                if method:
                    self._atc.method_dict[len(self._atc.txn_list) - 1] = method

        return TransactionComposerBuildResult(
            atc=self._atc,
            transactions=self._atc.build_group(),
            method_calls=self._atc.method_dict,
        )

    def rebuild(self) -> TransactionComposerBuildResult:
        """Rebuild the transaction group from scratch.

        :return: The rebuilt transaction group result
        """
        self._atc = AtomicTransactionComposer()
        return self.build()

    def build_transactions(self) -> BuiltTransactions:
        """Build and return the transactions without executing them.

        :return: The built transactions result
        """
        suggested_params = self._get_suggested_params()

        transactions: list[algosdk.transaction.Transaction] = []
        method_calls: dict[int, Method] = {}
        signers: dict[int, TransactionSigner] = {}

        idx = 0

        for txn in self._txns:
            txn_with_signers: list[TransactionWithSigner] = []

            if isinstance(txn, MethodCallParams):
                txn_with_signers.extend(self._build_method_call(txn, suggested_params))
            else:
                txn_with_signers.extend(self._build_txn(txn, suggested_params))

            for ts in txn_with_signers:
                transactions.append(ts.txn)
                if ts.signer and ts.signer != self._NULL_SIGNER:
                    signers[idx] = ts.signer
                method = self._txn_method_map.get(ts.txn.get_txid())
                if method:
                    method_calls[idx] = method
                idx += 1

        return BuiltTransactions(transactions=transactions, method_calls=method_calls, signers=signers)

    @deprecated("Use send() instead")
    def execute(
        self,
        *,
        max_rounds_to_wait: int | None = None,
    ) -> SendAtomicTransactionComposerResults:
        return self.send(
            max_rounds_to_wait=max_rounds_to_wait,
        )

    def send(
        self,
        *,
        max_rounds_to_wait: int | None = None,
        suppress_log: bool | None = None,
        populate_app_call_resources: bool | None = None,
    ) -> SendAtomicTransactionComposerResults:
        """Send the transaction group to the network.

        :param max_rounds_to_wait: Maximum number of rounds to wait for confirmation
        :param suppress_log: Whether to suppress transaction logging
        :param populate_app_call_resources: Whether to populate app call resources
        :return: The transaction send results
        :raises Exception: If the transaction fails
        """
        group = self.build().transactions

        wait_rounds = max_rounds_to_wait
        if wait_rounds is None:
            last_round = max(txn.txn.last_valid_round for txn in group)
            first_round = self._get_suggested_params().first
            wait_rounds = last_round - first_round + 1

        try:
            return send_atomic_transaction_composer(
                self._atc,
                self._algod,
                max_rounds_to_wait=wait_rounds,
                suppress_log=suppress_log,
                populate_resources=populate_app_call_resources,
            )
        except algosdk.error.AlgodHTTPError as e:
            raise Exception(f"Transaction failed: {e}") from e

    def _handle_simulate_error(self, simulate_response: SimulateAtomicTransactionResponse) -> None:
        # const failedGroup = simulateResponse?.txnGroups[0]
        failed_group = simulate_response.simulate_response.get("txn-groups", [{}])[0]
        failure_message = failed_group.get("failure-message")
        failed_at = [str(x) for x in failed_group.get("failed-at", [])]
        if failure_message:
            error_message = (
                f"Transaction failed at transaction(s) {', '.join(failed_at) if failed_at else 'N/A'} in the group. "
                f"{failure_message}"
            )
            raise Exception(error_message)

    def simulate(
        self,
        allow_more_logs: bool | None = None,
        allow_empty_signatures: bool | None = None,
        allow_unnamed_resources: bool | None = None,
        extra_opcode_budget: int | None = None,
        exec_trace_config: SimulateTraceConfig | None = None,
        simulation_round: int | None = None,
        skip_signatures: bool | None = None,
    ) -> SendAtomicTransactionComposerResults:
        """Simulate transaction group execution with configurable validation rules.

        :param allow_more_logs: Whether to allow more logs than the standard limit
        :param allow_empty_signatures: Whether to allow transactions with empty signatures
        :param allow_unnamed_resources: Whether to allow unnamed resources
        :param extra_opcode_budget: Additional opcode budget to allocate
        :param exec_trace_config: Configuration for execution tracing
        :param simulation_round: Round number to simulate at
        :param skip_signatures: Whether to skip signature validation
        :return: The simulation results
        """

        atc = AtomicTransactionComposer() if skip_signatures else self._atc

        if skip_signatures:
            allow_empty_signatures = True
            transactions = self.build_transactions()
            for txn in transactions.transactions:
                atc.add_transaction(TransactionWithSigner(txn=txn, signer=TransactionComposer._NULL_SIGNER))
            atc.method_dict = transactions.method_calls
        else:
            self.build()

        if config.debug and config.project_root and config.trace_all:
            response = simulate_and_persist_response(
                atc,
                config.project_root,
                self._algod,
                config.trace_buffer_size_mb,
                allow_more_logs,
                allow_empty_signatures,
                allow_unnamed_resources,
                extra_opcode_budget,
                exec_trace_config,
                simulation_round,
                skip_signatures,
            )
            self._handle_simulate_error(response)
            return SendAtomicTransactionComposerResults(
                confirmations=response.simulate_response.get("txn-groups", [{"txn-results": [{"txn-result": {}}]}])[0][
                    "txn-results"
                ],
                transactions=[TransactionWrapper(txn.txn) for txn in atc.txn_list],
                tx_ids=response.tx_ids,
                group_id=atc.txn_list[-1].txn.group or "",
                simulate_response=response.simulate_response,
                returns=[ABIReturn(r) for r in response.abi_results],
            )

        response = simulate_response(
            atc,
            self._algod,
            allow_more_logs,
            allow_empty_signatures,
            allow_unnamed_resources,
            extra_opcode_budget,
            exec_trace_config,
            simulation_round,
            skip_signatures,
        )
        self._handle_simulate_error(response)
        confirmation_results = response.simulate_response.get("txn-groups", [{"txn-results": [{"txn-result": {}}]}])[0][
            "txn-results"
        ]

        return SendAtomicTransactionComposerResults(
            confirmations=[txn["txn-result"] for txn in confirmation_results],
            transactions=[TransactionWrapper(txn.txn) for txn in atc.txn_list],
            tx_ids=response.tx_ids,
            group_id=atc.txn_list[-1].txn.group or "",
            simulate_response=response.simulate_response,
            returns=[ABIReturn(r) for r in response.abi_results],
        )

    @staticmethod
    def arc2_note(note: Arc2TransactionNote) -> bytes:
        """Create an encoded transaction note that follows the ARC-2 spec.

        https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0002.md

        :param note: The ARC-2 note to encode
        :return: The encoded note bytes
        :raises ValueError: If the dapp_name is invalid
        """

        pattern = r"^[a-zA-Z0-9][a-zA-Z0-9_/@.-]{4,31}$"
        if not re.match(pattern, note["dapp_name"]):
            raise ValueError(
                "dapp_name must be 5-32 chars, start with alphanumeric, "
                "and contain only alphanumeric, _, /, @, ., or -"
            )

        data = note["data"]
        if note["format"] == "j" and isinstance(data, (dict | list)):
            # Ensure JSON data uses double quotes
            data = json.dumps(data)

        arc2_payload = f"{note['dapp_name']}:{note['format']}{data}"
        return arc2_payload.encode("utf-8")

    def _build_atc(self, atc: AtomicTransactionComposer) -> list[TransactionWithSigner]:
        group = atc.build_group()

        for ts in group:
            ts.txn.group = None

        method = atc.method_dict.get(len(group) - 1)
        if method:
            self._txn_method_map[group[-1].txn.get_txid()] = method

        return group

    def _common_txn_build_step(
        self,
        build_txn: Callable[[dict], algosdk.transaction.Transaction],
        params: _CommonTxnWithSendParams,
        txn_params: dict,
    ) -> algosdk.transaction.Transaction:
        # Clone suggested params
        txn_params["sp"] = (
            algosdk.transaction.SuggestedParams(**txn_params["sp"].__dict__) if "sp" in txn_params else None
        )

        if params.lease:
            txn_params["lease"] = encode_lease(params.lease)
        if params.rekey_to:
            txn_params["rekey_to"] = params.rekey_to
        if params.note:
            txn_params["note"] = params.note

        if params.static_fee is not None and txn_params["sp"]:
            txn_params["sp"].fee = params.static_fee.micro_algos
            txn_params["sp"].flat_fee = True

        if isinstance(txn_params.get("method"), Arc56Method):
            txn_params["method"] = txn_params["method"].to_abi_method()

        txn = build_txn(txn_params)

        if params.extra_fee:
            txn.fee += params.extra_fee.micro_algos

        if params.max_fee and txn.fee > params.max_fee.micro_algos:
            raise ValueError(f"Transaction fee {txn.fee} is greater than max_fee {params.max_fee}")

        return txn

    def _build_method_call(  # noqa: C901, PLR0912
        self, params: MethodCallParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> list[TransactionWithSigner]:
        method_args: list[ABIValue | TransactionWithSigner] = []
        arg_offset = 0

        if params.args:
            for _, arg in enumerate(params.args):
                if self._is_abi_value(arg):
                    method_args.append(arg)
                    continue

                if isinstance(arg, TransactionWithSigner):
                    method_args.append(arg)
                    continue

                if isinstance(arg, algosdk.transaction.Transaction):
                    # Wrap in TransactionWithSigner
                    method_args.append(
                        TransactionWithSigner(txn=arg, signer=params.signer or self._get_signer(params.sender))
                    )
                    continue
                match arg:
                    case (
                        AppCreateMethodCallParams()
                        | AppCallMethodCallParams()
                        | AppUpdateMethodCallParams()
                        | AppDeleteMethodCallParams()
                    ):
                        temp_txn_with_signers = self._build_method_call(arg, suggested_params)
                        method_args.extend(temp_txn_with_signers)
                        arg_offset += len(temp_txn_with_signers) - 1
                        continue
                    case AppCallParams():
                        txn = self._build_app_call(arg, suggested_params)
                    case PaymentParams():
                        txn = self._build_payment(arg, suggested_params)
                    case AssetOptInParams():
                        txn = self._build_asset_transfer(
                            AssetTransferParams(**arg.__dict__, receiver=arg.sender, amount=0), suggested_params
                        )
                    case AssetCreateParams():
                        txn = self._build_asset_create(arg, suggested_params)
                    case AssetConfigParams():
                        txn = self._build_asset_config(arg, suggested_params)
                    case AssetDestroyParams():
                        txn = self._build_asset_destroy(arg, suggested_params)
                    case AssetFreezeParams():
                        txn = self._build_asset_freeze(arg, suggested_params)
                    case AssetTransferParams():
                        txn = self._build_asset_transfer(arg, suggested_params)
                    case OnlineKeyRegistrationParams() | OfflineKeyRegistrationParams():
                        txn = self._build_key_reg(arg, suggested_params)
                    case _:
                        raise ValueError(f"Unsupported method arg transaction type: {arg!s}")

                method_args.append(
                    TransactionWithSigner(txn=txn, signer=params.signer or self._get_signer(params.sender))
                )

                continue

        method_atc = AtomicTransactionComposer()

        txn_params = {
            "app_id": params.app_id or 0,
            "method": params.method,
            "sender": params.sender,
            "sp": suggested_params,
            "signer": params.signer or self._get_signer(params.sender),
            "method_args": method_args,
            "on_complete": params.on_complete or algosdk.transaction.OnComplete.NoOpOC,
            "note": params.note,
            "lease": params.lease,
            "boxes": [AppManager.get_box_reference(ref) for ref in params.box_references]
            if params.box_references
            else None,
            "foreign_apps": params.app_references,
            "foreign_assets": params.asset_references,
            "accounts": params.account_references,
            "global_schema": algosdk.transaction.StateSchema(
                num_uints=params.schema.get("global_ints", 0),
                num_byte_slices=params.schema.get("global_byte_slices", 0),
            )
            if params.schema
            else None,
            "local_schema": algosdk.transaction.StateSchema(
                num_uints=params.schema.get("local_ints", 0),
                num_byte_slices=params.schema.get("local_byte_slices", 0),
            )
            if params.schema
            else None,
            "approval_program": getattr(params, "approval_program", None),
            "clear_program": getattr(params, "clear_state_program", None),
            "rekey_to": params.rekey_to,
        }

        def _add_method_call_and_return_txn(x: dict) -> algosdk.transaction.Transaction:
            method_atc.add_method_call(**x)
            return method_atc.build_group()[-1].txn

        self._common_txn_build_step(lambda x: _add_method_call_and_return_txn(x), params, txn_params)

        return self._build_atc(method_atc)

    def _build_payment(
        self, params: PaymentParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn_params = {
            "sender": params.sender,
            "sp": suggested_params,
            "receiver": params.receiver,
            "amt": params.amount.micro_algos,
            "close_remainder_to": params.close_remainder_to,
        }

        return self._common_txn_build_step(lambda x: algosdk.transaction.PaymentTxn(**x), params, txn_params)

    def _build_asset_create(
        self, params: AssetCreateParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn_params = {
            "sender": params.sender,
            "sp": suggested_params,
            "total": params.total,
            "default_frozen": params.default_frozen or False,
            "unit_name": params.unit_name or "",
            "asset_name": params.asset_name or "",
            "manager": params.manager,
            "reserve": params.reserve,
            "freeze": params.freeze,
            "clawback": params.clawback,
            "url": params.url or "",
            "metadata_hash": params.metadata_hash,
            "decimals": params.decimals or 0,
        }

        return self._common_txn_build_step(lambda x: algosdk.transaction.AssetCreateTxn(**x), params, txn_params)

    def _build_app_call(
        self,
        params: AppCallParams | AppUpdateParams | AppCreateParams | AppDeleteParams,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> algosdk.transaction.Transaction:
        app_id = getattr(params, "app_id", 0)

        approval_program = None
        clear_program = None

        if isinstance(params, AppUpdateParams | AppCreateParams):
            if isinstance(params.approval_program, str):
                approval_program = self._app_manager.compile_teal(params.approval_program).compiled_base64_to_bytes
            elif isinstance(params.approval_program, bytes):
                approval_program = params.approval_program

            if isinstance(params.clear_state_program, str):
                clear_program = self._app_manager.compile_teal(params.clear_state_program).compiled_base64_to_bytes
            elif isinstance(params.clear_state_program, bytes):
                clear_program = params.clear_state_program

        approval_program_len = len(approval_program) if approval_program else 0
        clear_program_len = len(clear_program) if clear_program else 0

        sdk_params = {
            "sender": params.sender,
            "sp": suggested_params,
            "app_args": params.args,
            "on_complete": params.on_complete or algosdk.transaction.OnComplete.NoOpOC,
            "accounts": params.account_references,
            "foreign_apps": params.app_references,
            "foreign_assets": params.asset_references,
            "boxes": params.box_references,
            "approval_program": approval_program,
            "clear_program": clear_program,
        }

        txn_params = {**sdk_params, "index": app_id}

        if not app_id and isinstance(params, AppCreateParams):
            if not sdk_params["approval_program"] or not sdk_params["clear_program"]:
                raise ValueError("approval_program and clear_program are required for application creation")

            if not params.schema:
                raise ValueError("schema is required for application creation")

            txn_params = {
                **txn_params,
                "global_schema": algosdk.transaction.StateSchema(
                    num_uints=params.schema.get("global_ints", 0),
                    num_byte_slices=params.schema.get("global_byte_slices", 0),
                ),
                "local_schema": algosdk.transaction.StateSchema(
                    num_uints=params.schema.get("local_ints", 0),
                    num_byte_slices=params.schema.get("local_byte_slices", 0),
                ),
                "extra_pages": params.extra_program_pages
                or math.floor((approval_program_len + clear_program_len) / algosdk.constants.APP_PAGE_MAX_SIZE)
                if params.extra_program_pages
                else 0,
            }

        return self._common_txn_build_step(lambda x: algosdk.transaction.ApplicationCallTxn(**x), params, txn_params)

    def _build_asset_config(
        self, params: AssetConfigParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn_params = {
            "sender": params.sender,
            "sp": suggested_params,
            "index": params.asset_id,
            "manager": params.manager,
            "reserve": params.reserve,
            "freeze": params.freeze,
            "clawback": params.clawback,
            "strict_empty_address_check": False,
        }

        return self._common_txn_build_step(lambda x: algosdk.transaction.AssetConfigTxn(**x), params, txn_params)

    def _build_asset_destroy(
        self, params: AssetDestroyParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn_params = {
            "sender": params.sender,
            "sp": suggested_params,
            "index": params.asset_id,
        }

        return self._common_txn_build_step(lambda x: algosdk.transaction.AssetDestroyTxn(**x), params, txn_params)

    def _build_asset_freeze(
        self, params: AssetFreezeParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn_params = {
            "sender": params.sender,
            "sp": suggested_params,
            "index": params.asset_id,
            "target": params.account,
            "new_freeze_state": params.frozen,
        }

        return self._common_txn_build_step(lambda x: algosdk.transaction.AssetFreezeTxn(**x), params, txn_params)

    def _build_asset_transfer(
        self, params: AssetTransferParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn_params = {
            "sender": params.sender,
            "sp": suggested_params,
            "receiver": params.receiver,
            "amt": params.amount,
            "index": params.asset_id,
            "close_assets_to": params.close_asset_to,
            "revocation_target": params.clawback_target,
        }

        return self._common_txn_build_step(lambda x: algosdk.transaction.AssetTransferTxn(**x), params, txn_params)

    def _build_key_reg(
        self,
        params: OnlineKeyRegistrationParams | OfflineKeyRegistrationParams,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> algosdk.transaction.Transaction:
        if isinstance(params, OnlineKeyRegistrationParams):
            txn_params = {
                "sender": params.sender,
                "sp": suggested_params,
                "votekey": params.vote_key,
                "selkey": params.selection_key,
                "votefst": params.vote_first,
                "votelst": params.vote_last,
                "votekd": params.vote_key_dilution,
                "rekey_to": params.rekey_to,
                "nonpart": False,
                "sprfkey": params.state_proof_key,
            }

            return self._common_txn_build_step(lambda x: algosdk.transaction.KeyregTxn(**x), params, txn_params)

        return self._common_txn_build_step(
            lambda x: algosdk.transaction.KeyregTxn(**x),
            params,
            {
                "sender": params.sender,
                "sp": suggested_params,
                "nonpart": params.prevent_account_from_ever_participating_again,
                "votekey": None,
                "selkey": None,
                "votefst": None,
                "votelst": None,
                "votekd": None,
            },
        )

    def _is_abi_value(self, x: bool | float | str | bytes | list | TxnParams) -> bool:
        if isinstance(x, list | tuple):
            return len(x) == 0 or all(self._is_abi_value(item) for item in x)

        return isinstance(x, bool | int | float | str | bytes)

    def _build_txn(  # noqa: C901, PLR0912, PLR0911
        self,
        txn: TransactionWithSigner | TxnParams | AtomicTransactionComposer,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> list[TransactionWithSigner]:
        match txn:
            case TransactionWithSigner():
                return [txn]
            case AtomicTransactionComposer():
                return self._build_atc(txn)
            case algosdk.transaction.Transaction():
                signer = self._get_signer(txn.sender)
                return [TransactionWithSigner(txn=txn, signer=signer)]
            case (
                AppCreateMethodCallParams()
                | AppCallMethodCallParams()
                | AppUpdateMethodCallParams()
                | AppDeleteMethodCallParams()
            ):
                return self._build_method_call(txn, suggested_params)

        signer = txn.signer or self._get_signer(txn.sender)

        match txn:
            case PaymentParams():
                payment = self._build_payment(txn, suggested_params)
                return [TransactionWithSigner(txn=payment, signer=signer)]
            case AssetCreateParams():
                asset_create = self._build_asset_create(txn, suggested_params)
                return [TransactionWithSigner(txn=asset_create, signer=signer)]
            case AppCallParams() | AppUpdateParams() | AppCreateParams() | AppDeleteParams():
                app_call = self._build_app_call(txn, suggested_params)
                return [TransactionWithSigner(txn=app_call, signer=signer)]
            case AssetConfigParams():
                asset_config = self._build_asset_config(txn, suggested_params)
                return [TransactionWithSigner(txn=asset_config, signer=signer)]
            case AssetDestroyParams():
                asset_destroy = self._build_asset_destroy(txn, suggested_params)
                return [TransactionWithSigner(txn=asset_destroy, signer=signer)]
            case AssetFreezeParams():
                asset_freeze = self._build_asset_freeze(txn, suggested_params)
                return [TransactionWithSigner(txn=asset_freeze, signer=signer)]
            case AssetTransferParams():
                asset_transfer = self._build_asset_transfer(txn, suggested_params)
                return [TransactionWithSigner(txn=asset_transfer, signer=signer)]
            case AssetOptInParams():
                asset_transfer = self._build_asset_transfer(
                    AssetTransferParams(**txn.__dict__, receiver=txn.sender, amount=0), suggested_params
                )
                return [TransactionWithSigner(txn=asset_transfer, signer=signer)]
            case AssetOptOutParams():
                txn_dict = txn.__dict__
                creator = txn_dict.pop("creator")
                asset_transfer = self._build_asset_transfer(
                    AssetTransferParams(**txn_dict, receiver=txn.sender, amount=0, close_asset_to=creator),
                    suggested_params,
                )
                return [TransactionWithSigner(txn=asset_transfer, signer=signer)]
            case OnlineKeyRegistrationParams() | OfflineKeyRegistrationParams():
                key_reg = self._build_key_reg(txn, suggested_params)
                return [TransactionWithSigner(txn=key_reg, signer=signer)]
            case _:
                raise ValueError(f"Unsupported txn: {txn}")
