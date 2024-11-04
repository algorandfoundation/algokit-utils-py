from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

import algosdk
import algosdk.atomic_transaction_composer
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionSigner,
    TransactionWithSigner,
)
from algosdk.transaction import OnComplete
from deprecated import deprecated

from algokit_utils._debugging import simulate_and_persist_response, simulate_response
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.config import config

if TYPE_CHECKING:
    from collections.abc import Callable

    from algosdk.abi import Method
    from algosdk.box_reference import BoxReference
    from algosdk.v2client.algod import AlgodClient

    from algokit_utils.models.abi import ABIValue
    from algokit_utils.models.amount import AlgoAmount
    from algokit_utils.transactions.models import Arc2TransactionNote


@dataclass(frozen=True)
class SenderParam:
    sender: str


@dataclass(frozen=True)
class CommonTxnParams:
    """
    Common transaction parameters.

    :param signer: The function used to sign transactions.
    :param rekey_to: Change the signing key of the sender to the given address.
    :param note: Note to attach to the transaction.
    :param lease: Prevent multiple transactions with the same lease being included within the validity window.
    :param static_fee: The transaction fee. In most cases you want to use `extra_fee` unless setting the fee to 0 to be
    covered by another transaction.
    :param extra_fee: The fee to pay IN ADDITION to the suggested fee. Useful for covering inner transaction fees.
    :param max_fee: Throw an error if the fee for the transaction is more than this amount.
    :param validity_window: How many rounds the transaction should be valid for.
    :param first_valid_round: Set the first round this transaction is valid. If left undefined, the value from algod
    will be used. Only set this when you intentionally want this to be some time in the future.
    :param last_valid_round: The last round this transaction is valid. It is recommended to use validity_window instead.
    """

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


@dataclass(frozen=True)
class _RequiredPaymentParams:
    receiver: str
    amount: AlgoAmount


@dataclass(frozen=True)
class PaymentParams(CommonTxnParams, _RequiredPaymentParams):
    """
    Payment transaction parameters.

    :param receiver: The account that will receive the ALGO.
    :param amount: Amount to send.
    :param close_remainder_to: If given, close the sender account and send the remaining balance to this address.
    """

    close_remainder_to: str | None = None


@dataclass(frozen=True)
class _RequiredAssetCreateParams:
    total: int
    asset_name: str
    unit_name: str
    url: str


@dataclass(frozen=True)
class AssetCreateParams(
    CommonTxnParams,
    _RequiredAssetCreateParams,
):
    """
    Asset creation parameters.

    :param total: The total amount of the smallest divisible unit to create.
    :param decimals: The amount of decimal places the asset should have.
    :param default_frozen: Whether the asset is frozen by default in the creator address.
    :param manager: The address that can change the manager, reserve, clawback, and freeze addresses.
    There will permanently be no manager if undefined or an empty string.
    :param reserve: The address that holds the uncirculated supply.
    :param freeze: The address that can freeze the asset in any account.
    Freezing will be permanently disabled if undefined or an empty string.
    :param clawback: The address that can clawback the asset from any account.
    Clawback will be permanently disabled if undefined or an empty string.
    :param unit_name: The short ticker name for the asset.
    :param asset_name: The full name of the asset.
    :param url: The metadata URL for the asset.
    :param metadata_hash: Hash of the metadata contained in the metadata URL.
    """

    decimals: int | None = None
    default_frozen: bool | None = None
    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None
    metadata_hash: bytes | None = None


@dataclass(frozen=True)
class _RequiredAssetConfigParams:
    asset_id: int


@dataclass(frozen=True)
class AssetConfigParams(
    CommonTxnParams,
    _RequiredAssetConfigParams,
):
    """
    Asset configuration parameters.

    :param asset_id: ID of the asset.
    :param manager: The address that can change the manager, reserve, clawback, and freeze addresses.
    There will permanently be no manager if undefined or an empty string.
    :param reserve: The address that holds the uncirculated supply.
    :param freeze: The address that can freeze the asset in any account.
    Freezing will be permanently disabled if undefined or an empty string.
    :param clawback: The address that can clawback the asset from any account.
    Clawback will be permanently disabled if undefined or an empty string.
    """

    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None


@dataclass(frozen=True)
class _RequiredAssetFreezeParams:
    asset_id: int
    account: str
    frozen: bool


@dataclass(frozen=True)
class AssetFreezeParams(
    CommonTxnParams,
    _RequiredAssetFreezeParams,
):
    """
    Asset freeze parameters.

    :param asset_id: The ID of the asset.
    :param account: The account to freeze or unfreeze.
    :param frozen: Whether the assets in the account should be frozen.
    """


@dataclass(frozen=True)
class _RequiredAssetDestroyParams:
    asset_id: int


@dataclass(frozen=True)
class AssetDestroyParams(
    CommonTxnParams,
    _RequiredAssetDestroyParams,
):
    """
    Asset destruction parameters.

    :param asset_id: ID of the asset.
    """


@dataclass(frozen=True)
class _RequiredOnlineKeyRegistrationParams:
    vote_key: str
    selection_key: str
    vote_first: int
    vote_last: int
    vote_key_dilution: int


@dataclass(frozen=True)
class OnlineKeyRegistrationParams(
    CommonTxnParams,
    _RequiredOnlineKeyRegistrationParams,
):
    """
    Online key registration parameters.

    :param vote_key: The root participation public key.
    :param selection_key: The VRF public key.
    :param vote_first: The first round that the participation key is valid.
    Not to be confused with the `first_valid` round of the keyreg transaction.
    :param vote_last: The last round that the participation key is valid.
    Not to be confused with the `last_valid` round of the keyreg transaction.
    :param vote_key_dilution: This is the dilution for the 2-level participation key.
    It determines the interval (number of rounds) for generating new ephemeral keys.
    :param state_proof_key: The 64 byte state proof public key commitment.
    """

    state_proof_key: bytes | None = None


@dataclass(frozen=True)
class _RequiredAssetTransferParams:
    asset_id: int
    amount: int
    receiver: str


@dataclass(frozen=True)
class AssetTransferParams(
    CommonTxnParams,
    _RequiredAssetTransferParams,
):
    """
    Asset transfer parameters.

    :param asset_id: ID of the asset.
    :param amount: Amount of the asset to transfer (smallest divisible unit).
    :param receiver: The account to send the asset to.
    :param clawback_target: The account to take the asset from.
    :param close_asset_to: The account to close the asset to.
    """

    clawback_target: str | None = None
    close_asset_to: str | None = None


@dataclass(frozen=True)
class _RequiredAssetOptInParams:
    asset_id: int


@dataclass(frozen=True)
class AssetOptInParams(
    CommonTxnParams,
    _RequiredAssetOptInParams,
):
    """
    Asset opt-in parameters.

    :param asset_id: ID of the asset.
    """


@dataclass(frozen=True)
class _RequiredAssetOptOutParams:
    asset_id: int
    creator: str


@dataclass(frozen=True)
class AssetOptOutParams(
    CommonTxnParams,
    _RequiredAssetOptOutParams,
):
    """
    Asset opt-out parameters.
    """


@dataclass(frozen=True)
class AppCallParams(CommonTxnParams, SenderParam):
    """
    Application call parameters.

    :param on_complete: The OnComplete action.
    :param app_id: ID of the application.
    :param approval_program: The program to execute for all OnCompletes other than ClearState.
    :param clear_state_program: The program to execute for ClearState OnComplete.
    :param schema: The state schema for the app. This is immutable.
    :param args: Application arguments.
    :param account_references: Account references.
    :param app_references: App references.
    :param asset_references: Asset references.
    :param extra_pages: Number of extra pages required for the programs.
    :param box_references: Box references.
    """

    on_complete: OnComplete | None = None
    app_id: int | None = None
    approval_program: str | bytes | None = None
    clear_state_program: str | bytes | None = None
    schema: dict[str, int] | None = None
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    extra_pages: int | None = None
    box_references: list[BoxReference] | None = None


@dataclass(frozen=True)
class _RequiredAppCreateParams:
    approval_program: str | bytes
    clear_state_program: str | bytes


@dataclass(frozen=True)
class AppCreateParams(CommonTxnParams, SenderParam, _RequiredAppCreateParams):
    """
    Application create parameters.

    :param approval_program: The program to execute for all OnCompletes other than ClearState as raw teal (string)
    or compiled teal (bytes)
    :param clear_state_program: The program to execute for ClearState OnComplete as raw teal (string)
    or compiled teal (bytes)
    :param schema: The state schema for the app. This is immutable.
    :param on_complete: The OnComplete action (cannot be ClearState)
    :param args: Application arguments
    :param account_references: Account references
    :param app_references: App references
    :param asset_references: Asset references
    :param box_references: Box references
    :param extra_program_pages: Number of extra pages required for the programs
    """

    schema: dict[str, int] | None = None
    on_complete: OnComplete | None = None
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference] | None = None
    extra_program_pages: int | None = None


@dataclass(frozen=True)
class _RequiredAppUpdateParams:
    app_id: int
    approval_program: str | bytes
    clear_state_program: str | bytes


@dataclass(frozen=True)
class AppUpdateParams(CommonTxnParams, SenderParam, _RequiredAppUpdateParams):
    """
    Application update parameters.

    :param app_id: ID of the application
    :param approval_program: The program to execute for all OnCompletes other than ClearState as raw teal (string) or
    compiled teal (bytes)
    :param clear_state_program: The program to execute for ClearState OnComplete as raw teal (string) or compiled
    teal (bytes)
    """

    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference] | None = None
    on_complete: OnComplete | None = None


@dataclass(frozen=True)
class _RequiredAppDeleteParams:
    app_id: int


@dataclass(frozen=True)
class AppDeleteParams(
    CommonTxnParams,
    SenderParam,
    _RequiredAppDeleteParams,
):
    """
    Application delete parameters.

    :param app_id: ID of the application
    """

    app_id: int
    on_complete: OnComplete = OnComplete.DeleteApplicationOC


@dataclass(frozen=True)
class _RequiredMethodCallParams:
    app_id: int
    method: Method


@dataclass(frozen=True)
class AppMethodCall(CommonTxnParams, SenderParam, _RequiredMethodCallParams):
    """Base class for ABI method calls."""

    args: list | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference] | None = None


@dataclass(frozen=True)
class _RequiredAppMethodCallParams:
    app_id: int
    method: Method


@dataclass(frozen=True)
class AppMethodCallParams(CommonTxnParams, SenderParam, _RequiredAppMethodCallParams):
    """
    Method call parameters.

    :param app_id: ID of the application
    :param method: The ABI method to call
    :param args: Arguments to the ABI method
    :param on_complete: The OnComplete action (cannot be UpdateApplication or ClearState)
    """

    args: list[bytes] | None = None
    on_complete: OnComplete | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference] | None = None


@dataclass(frozen=True)
class AppCallMethodCall(AppMethodCall):
    """Parameters for a regular ABI method call.

    :param app_id: ID of the application
    :param method: The ABI method to call
    :param args: Arguments to the ABI method, either:
        * An ABI value
        * A transaction with explicit signer
        * A transaction (where the signer will be automatically assigned)
        * Another method call
        * None (represents a placeholder transaction argument)
    :param on_complete: The OnComplete action (cannot be UpdateApplication or ClearState)
    """

    app_id: int
    on_complete: OnComplete | None = None


@dataclass(frozen=True)
class _RequiredAppCreateMethodCallParams:
    approval_program: str | bytes
    clear_state_program: str | bytes


@dataclass(frozen=True)
class AppCreateMethodCall(AppMethodCall, _RequiredAppCreateMethodCallParams):
    """Parameters for an ABI method call that creates an application.

    :param approval_program: The program to execute for all OnCompletes other than ClearState
    :param clear_state_program: The program to execute for ClearState OnComplete
    :param schema: The state schema for the app
    :param on_complete: The OnComplete action (cannot be ClearState)
    :param extra_program_pages: Number of extra pages required for the programs
    """

    schema: dict[str, int] | None = None
    on_complete: OnComplete | None = None
    extra_program_pages: int | None = None


@dataclass(frozen=True)
class _RequiredAppUpdateMethodCallParams:
    app_id: int
    approval_program: str | bytes
    clear_state_program: str | bytes


@dataclass(frozen=True)
class AppUpdateMethodCall(AppMethodCall, _RequiredAppUpdateMethodCallParams):
    """Parameters for an ABI method call that updates an application.

    :param app_id: ID of the application
    :param approval_program: The program to execute for all OnCompletes other than ClearState
    :param clear_state_program: The program to execute for ClearState OnComplete
    """

    on_complete: OnComplete = OnComplete.UpdateApplicationOC


@dataclass(frozen=True)
class AppDeleteMethodCall(AppMethodCall):
    """Parameters for an ABI method call that deletes an application.

    :param app_id: ID of the application
    """

    app_id: int
    on_complete: OnComplete = OnComplete.DeleteApplicationOC


# Type alias for all possible method call types
MethodCallParams = AppCallMethodCall | AppCreateMethodCall | AppUpdateMethodCall | AppDeleteMethodCall


# Type alias for transaction arguments in method calls
AppMethodCallTransactionArgument = (
    TransactionWithSigner
    | algosdk.transaction.Transaction
    | AppCreateMethodCall
    | AppUpdateMethodCall
    | AppCallMethodCall
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
]


@dataclass
class BuiltTransactions:
    """
    Set of transactions built by TransactionComposer.

    :param transactions: The built transactions.
    :param method_calls: Any ABIMethod objects associated with any of the transactions in a map keyed by txn id.
    :param signers: Any TransactionSigner objects associated with any of the transactions in a map keyed by txn id.
    """

    transactions: list[algosdk.transaction.Transaction]
    method_calls: dict[int, Method]
    signers: dict[int, TransactionSigner]


@dataclass
class TransactionComposerBuildResult:
    atc: AtomicTransactionComposer
    transactions: list[TransactionWithSigner]
    method_calls: dict[int, Method]


class TransactionComposer:
    """
    A class for composing and managing Algorand transactions using the Algosdk library.

    Attributes:
        txn_method_map (dict[str, algosdk.abi.Method]): A dictionary that maps transaction IDs to their
        corresponding ABI methods.
        txns (List[Union[TransactionWithSigner, TxnParams, AtomicTransactionComposer]]): A list of transactions
        that have not yet been composed.
        atc (AtomicTransactionComposer): An instance of AtomicTransactionComposer used to compose transactions.
        algod (AlgodClient): The AlgodClient instance used by the composer for suggested params.
        get_suggested_params (Callable[[], algosdk.future.transaction.SuggestedParams]): A function that returns
        suggested parameters for transactions.
        get_signer (Callable[[str], TransactionSigner]): A function that takes an address as input and returns a
        TransactionSigner for that address.
        default_validity_window (int): The default validity window for transactions.
    """

    NULL_SIGNER: TransactionSigner = algosdk.atomic_transaction_composer.EmptySigner()

    def __init__(  # noqa: PLR0913
        self,
        algod: AlgodClient,
        get_signer: Callable[[str], TransactionSigner],
        get_suggested_params: Callable[[], algosdk.transaction.SuggestedParams] | None = None,
        default_validity_window: int | None = None,
        app_manager: AppManager | None = None,
    ):
        """
        Initialize an instance of the TransactionComposer class.

        Args:
            algod (AlgodClient): An instance of AlgodClient used to get suggested params and send transactions.
            get_signer (Callable[[str], TransactionSigner]): A function that takes an address as input and
            returns a TransactionSigner for that address.
            get_suggested_params (Optional[Callable[[], algosdk.future.transaction.SuggestedParams]], optional): A
            function that returns suggested parameters for transactions. If not provided, it defaults to using
            algod.suggested_params(). Defaults to None.
            default_validity_window (Optional[int], optional): The default validity window for transactions. If not
            provided, it defaults to 10. Defaults to None.
        """
        self.txn_method_map: dict[str, algosdk.abi.Method] = {}
        self.txns: list[TransactionWithSigner | TxnParams | AtomicTransactionComposer] = []
        self.atc: AtomicTransactionComposer = AtomicTransactionComposer()
        self.algod: AlgodClient = algod
        self.default_get_send_params = lambda: self.algod.suggested_params()
        self.get_suggested_params = get_suggested_params or self.default_get_send_params
        self.get_signer: Callable[[str], TransactionSigner] = get_signer
        self.default_validity_window: int = default_validity_window or 10
        self.app_manager = app_manager or AppManager(algod)

    def add_transaction(
        self, transaction: algosdk.transaction.Transaction, signer: TransactionSigner | None = None
    ) -> TransactionComposer:
        self.txns.append(TransactionWithSigner(txn=transaction, signer=signer or self.get_signer(transaction.sender)))
        return self

    def add_payment(self, params: PaymentParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_create(self, params: AssetCreateParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_config(self, params: AssetConfigParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_freeze(self, params: AssetFreezeParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_destroy(self, params: AssetDestroyParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_transfer(self, params: AssetTransferParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_opt_in(self, params: AssetOptInParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_opt_out(self, params: AssetOptOutParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_create(self, params: AppCreateParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_update(self, params: AppUpdateParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_delete(self, params: AppDeleteParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_call(self, params: AppCallParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_create_method_call(self, params: AppCreateMethodCall) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_update_method_call(self, params: AppUpdateMethodCall) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_delete_method_call(self, params: AppDeleteMethodCall) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_call_method_call(self, params: AppCallMethodCall) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_online_key_registration(self, params: OnlineKeyRegistrationParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_atc(self, atc: AtomicTransactionComposer) -> TransactionComposer:
        self.txns.append(atc)
        return self

    def count(self) -> int:
        return len(self.build_transactions().transactions)

    def build(self) -> TransactionComposerBuildResult:
        if self.atc.get_status() == algosdk.atomic_transaction_composer.AtomicTransactionComposerStatus.BUILDING:
            suggested_params = self.get_suggested_params()
            txn_with_signers: list[TransactionWithSigner] = []

            for txn in self.txns:
                txn_with_signers.extend(self._build_txn(txn, suggested_params))

            for ts in txn_with_signers:
                self.atc.add_transaction(ts)
                method = self.txn_method_map.get(ts.txn.get_txid())
                if method:
                    self.atc.method_dict[len(self.atc.txn_list) - 1] = method

        return TransactionComposerBuildResult(
            atc=self.atc,
            transactions=self.atc.build_group(),
            method_calls=self.atc.method_dict,
        )

    def rebuild(self) -> TransactionComposerBuildResult:
        self.atc = AtomicTransactionComposer()
        return self.build()

    def build_transactions(self) -> BuiltTransactions:
        suggested_params = self.get_suggested_params()

        transactions: list[algosdk.transaction.Transaction] = []
        method_calls: dict[int, Method] = {}
        signers: dict[int, TransactionSigner] = {}

        idx = 0

        for txn in self.txns:
            txn_with_signers: list[TransactionWithSigner] = []

            if isinstance(txn, MethodCallParams):
                txn_with_signers.extend(self._build_method_call(txn, suggested_params))
            else:
                txn_with_signers.extend(self._build_txn(txn, suggested_params))

            for ts in txn_with_signers:
                transactions.append(ts.txn)
                if ts.signer and ts.signer != self.NULL_SIGNER:
                    signers[idx] = ts.signer
                method = self.txn_method_map.get(ts.txn.get_txid())
                if method:
                    method_calls[idx] = method
                idx += 1

        return BuiltTransactions(transactions=transactions, method_calls=method_calls, signers=signers)

    @deprecated(reason="Use send() instead", version="3.0.0")
    def execute(
        self,
        *,
        max_rounds_to_wait: int | None = None,
    ) -> algosdk.atomic_transaction_composer.AtomicTransactionResponse:
        return self.send(
            max_rounds_to_wait=max_rounds_to_wait,
        )

    def send(
        self,
        max_rounds_to_wait: int | None = None,
    ) -> algosdk.atomic_transaction_composer.AtomicTransactionResponse:
        group = self.build().transactions

        wait_rounds = max_rounds_to_wait
        if wait_rounds is None:
            last_round = max(txn.txn.last_valid_round for txn in group)
            first_round = self.get_suggested_params().first
            wait_rounds = last_round - first_round + 1

        try:
            return self.atc.execute(client=self.algod, wait_rounds=wait_rounds)  # TODO: reimplement ATC
        except algosdk.error.AlgodHTTPError as e:
            raise Exception(f"Transaction failed: {e}") from e

    def simulate(self) -> algosdk.atomic_transaction_composer.SimulateAtomicTransactionResponse:
        if config.debug and config.project_root and config.trace_all:
            return simulate_and_persist_response(
                self.atc,
                config.project_root,
                self.algod,
                config.trace_buffer_size_mb,
            )

        return simulate_response(
            self.atc,
            self.algod,
        )

    @staticmethod
    def arc2_note(note: Arc2TransactionNote) -> bytes:
        """
        Create an encoded transaction note that follows the ARC-2 spec.

        https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0002.md

        :param note: The ARC-2 note to encode.
        """

        arc2_payload = f"{note['dapp_name']}:{note['format']}{note['data']}"
        return arc2_payload.encode("utf-8")

    def _build_atc(self, atc: AtomicTransactionComposer) -> list[TransactionWithSigner]:
        group = atc.build_group()

        for ts in group:
            ts.txn.group = None

        method = atc.method_dict.get(len(group) - 1)
        if method:
            self.txn_method_map[group[-1].txn.get_txid()] = method

        return group

    def _common_txn_build_step(
        self,
        params: CommonTxnParams,
        txn: algosdk.transaction.Transaction,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> algosdk.transaction.Transaction:
        if params.lease:
            txn.lease = params.lease
        if params.rekey_to:
            txn.rekey_to = algosdk.encoding.decode_address(params.rekey_to)
        if params.note:
            txn.note = params.note

        if params.first_valid_round:
            txn.first_valid_round = params.first_valid_round

        if params.last_valid_round:
            txn.last_valid_round = params.last_valid_round
        else:
            txn.last_valid_round = txn.first_valid_round + (params.validity_window or self.default_validity_window)

        if params.static_fee is not None and params.extra_fee is not None:
            raise ValueError("Cannot set both static_fee and extra_fee")

        if params.static_fee is not None:
            txn.fee = params.static_fee.micro_algos
        else:
            txn.fee = txn.estimate_size() * suggested_params.fee or algosdk.constants.min_txn_fee
            if params.extra_fee:
                txn.fee += params.extra_fee

        if params.max_fee is not None and txn.fee > params.max_fee:
            raise ValueError(f"Transaction fee {txn.fee} is greater than max_fee {params.max_fee}")

        return txn

    def _build_method_call(  # noqa: C901, PLR0912
        self, params: MethodCallParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> list[TransactionWithSigner]:
        method_args: list[ABIValue | TransactionWithSigner] = []
        arg_offset = 0

        if params.args:
            for i, arg in enumerate(params.args):
                if self._is_abi_value(arg):
                    method_args.append(arg)
                    continue

                if algosdk.abi.is_abi_transaction_type(params.method.args[i + arg_offset].type):
                    match arg:
                        case (
                            AppCreateMethodCall()
                            | AppCallMethodCall()
                            | AppUpdateMethodCall()
                            | AppDeleteMethodCall()
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
                        case OnlineKeyRegistrationParams():
                            txn = self._build_key_reg(arg, suggested_params)
                        case _:
                            raise ValueError(f"Unsupported method arg transaction type: {arg!s}")

                    method_args.append(
                        TransactionWithSigner(txn=txn, signer=params.signer or self.get_signer(params.sender))
                    )

                    continue

                raise ValueError(f"Unsupported method arg: {arg!s}")

        method_atc = AtomicTransactionComposer()

        method_atc.add_method_call(
            app_id=params.app_id or 0,
            method=params.method,
            sender=params.sender,
            sp=suggested_params,
            signer=params.signer or self.get_signer(params.sender),
            method_args=method_args,
            on_complete=algosdk.transaction.OnComplete.NoOpOC,
            note=params.note,
            lease=params.lease,
            boxes=[(ref.app_index, ref.name) for ref in params.box_references] if params.box_references else None,
        )

        return self._build_atc(method_atc)

    def _build_payment(
        self, params: PaymentParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.PaymentTxn(
            sender=params.sender,
            sp=suggested_params,
            receiver=params.receiver,
            amt=params.amount.micro_algos,
            close_remainder_to=params.close_remainder_to,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_create(
        self, params: AssetCreateParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.AssetCreateTxn(
            sender=params.sender,
            sp=suggested_params,
            total=params.total,
            default_frozen=params.default_frozen or False,
            unit_name=params.unit_name,
            asset_name=params.asset_name,
            manager=params.manager,
            reserve=params.reserve,
            freeze=params.freeze,
            clawback=params.clawback,
            url=params.url,
            metadata_hash=params.metadata_hash,
            decimals=params.decimals or 0,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_app_call(
        self,
        params: AppCallParams | AppUpdateParams | AppCreateParams,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> algosdk.transaction.Transaction:
        app_id = params.app_id if isinstance(params, AppCallParams | AppUpdateMethodCall) else None

        approval_program = None
        clear_program = None

        if isinstance(params, AppUpdateParams | AppCreateParams):
            if isinstance(params.approval_program, str):
                approval_program = self.app_manager.compile_teal(params.approval_program).compiled_base64_to_bytes
            elif isinstance(params.approval_program, bytes):
                approval_program = params.approval_program

            if isinstance(params.clear_state_program, str):
                clear_program = self.app_manager.compile_teal(params.clear_state_program).compiled_base64_to_bytes
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

        if not app_id and isinstance(params, AppCreateParams):
            if not sdk_params["approval_program"] or not sdk_params["clear_program"]:
                raise ValueError("approval_program and clear_program are required for application creation")

            if not params.schema:
                raise ValueError("schema is required for application creation")

            txn = algosdk.transaction.ApplicationCreateTxn(
                **sdk_params,
                global_schema=algosdk.transaction.StateSchema(
                    num_uints=params.schema.get("global_uints", 0),
                    num_byte_slices=params.schema.get("global_byte_slices", 0),
                ),
                local_schema=algosdk.transaction.StateSchema(
                    num_uints=params.schema.get("local_uints", 0),
                    num_byte_slices=params.schema.get("local_byte_slices", 0),
                ),
                extra_pages=params.extra_program_pages
                or math.floor((approval_program_len + clear_program_len) / algosdk.constants.APP_PAGE_MAX_SIZE)
                if params.extra_program_pages
                else 0,
            )
        else:
            txn = algosdk.transaction.ApplicationCallTxn(**sdk_params, index=app_id)  # type: ignore[assignment]

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_config(
        self, params: AssetConfigParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.AssetConfigTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
            manager=params.manager,
            reserve=params.reserve,
            freeze=params.freeze,
            clawback=params.clawback,
            strict_empty_address_check=False,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_destroy(
        self, params: AssetDestroyParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.AssetDestroyTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_freeze(
        self, params: AssetFreezeParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.AssetFreezeTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
            target=params.account,
            new_freeze_state=params.frozen,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_transfer(
        self, params: AssetTransferParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.AssetTransferTxn(
            sender=params.sender,
            sp=suggested_params,
            receiver=params.receiver,
            amt=params.amount,
            index=params.asset_id,
            close_assets_to=params.close_asset_to,
            revocation_target=params.clawback_target,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_key_reg(
        self, params: OnlineKeyRegistrationParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.KeyregTxn(
            sender=params.sender,
            sp=suggested_params,
            votekey=params.vote_key,
            selkey=params.selection_key,
            votefst=params.vote_first,
            votelst=params.vote_last,
            votekd=params.vote_key_dilution,
            rekey_to=params.rekey_to,
            nonpart=False,
            sprfkey=params.state_proof_key,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _is_abi_value(self, x: bool | float | str | bytes | list | TxnParams) -> bool:
        if isinstance(x, list):
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
            case AppCreateMethodCall() | AppCallMethodCall() | AppUpdateMethodCall() | AppDeleteMethodCall():
                return self._build_method_call(txn, suggested_params)

        signer = txn.signer or self.get_signer(txn.sender)

        match txn:
            case PaymentParams():
                payment = self._build_payment(txn, suggested_params)
                return [TransactionWithSigner(txn=payment, signer=signer)]
            case AssetCreateParams():
                asset_create = self._build_asset_create(txn, suggested_params)
                return [TransactionWithSigner(txn=asset_create, signer=signer)]
            case AppCallParams() | AppUpdateParams() | AppCreateParams():
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
            case OnlineKeyRegistrationParams():
                key_reg = self._build_key_reg(txn, suggested_params)
                return [TransactionWithSigner(txn=key_reg, signer=signer)]
            case _:
                raise ValueError(f"Unsupported txn: {txn}")