from __future__ import annotations

import base64
import json
import math
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypedDict, Union, cast

import algosdk
import algosdk.atomic_transaction_composer
import algosdk.v2client.models
from algosdk import logic, transaction
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    SimulateAtomicTransactionResponse,
    TransactionSigner,
    TransactionWithSigner,
)
from algosdk.transaction import ApplicationCallTxn, OnComplete, SuggestedParams
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.models.simulate_request import SimulateRequest
from typing_extensions import deprecated

from algokit_utils.applications.abi import ABIReturn, ABIValue
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.applications.app_spec.arc56 import Method as Arc56Method
from algokit_utils.config import config
from algokit_utils.models.state import BoxIdentifier, BoxReference
from algokit_utils.models.transaction import SendParams, TransactionWrapper
from algokit_utils.protocols.account import TransactionSignerAccountProtocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from algosdk.abi import Method
    from algosdk.v2client.algod import AlgodClient
    from algosdk.v2client.models import SimulateTraceConfig

    from algokit_utils.models.amount import AlgoAmount
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

MAX_TRANSACTION_GROUP_SIZE = 16
MAX_APP_CALL_FOREIGN_REFERENCES = 8
MAX_APP_CALL_ACCOUNT_REFERENCES = 4


@dataclass(kw_only=True, frozen=True)
class _CommonTxnParams:
    sender: str
    signer: TransactionSigner | TransactionSignerAccountProtocol | None = None
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
class AdditionalAtcContext:
    max_fees: dict[int, AlgoAmount] | None = None
    suggested_params: SuggestedParams | None = None


@dataclass(kw_only=True, frozen=True)
class PaymentParams(_CommonTxnParams):
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
class AssetCreateParams(_CommonTxnParams):
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
class AssetConfigParams(_CommonTxnParams):
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
class AssetFreezeParams(_CommonTxnParams):
    """Parameters for freezing an asset.

    :ivar asset_id: The ID of the asset
    :ivar account: The account to freeze or unfreeze
    :ivar frozen: Whether the assets in the account should be frozen
    """

    asset_id: int
    account: str
    frozen: bool


@dataclass(kw_only=True, frozen=True)
class AssetDestroyParams(_CommonTxnParams):
    """Parameters for destroying an asset.

    :ivar asset_id: ID of the asset
    """

    asset_id: int


@dataclass(kw_only=True, frozen=True)
class OnlineKeyRegistrationParams(_CommonTxnParams):
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
class OfflineKeyRegistrationParams(_CommonTxnParams):
    """Parameters for offline key registration.

    :ivar prevent_account_from_ever_participating_again: Whether to prevent the account from ever participating again
    """

    prevent_account_from_ever_participating_again: bool


@dataclass(kw_only=True, frozen=True)
class AssetTransferParams(_CommonTxnParams):
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
class AssetOptInParams(_CommonTxnParams):
    """Parameters for opting into an asset.

    :ivar asset_id: ID of the asset
    """

    asset_id: int


@dataclass(kw_only=True, frozen=True)
class AssetOptOutParams(_CommonTxnParams):
    """Parameters for opting out of an asset.

    :ivar asset_id: ID of the asset
    :ivar creator: The creator address of the asset
    """

    asset_id: int
    creator: str


@dataclass(kw_only=True, frozen=True)
class AppCallParams(_CommonTxnParams):
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
class AppCreateParams(_CommonTxnParams):
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
class AppUpdateParams(_CommonTxnParams):
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
class AppDeleteParams(_CommonTxnParams):
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
class _BaseAppMethodCall(_CommonTxnParams):
    app_id: int
    method: Method
    args: list | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None
    schema: AppCreateSchema | None = None


@dataclass(kw_only=True, frozen=True)
class AppMethodCallParams(_CommonTxnParams):
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


@dataclass(frozen=True, kw_only=True)
class TransactionContext:
    """Contextual information for a transaction."""

    max_fee: AlgoAmount | None = None
    abi_method: Method | None = None

    @staticmethod
    def empty() -> TransactionContext:
        return TransactionContext(max_fee=None, abi_method=None)


class TransactionWithContext:
    """Combines Transaction with additional context."""

    def __init__(self, txn: algosdk.transaction.Transaction, context: TransactionContext):
        self.txn = txn
        self.context = context


class TransactionWithSignerAndContext(TransactionWithSigner):
    """Combines TransactionWithSigner with additional context."""

    def __init__(self, txn: algosdk.transaction.Transaction, signer: TransactionSigner, context: TransactionContext):
        super().__init__(txn, signer)
        self.context = context

    @staticmethod
    def from_txn_with_context(
        txn_with_context: TransactionWithContext, signer: TransactionSigner
    ) -> TransactionWithSignerAndContext:
        return TransactionWithSignerAndContext(
            txn=txn_with_context.txn, signer=signer, context=txn_with_context.context
        )


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


@dataclass
class ExecutionInfoTxn:
    unnamed_resources_accessed: dict | None = None
    required_fee_delta: int = 0


@dataclass
class ExecutionInfo:
    """Information about transaction execution from simulation."""

    group_unnamed_resources_accessed: dict[str, Any] | None = None
    txns: list[ExecutionInfoTxn] | None = None


@dataclass
class _TransactionWithPriority:
    txn: algosdk.transaction.Transaction
    priority: int
    fee_delta: int
    index: int


MAX_LEASE_LENGTH = 32
NULL_SIGNER: TransactionSigner = algosdk.atomic_transaction_composer.EmptySigner()


def _encode_lease(lease: str | bytes | None) -> bytes | None:
    if lease is None:
        return None
    elif isinstance(lease, bytes):
        if not (1 <= len(lease) <= MAX_LEASE_LENGTH):
            raise ValueError(
                f"Received invalid lease; expected something with length between 1 and {MAX_LEASE_LENGTH}, "
                f"but received bytes with length {len(lease)}"
            )
        if len(lease) == MAX_LEASE_LENGTH:
            return lease
        lease32 = bytearray(32)
        lease32[: len(lease)] = lease
        return bytes(lease32)
    elif isinstance(lease, str):
        encoded = lease.encode("utf-8")
        if not (1 <= len(encoded) <= MAX_LEASE_LENGTH):
            raise ValueError(
                f"Received invalid lease; expected something with length between 1 and {MAX_LEASE_LENGTH}, "
                f"but received '{lease}' with length {len(lease)}"
            )
        lease32 = bytearray(MAX_LEASE_LENGTH)
        lease32[: len(encoded)] = encoded
        return bytes(lease32)
    else:
        raise TypeError(f"Unknown lease type received of {type(lease)}")


def _get_group_execution_info(  # noqa: C901, PLR0912
    atc: AtomicTransactionComposer,
    algod: AlgodClient,
    populate_app_call_resources: bool | None = None,
    cover_app_call_inner_transaction_fees: bool | None = None,
    additional_atc_context: AdditionalAtcContext | None = None,
) -> ExecutionInfo:
    # Create simulation request
    suggested_params = additional_atc_context.suggested_params if additional_atc_context else None
    max_fees = additional_atc_context.max_fees if additional_atc_context else None

    simulate_request = SimulateRequest(
        txn_groups=[],
        allow_unnamed_resources=True,
        allow_empty_signatures=True,
    )

    # Clone ATC with null signers
    empty_signer_atc = atc.clone()

    # Track app call indexes without max fees
    app_call_indexes_without_max_fees = []

    # Copy transactions with null signers
    for i, txn in enumerate(empty_signer_atc.txn_list):
        txn_with_signer = TransactionWithSigner(txn=txn.txn, signer=NULL_SIGNER)

        if cover_app_call_inner_transaction_fees and isinstance(txn.txn, algosdk.transaction.ApplicationCallTxn):
            if not suggested_params:
                raise ValueError("suggested_params required when cover_app_call_inner_transaction_fees enabled")

            max_fee = max_fees.get(i).micro_algos if max_fees and i in max_fees else None  # type: ignore[union-attr]
            if max_fee is None:
                app_call_indexes_without_max_fees.append(i)
            else:
                txn_with_signer.txn.fee = max_fee

    if cover_app_call_inner_transaction_fees and app_call_indexes_without_max_fees:
        raise ValueError(
            f"Please provide a `max_fee` for each app call transaction when `cover_app_call_inner_transaction_fees` is enabled. "  # noqa: E501
            f"Required for transactions: {', '.join(str(i) for i in app_call_indexes_without_max_fees)}"
        )

    # Get fee parameters
    per_byte_txn_fee = suggested_params.fee if suggested_params else 0
    min_txn_fee = int(suggested_params.min_fee) if suggested_params else 1000  # type: ignore[unused-ignore]

    # Simulate transactions
    result = empty_signer_atc.simulate(algod, simulate_request)

    group_response = result.simulate_response["txn-groups"][0]

    if group_response.get("failure-message"):
        msg = group_response["failure-message"]
        if cover_app_call_inner_transaction_fees and "fee too small" in msg:
            raise ValueError(
                "Fees were too small to resolve execution info via simulate. "
                "You may need to increase an app call transaction maxFee."
            )
        failed_at = group_response.get("failed-at", [0])[0]
        raise ValueError(
            f"Error during resource population simulation in transaction {failed_at}: "
            f"{group_response['failure-message']}"
        )

    # Build execution info
    txn_results = []
    for i, txn_result_raw in enumerate(group_response["txn-results"]):
        txn_result = txn_result_raw.get("txn-result")
        if not txn_result:
            continue

        original_txn = atc.build_group()[i].txn

        required_fee_delta = 0
        if cover_app_call_inner_transaction_fees:
            # Calculate parent transaction fee
            parent_per_byte_fee = per_byte_txn_fee * (original_txn.estimate_size() + 75)
            parent_min_fee = max(parent_per_byte_fee, min_txn_fee)
            parent_fee_delta = parent_min_fee - original_txn.fee

            if isinstance(original_txn, algosdk.transaction.ApplicationCallTxn):
                # Calculate inner transaction fees recursively
                def calculate_inner_fee_delta(inner_txns: list[dict], acc: int = 0) -> int:
                    for inner_txn in reversed(inner_txns):
                        current_fee_delta = (
                            calculate_inner_fee_delta(inner_txn["inner-txns"], acc)
                            if inner_txn.get("inner-txns")
                            else acc
                        ) + (min_txn_fee - inner_txn["txn"]["txn"].get("fee", 0))
                        acc = max(0, current_fee_delta)
                    return acc

                inner_fee_delta = calculate_inner_fee_delta(txn_result.get("inner-txns", []))
                required_fee_delta = inner_fee_delta + parent_fee_delta
            else:
                required_fee_delta = parent_fee_delta

        txn_results.append(
            ExecutionInfoTxn(
                unnamed_resources_accessed=txn_result_raw.get("unnamed-resources-accessed")
                if populate_app_call_resources
                else None,
                required_fee_delta=required_fee_delta,
            )
        )

    return ExecutionInfo(
        group_unnamed_resources_accessed=group_response.get("unnamed-resources-accessed")
        if populate_app_call_resources
        else None,
        txns=txn_results,
    )


def _find_available_transaction_index(
    txns: list[TransactionWithSigner], reference_type: str, reference: str | dict[str, Any] | int
) -> int:
    """Find index of first transaction that can accommodate the new reference."""

    def check_transaction(txn: TransactionWithSigner) -> bool:
        # Skip if not an application call transaction
        if txn.txn.type != "appl":
            return False

        # Get current counts (using get() with default 0 for Pythonic null handling)
        accounts = len(getattr(txn.txn, "accounts", []) or [])
        assets = len(getattr(txn.txn, "foreign_assets", []) or [])
        apps = len(getattr(txn.txn, "foreign_apps", []) or [])
        boxes = len(getattr(txn.txn, "boxes", []) or [])

        # For account references, only check account limit
        if reference_type == "account":
            return accounts < MAX_APP_CALL_ACCOUNT_REFERENCES

        # For asset holdings or local state, need space for both account and other reference
        if reference_type in ("asset_holding", "app_local"):
            return (
                accounts + assets + apps + boxes < MAX_APP_CALL_FOREIGN_REFERENCES - 1
                and accounts < MAX_APP_CALL_ACCOUNT_REFERENCES
            )

        # For boxes with non-zero app ID, need space for box and app reference
        if reference_type == "box" and reference and int(getattr(reference, "app", 0)) != 0:
            return accounts + assets + apps + boxes < MAX_APP_CALL_FOREIGN_REFERENCES - 1

        # Default case - just check total references
        return accounts + assets + apps + boxes < MAX_APP_CALL_FOREIGN_REFERENCES

    # Return first matching index or -1 if none found
    return next((i for i, txn in enumerate(txns) if check_transaction(txn)), -1)


def populate_app_call_resources(atc: AtomicTransactionComposer, algod: AlgodClient) -> AtomicTransactionComposer:
    """Populate application call resources based on simulation results.

    :param atc: The AtomicTransactionComposer containing transactions
    :param algod: Algod client for simulation
    :return: Modified AtomicTransactionComposer with populated resources
    """
    return prepare_group_for_sending(atc, algod, populate_app_call_resources=True)


def prepare_group_for_sending(  # noqa: C901, PLR0912, PLR0915
    atc: AtomicTransactionComposer,
    algod: AlgodClient,
    populate_app_call_resources: bool | None = None,
    cover_app_call_inner_transaction_fees: bool | None = None,
    additional_atc_context: AdditionalAtcContext | None = None,
) -> AtomicTransactionComposer:
    """Prepare a transaction group for sending by handling execution info and resources.

    :param atc: The AtomicTransactionComposer containing transactions
    :param algod: Algod client for simulation
    :param populate_app_call_resources: Whether to populate app call resources
    :param cover_app_call_inner_transaction_fees: Whether to cover inner txn fees
    :param additional_atc_context: Additional context for the AtomicTransactionComposer
    :return: Modified AtomicTransactionComposer ready for sending
    """
    # Get execution info via simulation
    execution_info = _get_group_execution_info(
        atc, algod, populate_app_call_resources, cover_app_call_inner_transaction_fees, additional_atc_context
    )
    max_fees = additional_atc_context.max_fees if additional_atc_context else None

    group = atc.build_group()

    # Handle transaction fees if needed
    if cover_app_call_inner_transaction_fees:
        # Sort transactions by fee priority
        txns_with_priority: list[_TransactionWithPriority] = []
        for i, txn_info in enumerate(execution_info.txns or []):
            if not txn_info:
                continue
            txn = group[i].txn
            max_fee = max_fees.get(i).micro_algos if max_fees and i in max_fees else None  # type: ignore[union-attr]
            immutable_fee = max_fee is not None and max_fee == txn.fee
            priority_multiplier = (
                1000
                if (
                    txn_info.required_fee_delta > 0
                    and (immutable_fee or not isinstance(txn, algosdk.transaction.ApplicationCallTxn))
                )
                else 1
            )

            txns_with_priority.append(
                _TransactionWithPriority(
                    txn=txn,
                    index=i,
                    fee_delta=txn_info.required_fee_delta,
                    priority=txn_info.required_fee_delta * priority_multiplier
                    if txn_info.required_fee_delta > 0
                    else -1,
                )
            )

        # Sort by priority descending
        txns_with_priority.sort(key=lambda x: x.priority, reverse=True)

        # Calculate surplus fees and additional fees needed
        surplus_fees = sum(
            txn_info.required_fee_delta * -1
            for txn_info in execution_info.txns or []
            if txn_info is not None and txn_info.required_fee_delta < 0
        )

        additional_fees = {}

        # Distribute surplus fees to cover deficits
        for txn_obj in txns_with_priority:
            if txn_obj.fee_delta > 0:
                if surplus_fees >= txn_obj.fee_delta:
                    surplus_fees -= txn_obj.fee_delta
                else:
                    additional_fees[txn_obj.index] = txn_obj.fee_delta - surplus_fees
                    surplus_fees = 0

    def populate_group_resource(  # noqa: PLR0915, PLR0912, C901
        txns: list[TransactionWithSigner], reference: str | dict[str, Any] | int, ref_type: str
    ) -> None:
        """Helper function to populate group-level resources."""

        def is_appl_below_limit(t: TransactionWithSigner) -> bool:
            if not isinstance(t.txn, transaction.ApplicationCallTxn):
                return False

            accounts = len(getattr(t.txn, "accounts", []) or [])
            assets = len(getattr(t.txn, "foreign_assets", []) or [])
            apps = len(getattr(t.txn, "foreign_apps", []) or [])
            boxes = len(getattr(t.txn, "boxes", []) or [])

            return accounts + assets + apps + boxes < MAX_APP_CALL_FOREIGN_REFERENCES

        # Handle asset holding and app local references first
        if ref_type in ("assetHolding", "appLocal"):
            ref_dict = cast(dict[str, Any], reference)
            account = ref_dict["account"]

            # First try to find transaction with account already available
            txn_idx = next(
                (
                    i
                    for i, t in enumerate(txns)
                    if is_appl_below_limit(t)
                    and isinstance(t.txn, transaction.ApplicationCallTxn)
                    and (
                        account in (getattr(t.txn, "accounts", []) or [])
                        or account
                        in (
                            logic.get_application_address(app_id)
                            for app_id in (getattr(t.txn, "foreign_apps", []) or [])
                        )
                        or any(str(account) in str(v) for v in t.txn.__dict__.values())
                    )
                ),
                -1,
            )

            if txn_idx >= 0:
                app_txn = cast(transaction.ApplicationCallTxn, txns[txn_idx].txn)
                if ref_type == "assetHolding":
                    asset_id = ref_dict["asset"]
                    app_txn.foreign_assets = [*list(getattr(app_txn, "foreign_assets", []) or []), asset_id]
                else:
                    app_id = ref_dict["app"]
                    app_txn.foreign_apps = [*list(getattr(app_txn, "foreign_apps", []) or []), app_id]
                return

            # Try to find transaction that already has the app/asset available
            txn_idx = next(
                (
                    i
                    for i, t in enumerate(txns)
                    if is_appl_below_limit(t)
                    and isinstance(t.txn, transaction.ApplicationCallTxn)
                    and len(getattr(t.txn, "accounts", []) or []) < MAX_APP_CALL_ACCOUNT_REFERENCES
                    and (
                        (
                            ref_type == "assetHolding"
                            and ref_dict["asset"] in (getattr(t.txn, "foreign_assets", []) or [])
                        )
                        or (
                            ref_type == "appLocal"
                            and (
                                ref_dict["app"] in (getattr(t.txn, "foreign_apps", []) or [])
                                or t.txn.index == ref_dict["app"]
                            )
                        )
                    )
                ),
                -1,
            )

            if txn_idx >= 0:
                app_txn = cast(transaction.ApplicationCallTxn, txns[txn_idx].txn)
                accounts = list(getattr(app_txn, "accounts", []) or [])
                accounts.append(account)
                app_txn.accounts = accounts
                return

        # Handle box references
        if ref_type == "box":
            box_ref = (reference["app"], base64.b64decode(reference["name"]))  # type: ignore[index]

            # Try to find transaction that already has the app available
            txn_idx = next(
                (
                    i
                    for i, t in enumerate(txns)
                    if is_appl_below_limit(t)
                    and isinstance(t.txn, transaction.ApplicationCallTxn)
                    and (box_ref[0] in (getattr(t.txn, "foreign_apps", []) or []) or t.txn.index == box_ref[0])
                ),
                -1,
            )

            if txn_idx >= 0:
                app_txn = cast(transaction.ApplicationCallTxn, txns[txn_idx].txn)
                boxes = list(getattr(app_txn, "boxes", []) or [])
                boxes.append(BoxReference.translate_box_reference(box_ref, app_txn.foreign_apps or [], app_txn.index))  # type: ignore[arg-type]
                app_txn.boxes = boxes
                return

        # Find available transaction for the resource
        txn_idx = _find_available_transaction_index(txns, ref_type, reference)

        if txn_idx == -1:
            raise ValueError("No more transactions below reference limit. Add another app call to the group.")

        app_txn = cast(transaction.ApplicationCallTxn, txns[txn_idx].txn)

        if ref_type == "account":
            accounts = list(getattr(app_txn, "accounts", []) or [])
            accounts.append(cast(str, reference))
            app_txn.accounts = accounts
        elif ref_type == "app":
            app_id = int(cast(str | int, reference))
            foreign_apps = list(getattr(app_txn, "foreign_apps", []) or [])
            foreign_apps.append(app_id)
            app_txn.foreign_apps = foreign_apps
        elif ref_type == "box":
            boxes = list(getattr(app_txn, "boxes", []) or [])
            boxes.append(BoxReference.translate_box_reference(box_ref, app_txn.foreign_apps or [], app_txn.index))  # type: ignore[arg-type]
            app_txn.boxes = boxes
            if box_ref[0] != 0:
                foreign_apps = list(getattr(app_txn, "foreign_apps", []) or [])
                foreign_apps.append(box_ref[0])
                app_txn.foreign_apps = foreign_apps
        elif ref_type == "asset":
            asset_id = int(cast(str | int, reference))
            foreign_assets = list(getattr(app_txn, "foreign_assets", []) or [])
            foreign_assets.append(asset_id)
            app_txn.foreign_assets = foreign_assets
        elif ref_type == "assetHolding":
            ref_dict = cast(dict[str, Any], reference)
            foreign_assets = list(getattr(app_txn, "foreign_assets", []) or [])
            foreign_assets.append(ref_dict["asset"])
            app_txn.foreign_assets = foreign_assets
            accounts = list(getattr(app_txn, "accounts", []) or [])
            accounts.append(ref_dict["account"])
            app_txn.accounts = accounts
        elif ref_type == "appLocal":
            ref_dict = cast(dict[str, Any], reference)
            foreign_apps = list(getattr(app_txn, "foreign_apps", []) or [])
            foreign_apps.append(ref_dict["app"])
            app_txn.foreign_apps = foreign_apps
            accounts = list(getattr(app_txn, "accounts", []) or [])
            accounts.append(ref_dict["account"])
            app_txn.accounts = accounts

    # Process transaction-level resources
    for i, txn_info in enumerate(execution_info.txns or []):
        if not txn_info:
            continue

        # Validate no unexpected resources
        is_app_txn = isinstance(group[i].txn, algosdk.transaction.ApplicationCallTxn)
        resources = txn_info.unnamed_resources_accessed
        if resources and is_app_txn:
            app_txn = group[i].txn
            if resources.get("boxes") or resources.get("extra-box-refs"):
                raise ValueError("Unexpected boxes at transaction level")
            if resources.get("appLocals"):
                raise ValueError("Unexpected app local at transaction level")
            if resources.get("assetHoldings"):
                raise ValueError("Unexpected asset holding at transaction level")

            # Update application call fields
            accounts = list(getattr(app_txn, "accounts", []) or [])
            foreign_apps = list(getattr(app_txn, "foreign_apps", []) or [])
            foreign_assets = list(getattr(app_txn, "foreign_assets", []) or [])
            boxes = list(getattr(app_txn, "boxes", []) or [])

            # Add new resources
            accounts.extend(resources.get("accounts", []))
            foreign_apps.extend(resources.get("apps", []))
            foreign_assets.extend(resources.get("assets", []))
            boxes.extend(resources.get("boxes", []))

            # Validate limits
            if len(accounts) > MAX_APP_CALL_ACCOUNT_REFERENCES:
                raise ValueError(
                    f"Account reference limit of {MAX_APP_CALL_ACCOUNT_REFERENCES} exceeded in transaction {i}"
                )

            total_refs = len(accounts) + len(foreign_assets) + len(foreign_apps) + len(boxes)
            if total_refs > MAX_APP_CALL_FOREIGN_REFERENCES:
                raise ValueError(
                    f"Resource reference limit of {MAX_APP_CALL_FOREIGN_REFERENCES} exceeded in transaction {i}"
                )

            # Update transaction
            app_txn.accounts = accounts  # type: ignore[attr-defined]
            app_txn.foreign_apps = foreign_apps  # type: ignore[attr-defined]
            app_txn.foreign_assets = foreign_assets  # type: ignore[attr-defined]
            app_txn.boxes = boxes  # type: ignore[attr-defined]

        # Update fees if needed
        if cover_app_call_inner_transaction_fees and i in additional_fees:
            cur_txn = group[i].txn
            additional_fee = additional_fees[i]
            if not isinstance(cur_txn, algosdk.transaction.ApplicationCallTxn):
                raise ValueError(
                    f"An additional fee of {additional_fee} µALGO is required for non app call transaction {i}"
                )

            transaction_fee = cur_txn.fee + additional_fee
            max_fee = max_fees.get(i).micro_algos if max_fees and i in max_fees else None  # type: ignore[union-attr]

            if max_fee is None or transaction_fee > max_fee:
                raise ValueError(
                    f"Calculated transaction fee {transaction_fee} µALGO is greater "
                    f"than max of {max_fee or 'undefined'} "
                    f"for transaction {i}"
                )
            cur_txn.fee = transaction_fee

    # Process group-level resources
    group_resources = execution_info.group_unnamed_resources_accessed
    if group_resources:
        # Handle cross-reference resources first
        for app_local in group_resources.get("appLocals", []):
            populate_group_resource(group, app_local, "appLocal")
            # Remove processed resources
            if "accounts" in group_resources:
                group_resources["accounts"] = [
                    acc for acc in group_resources["accounts"] if acc != app_local["account"]
                ]
            if "apps" in group_resources:
                group_resources["apps"] = [app for app in group_resources["apps"] if int(app) != int(app_local["app"])]

        for asset_holding in group_resources.get("assetHoldings", []):
            populate_group_resource(group, asset_holding, "assetHolding")
            # Remove processed resources
            if "accounts" in group_resources:
                group_resources["accounts"] = [
                    acc for acc in group_resources["accounts"] if acc != asset_holding["account"]
                ]
            if "assets" in group_resources:
                group_resources["assets"] = [
                    asset for asset in group_resources["assets"] if int(asset) != int(asset_holding["asset"])
                ]

        # Handle remaining resources
        for account in group_resources.get("accounts", []):
            populate_group_resource(group, account, "account")

        for box in group_resources.get("boxes", []):
            populate_group_resource(group, box, "box")
            if "apps" in group_resources:
                group_resources["apps"] = [app for app in group_resources["apps"] if int(app) != int(box["app"])]

        for asset in group_resources.get("assets", []):
            populate_group_resource(group, asset, "asset")

        for app in group_resources.get("apps", []):
            populate_group_resource(group, app, "app")

        # Handle extra box references
        extra_box_refs = group_resources.get("extra-box-refs", 0)
        for _ in range(extra_box_refs):
            populate_group_resource(group, {"app": 0, "name": ""}, "box")

    # Create new ATC with updated transactions
    new_atc = AtomicTransactionComposer()
    for txn_with_signer in group:
        txn_with_signer.txn.group = None
        new_atc.add_transaction(txn_with_signer)
    new_atc.method_dict = deepcopy(atc.method_dict)

    return new_atc


def send_atomic_transaction_composer(  # noqa: C901, PLR0912
    atc: AtomicTransactionComposer,
    algod: AlgodClient,
    *,
    max_rounds_to_wait: int | None = 5,
    skip_waiting: bool = False,
    suppress_log: bool | None = None,
    populate_app_call_resources: bool | None = None,
    cover_app_call_inner_transaction_fees: bool | None = None,
    additional_atc_context: AdditionalAtcContext | None = None,
) -> SendAtomicTransactionComposerResults:
    """Send an AtomicTransactionComposer transaction group.

    Executes a group of transactions atomically using the AtomicTransactionComposer.

    :param atc: The AtomicTransactionComposer instance containing the transaction group to send
    :param algod: The Algod client to use for sending the transactions
    :param max_rounds_to_wait: Maximum number of rounds to wait for confirmation, defaults to 5
    :param skip_waiting: If True, don't wait for transaction confirmation, defaults to False
    :param suppress_log: If True, suppress logging, defaults to None
    :param populate_app_call_resources: If True, populate app call resources, defaults to None
    :param cover_app_call_inner_transaction_fees: If True, cover app call inner transaction fees, defaults to None
    :param additional_atc_context: Additional context for the AtomicTransactionComposer
    :return: Results from sending the transaction group
    :raises Exception: If there is an error sending the transactions
    :raises error: If there is an error from the Algorand node
    """
    from algokit_utils._debugging import simulate_and_persist_response, simulate_response

    try:
        # Build transactions
        transactions_with_signer = atc.build_group()

        populate_app_call_resources = (
            populate_app_call_resources
            if populate_app_call_resources is not None
            else config.populate_app_call_resource
        )

        if (populate_app_call_resources or cover_app_call_inner_transaction_fees) and any(
            isinstance(t.txn, algosdk.transaction.ApplicationCallTxn) for t in transactions_with_signer
        ):
            atc = prepare_group_for_sending(
                atc,
                algod,
                populate_app_call_resources,
                cover_app_call_inner_transaction_fees,
                additional_atc_context,
            )

        transactions_to_send = [t.txn for t in transactions_with_signer]

        # Get group ID if multiple transactions
        group_id = None
        if len(transactions_to_send) > 1:
            group_id = (
                base64.b64encode(transactions_to_send[0].group).decode("utf-8") if transactions_to_send[0].group else ""
            )

            if not suppress_log:
                logger.info(
                    f"Sending group of {len(transactions_to_send)} transactions ({group_id})",
                    suppress_log=suppress_log or False,
                )
                logger.debug(
                    f"Transaction IDs ({group_id}): {[t.get_txid() for t in transactions_to_send]}",
                    suppress_log=suppress_log or False,
                )

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
                logger.info(
                    f"Group transaction ({group_id}) sent with {len(transactions_to_send)} transactions",
                    suppress_log=suppress_log or False,
                )
            else:
                logger.info(
                    f"Sent transaction ID {transactions_to_send[0].get_txid()}",
                    suppress_log=suppress_log or False,
                )

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
                "attempting simulation to get more information",
                suppress_log=suppress_log or False,
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

        logger.error(
            "Received error executing Atomic Transaction Composer, for more information enable the debug flag",
            suppress_log=suppress_log or False,
        )
        raise e


class TransactionComposer:
    """A class for composing and managing Algorand transactions.

    Provides a high-level interface for building and executing transaction groups using the Algosdk library.
    Supports various transaction types including payments, asset operations, application calls, and key registrations.

    :param algod: An instance of AlgodClient used to get suggested params and send transactions
    :param get_signer: A function that takes an address and returns a TransactionSigner for that address
    :param get_suggested_params: Optional function to get suggested transaction parameters,
    defaults to using algod.suggested_params()
    :param default_validity_window: Optional default validity window for transactions in rounds, defaults to 10
    :param app_manager: Optional AppManager instance for compiling TEAL programs, defaults to None
    """

    def __init__(
        self,
        algod: AlgodClient,
        get_signer: Callable[[str], TransactionSigner],
        get_suggested_params: Callable[[], algosdk.transaction.SuggestedParams] | None = None,
        default_validity_window: int | None = None,
        app_manager: AppManager | None = None,
    ):
        # Map of transaction index in the atc to a max logical fee.
        # This is set using the value of either maxFee or staticFee.
        self._txn_max_fees: dict[int, AlgoAmount] = {}
        self._txns: list[TransactionWithSigner | TxnParams | AtomicTransactionComposer] = []
        self._atc: AtomicTransactionComposer = AtomicTransactionComposer()
        self._algod: AlgodClient = algod
        self._default_get_send_params = lambda: self._algod.suggested_params()
        self._get_suggested_params = get_suggested_params or self._default_get_send_params
        self._get_signer: Callable[[str], TransactionSigner] = get_signer
        self._default_validity_window: int = default_validity_window or 10
        self._default_validity_window_is_explicit: bool = default_validity_window is not None
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
            txn_with_signers: list[TransactionWithSignerAndContext] = []

            for txn in self._txns:
                txn_with_signers.extend(self._build_txn(txn, suggested_params))

            for ts in txn_with_signers:
                self._atc.add_transaction(ts)
                if ts.context.abi_method:
                    self._atc.method_dict[len(self._atc.txn_list) - 1] = ts.context.abi_method
                if ts.context.max_fee:
                    self._txn_max_fees[len(self._atc.txn_list) - 1] = ts.context.max_fee

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
                if ts.signer and ts.signer != NULL_SIGNER:
                    signers[idx] = ts.signer
                if isinstance(ts, TransactionWithSignerAndContext) and ts.context.abi_method:
                    method_calls[idx] = ts.context.abi_method
                idx += 1

        return BuiltTransactions(transactions=transactions, method_calls=method_calls, signers=signers)

    @deprecated("Use send() instead")
    def execute(
        self,
        *,
        max_rounds_to_wait: int | None = None,
    ) -> SendAtomicTransactionComposerResults:
        return self.send(SendParams(max_rounds_to_wait=max_rounds_to_wait))

    def send(
        self,
        params: SendParams | None = None,
    ) -> SendAtomicTransactionComposerResults:
        """Send the transaction group to the network.

        :param params: Parameters for the send operation
        :return: The transaction send results
        :raises Exception: If the transaction fails
        """
        group = self.build().transactions

        if not params:
            has_app_call = any(isinstance(txn.txn, ApplicationCallTxn) for txn in group)
            params = SendParams() if has_app_call else SendParams()

        cover_app_call_inner_transaction_fees = params.get("cover_app_call_inner_transaction_fees")
        populate_app_call_resources = params.get("populate_app_call_resources")
        wait_rounds = params.get("max_rounds_to_wait")
        sp = self._get_suggested_params() if not wait_rounds or cover_app_call_inner_transaction_fees else None

        if wait_rounds is None:
            last_round = max(txn.txn.last_valid_round for txn in group)
            assert sp is not None
            first_round = sp.first
            wait_rounds = last_round - first_round + 1

        try:
            return send_atomic_transaction_composer(
                self._atc,
                self._algod,
                max_rounds_to_wait=wait_rounds,
                suppress_log=params.get("suppress_log"),
                populate_app_call_resources=populate_app_call_resources,
                cover_app_call_inner_transaction_fees=cover_app_call_inner_transaction_fees,
                additional_atc_context=AdditionalAtcContext(
                    suggested_params=sp,
                    max_fees=self._txn_max_fees,
                ),
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
        from algokit_utils._debugging import simulate_and_persist_response, simulate_response

        atc = AtomicTransactionComposer() if skip_signatures else self._atc

        if skip_signatures:
            allow_empty_signatures = True
            transactions = self.build_transactions()
            for txn in transactions.transactions:
                atc.add_transaction(TransactionWithSigner(txn=txn, signer=NULL_SIGNER))
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

    def _build_atc(self, atc: AtomicTransactionComposer) -> list[TransactionWithSignerAndContext]:
        group = atc.build_group()

        txn_with_signers = []
        for idx, ts in enumerate(group):
            ts.txn.group = None
            if atc.method_dict.get(idx):
                txn_with_signers.append(
                    TransactionWithSignerAndContext(
                        txn=ts.txn,
                        signer=ts.signer,
                        context=TransactionContext(abi_method=atc.method_dict.get(idx)),
                    )
                )
            else:
                txn_with_signers.append(
                    TransactionWithSignerAndContext(
                        txn=ts.txn,
                        signer=ts.signer,
                        context=TransactionContext(abi_method=None),
                    )
                )

        return txn_with_signers

    def _common_txn_build_step(  # noqa: C901
        self,
        build_txn: Callable[[dict], algosdk.transaction.Transaction],
        params: _CommonTxnParams,
        txn_params: dict,
    ) -> TransactionWithContext:
        # Clone suggested params
        txn_params["sp"] = (
            algosdk.transaction.SuggestedParams(**txn_params["sp"].__dict__) if "sp" in txn_params else None
        )

        if params.lease:
            txn_params["lease"] = _encode_lease(params.lease)
        if params.rekey_to:
            txn_params["rekey_to"] = params.rekey_to
        if params.note:
            txn_params["note"] = params.note

        if txn_params["sp"]:
            if params.first_valid_round:
                txn_params["sp"].first = params.first_valid_round

            if params.last_valid_round:
                txn_params["sp"].last = params.last_valid_round
            else:
                # If the validity window isn't set in this transaction or by default and we are pointing at
                #  LocalNet set a bigger window to avoid dead transactions
                from algokit_utils.clients import ClientManager

                is_localnet = ClientManager.genesis_id_is_localnet(txn_params["sp"].gen)
                window = params.validity_window or (
                    1000
                    if is_localnet and not self._default_validity_window_is_explicit
                    else self._default_validity_window
                )
                txn_params["sp"].last = txn_params["sp"].first + window

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
        use_max_fee = params.max_fee and params.max_fee.micro_algo > (
            params.static_fee.micro_algo if params.static_fee else 0
        )
        logical_max_fee = params.max_fee if use_max_fee else params.static_fee

        return TransactionWithContext(
            txn=txn,
            context=TransactionContext(max_fee=logical_max_fee),
        )

    def _build_method_call(  # noqa: C901, PLR0912, PLR0915
        self, params: MethodCallParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> list[TransactionWithSignerAndContext]:
        method_args: list[ABIValue | TransactionWithSigner] = []
        txns_for_group: list[TransactionWithSignerAndContext] = []

        if params.args:
            for arg in reversed(params.args):
                if arg is None and len(txns_for_group) > 0:
                    # Pull last transaction from group as placeholder
                    placeholder_transaction = txns_for_group.pop()
                    method_args.append(placeholder_transaction)
                    continue
                if self._is_abi_value(arg):
                    method_args.append(arg)
                    continue

                if isinstance(arg, TransactionWithSigner):
                    method_args.append(arg)
                    continue

                if isinstance(arg, algosdk.transaction.Transaction):
                    # Wrap in TransactionWithSigner
                    signer = (
                        params.signer.signer
                        if isinstance(params.signer, TransactionSignerAccountProtocol)
                        else params.signer
                    )
                    method_args.append(
                        TransactionWithSignerAndContext(
                            txn=arg,
                            signer=signer if signer is not None else self._get_signer(params.sender),
                            context=TransactionContext(abi_method=None),
                        )
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
                        # Add all transactions except the last one in reverse order
                        txns_for_group.extend(temp_txn_with_signers[:-1])
                        # Add the last transaction to method_args
                        method_args.append(temp_txn_with_signers[-1])
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

                signer = (
                    params.signer.signer
                    if isinstance(params.signer, TransactionSignerAccountProtocol)
                    else params.signer
                )
                method_args.append(
                    TransactionWithSignerAndContext(
                        txn=txn.txn,
                        signer=signer or self._get_signer(params.sender),
                        context=TransactionContext(abi_method=params.method),
                    )
                )

                continue

        method_atc = AtomicTransactionComposer()
        max_fees: dict[int, AlgoAmount] = {}

        # Process in reverse order
        for arg in reversed(txns_for_group):
            atc_index = method_atc.get_tx_count() - 1

            if isinstance(arg, TransactionWithSignerAndContext) and arg.context:
                if arg.context.abi_method:
                    method_atc.method_dict[atc_index] = arg.context.abi_method

                if arg.context.max_fee is not None:
                    max_fees[atc_index] = arg.context.max_fee

        # Process method args that are transactions with ABI method info
        for i, arg in enumerate(reversed([a for a in method_args if isinstance(a, TransactionWithSignerAndContext)])):
            atc_index = method_atc.get_tx_count() + i
            if arg.context:
                if arg.context.abi_method:
                    method_atc.method_dict[atc_index] = arg.context.abi_method
                if arg.context.max_fee is not None:
                    max_fees[atc_index] = arg.context.max_fee

        app_id = params.app_id or 0
        approval_program = getattr(params, "approval_program", None)
        clear_program = getattr(params, "clear_state_program", None)
        extra_pages = None

        if app_id == 0:
            extra_pages = getattr(params, "extra_program_pages", None)
            if extra_pages is None and approval_program is not None:
                approval_len, clear_len = len(approval_program), len(clear_program or b"")
                extra_pages = (
                    int(math.floor((approval_len + clear_len) / algosdk.constants.APP_PAGE_MAX_SIZE))
                    if approval_len
                    else 0
                )

        txn_params = {
            "app_id": app_id,
            "method": params.method,
            "sender": params.sender,
            "sp": suggested_params,
            "signer": params.signer
            if params.signer is not None
            else self._get_signer(params.sender) or algosdk.atomic_transaction_composer.EmptySigner(),
            "method_args": list(reversed(method_args)),
            "on_complete": params.on_complete or algosdk.transaction.OnComplete.NoOpOC,
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
            "approval_program": approval_program,
            "clear_program": clear_program,
            "extra_pages": extra_pages,
        }

        def _add_method_call_and_return_txn(x: dict) -> algosdk.transaction.Transaction:
            method_atc.add_method_call(**x)
            return method_atc.build_group()[-1].txn

        result = self._common_txn_build_step(lambda x: _add_method_call_and_return_txn(x), params, txn_params)

        build_atc_resp = self._build_atc(method_atc)
        response = []
        for i, v in enumerate(build_atc_resp):
            max_fee = result.context.max_fee if i == method_atc.get_tx_count() - 1 else max_fees.get(i)
            context = TransactionContext(abi_method=v.context.abi_method, max_fee=max_fee)
            response.append(TransactionWithSignerAndContext(txn=v.txn, signer=v.signer, context=context))

        return response

    def _build_payment(
        self, params: PaymentParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> TransactionWithContext:
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
    ) -> TransactionWithContext:
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
    ) -> TransactionWithContext:
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
    ) -> TransactionWithContext:
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
    ) -> TransactionWithContext:
        txn_params = {
            "sender": params.sender,
            "sp": suggested_params,
            "index": params.asset_id,
        }

        return self._common_txn_build_step(lambda x: algosdk.transaction.AssetDestroyTxn(**x), params, txn_params)

    def _build_asset_freeze(
        self, params: AssetFreezeParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> TransactionWithContext:
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
    ) -> TransactionWithContext:
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
    ) -> TransactionWithContext:
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
    ) -> list[TransactionWithSignerAndContext]:
        match txn:
            case TransactionWithSigner():
                return [
                    TransactionWithSignerAndContext(txn=txn.txn, signer=txn.signer, context=TransactionContext.empty())
                ]
            case AtomicTransactionComposer():
                return self._build_atc(txn)
            case algosdk.transaction.Transaction():
                signer = self._get_signer(txn.sender)
                return [TransactionWithSignerAndContext(txn=txn, signer=signer, context=TransactionContext.empty())]
            case (
                AppCreateMethodCallParams()
                | AppCallMethodCallParams()
                | AppUpdateMethodCallParams()
                | AppDeleteMethodCallParams()
            ):
                return self._build_method_call(txn, suggested_params)

        signer = txn.signer.signer if isinstance(txn.signer, TransactionSignerAccountProtocol) else txn.signer  # type: ignore[assignment]
        signer = signer or self._get_signer(txn.sender)

        match txn:
            case PaymentParams():
                payment = self._build_payment(txn, suggested_params)
                return [TransactionWithSignerAndContext.from_txn_with_context(payment, signer)]
            case AssetCreateParams():
                asset_create = self._build_asset_create(txn, suggested_params)
                return [TransactionWithSignerAndContext.from_txn_with_context(asset_create, signer)]
            case AppCallParams() | AppUpdateParams() | AppCreateParams() | AppDeleteParams():
                app_call = self._build_app_call(txn, suggested_params)
                return [TransactionWithSignerAndContext.from_txn_with_context(app_call, signer)]
            case AssetConfigParams():
                asset_config = self._build_asset_config(txn, suggested_params)
                return [TransactionWithSignerAndContext.from_txn_with_context(asset_config, signer)]
            case AssetDestroyParams():
                asset_destroy = self._build_asset_destroy(txn, suggested_params)
                return [TransactionWithSignerAndContext.from_txn_with_context(asset_destroy, signer)]
            case AssetFreezeParams():
                asset_freeze = self._build_asset_freeze(txn, suggested_params)
                return [TransactionWithSignerAndContext.from_txn_with_context(asset_freeze, signer)]
            case AssetTransferParams():
                asset_transfer = self._build_asset_transfer(txn, suggested_params)
                return [TransactionWithSignerAndContext.from_txn_with_context(asset_transfer, signer)]
            case AssetOptInParams():
                asset_transfer = self._build_asset_transfer(
                    AssetTransferParams(**txn.__dict__, receiver=txn.sender, amount=0), suggested_params
                )
                return [TransactionWithSignerAndContext.from_txn_with_context(asset_transfer, signer)]
            case AssetOptOutParams():
                txn_dict = txn.__dict__
                creator = txn_dict.pop("creator")
                asset_transfer = self._build_asset_transfer(
                    AssetTransferParams(**txn_dict, receiver=txn.sender, amount=0, close_asset_to=creator),
                    suggested_params,
                )
                return [TransactionWithSignerAndContext.from_txn_with_context(asset_transfer, signer)]
            case OnlineKeyRegistrationParams() | OfflineKeyRegistrationParams():
                key_reg = self._build_key_reg(txn, suggested_params)
                return [TransactionWithSignerAndContext.from_txn_with_context(key_reg, signer)]
            case _:
                raise ValueError(f"Unsupported txn: {txn}")
