import base64
import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import Any, TypeAlias, TypedDict, cast

from algokit_abi import arc56
from algokit_algod_client import AlgodClient
from algokit_algod_client import models as algod_models
from algokit_algod_client.exceptions import UnexpectedStatusError
from algokit_algod_client.models import SimulateTransactionResult
from algokit_common.constants import MAX_TRANSACTION_GROUP_SIZE
from algokit_transact import make_empty_transaction_signer
from algokit_transact.codec.signed import decode_signed_transactions
from algokit_transact.models.transaction import Transaction, TransactionType
from algokit_transact.ops.fees import calculate_fee
from algokit_transact.ops.group import group_transactions
from algokit_transact.ops.ids import get_transaction_id
from algokit_transact.ops.validate import validate_transaction
from algokit_transact.signer import AddressWithTransactionSigner, TransactionSigner
from algokit_utils.applications.abi import ABIReturn
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.clients.client_manager import ClientManager
from algokit_utils.config import config
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.models.transaction import Arc2TransactionNote, SendParams
from algokit_utils.transactions.builders import (
    build_app_call_method_call_transaction,
    build_app_call_transaction,
    build_app_create_method_call_transaction,
    build_app_create_transaction,
    build_app_delete_method_call_transaction,
    build_app_delete_transaction,
    build_app_update_method_call_transaction,
    build_app_update_transaction,
    build_asset_config_transaction,
    build_asset_create_transaction,
    build_asset_destroy_transaction,
    build_asset_freeze_transaction,
    build_asset_opt_in_transaction,
    build_asset_opt_out_transaction,
    build_asset_transfer_transaction,
    build_offline_key_registration_transaction,
    build_online_key_registration_transaction,
    build_payment_transaction,
)
from algokit_utils.transactions.builders.common import calculate_inner_fee_delta
from algokit_utils.transactions.composer_resources import populate_group_resources, populate_transaction_resources
from algokit_utils.transactions.fee_coverage import FeeDelta, FeePriority
from algokit_utils.transactions.helpers import calculate_extra_program_pages
from algokit_utils.transactions.types import (
    AppCallMethodCallParams,
    AppCallParams,
    AppCreateMethodCallParams,
    AppCreateParams,
    AppCreateSchema,
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
    TxnParams,
)

ABIMethod: TypeAlias = arc56.Method

__all__ = [
    "MAX_TRANSACTION_GROUP_SIZE",
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
    "ErrorTransformer",
    "ErrorTransformerError",
    "InvalidErrorTransformerValueError",
    "OfflineKeyRegistrationParams",
    "OnlineKeyRegistrationParams",
    "PaymentParams",
    "SendParams",
    "SendTransactionComposerResults",
    "TransactionComposer",
    "TransactionComposerConfig",
    "TransactionComposerError",
    "TransactionComposerParams",
    "TransactionWithSigner",
    "TxnParams",
    "calculate_extra_program_pages",
]

AppMethodCallTransactionArgument = Any
TxnParamTypes = (
    PaymentParams
    | AssetCreateParams
    | AssetConfigParams
    | AssetFreezeParams
    | AssetDestroyParams
    | AssetTransferParams
    | AssetOptInParams
    | AssetOptOutParams
    | AppCreateParams
    | AppUpdateParams
    | AppDeleteParams
    | AppCallParams
    | OnlineKeyRegistrationParams
    | OfflineKeyRegistrationParams
)
MethodCallTxnParamTypes = (
    AppCreateMethodCallParams | AppUpdateMethodCallParams | AppDeleteMethodCallParams | AppCallMethodCallParams
)


class ErrorTransformerError(RuntimeError):
    """Raised when an error transformer throws."""


ErrorTransformer = Callable[[Exception], Exception]


class InvalidErrorTransformerValueError(RuntimeError):
    """Raised when an error transformer returns a non-error value."""

    def __init__(self, original_error: Exception, value: object) -> None:
        super().__init__(
            f"An error transformer returned a non-error value: {value}. "
            f"The original error before any transformation: {original_error}"
        )


class TransactionComposerError(RuntimeError):
    """Error raised when transaction composer fails to send transactions.

    Contains detailed debugging information including simulation traces and sent transactions.
    """

    def __init__(
        self,
        message: str,
        *,
        cause: Exception | None = None,
        traces: list[SimulateTransactionResult] | None = None,
        sent_transactions: list[Transaction] | None = None,
        simulate_response: algod_models.SimulateResponse | None = None,
    ) -> None:
        super().__init__(message)
        self.__cause__ = cause
        self.traces = traces
        self.sent_transactions = sent_transactions
        self.simulate_response = simulate_response


@dataclass(slots=True)
class TransactionComposerConfig:
    cover_app_call_inner_transaction_fees: bool = False
    populate_app_call_resources: bool = True


@dataclass(slots=True)
class TransactionComposerParams:
    algod: AlgodClient
    get_signer: Callable[[str], TransactionSigner]
    get_suggested_params: Callable[[], algod_models.SuggestedParams] | None = None
    default_validity_window: int | None = None
    app_manager: AppManager | None = None
    error_transformers: list[ErrorTransformer] | None = None
    composer_config: TransactionComposerConfig | None = None


class _BuilderKwargs(TypedDict):
    suggested_params: algod_models.SuggestedParams
    default_validity_window: int
    default_validity_window_is_explicit: bool
    is_localnet: bool


@dataclass(slots=True, frozen=True)
class TransactionWithSigner:
    txn: Transaction
    signer: TransactionSigner
    method: ABIMethod | None = None


@dataclass(slots=True, frozen=True)
class BuiltTransactions:
    transactions: list[Transaction]
    method_calls: dict[int, ABIMethod]
    signers: dict[int, TransactionSigner]


@dataclass(slots=True, frozen=True)
class SendTransactionComposerResults:
    tx_ids: list[str]
    transactions: list[Transaction]
    confirmations: list[algod_models.PendingTransactionResponse]
    returns: list[ABIReturn]
    group_id: str | None = None
    simulate_response: algod_models.SimulateResponse | None = None


@dataclass(slots=True)
class _QueuedTransaction:
    txn: Transaction | TxnParams
    signer: TransactionSigner | AddressWithTransactionSigner | None
    max_fee: AlgoAmount | None = None


@dataclass(slots=True)
class _BuiltTxnSpec:
    txn: Transaction
    signer: TransactionSigner | None
    logical_max_fee: AlgoAmount | None
    method: ABIMethod | None = None


@dataclass(slots=True)
class _TransactionAnalysis:
    required_fee_delta: FeeDelta | None
    unnamed_resources_accessed: algod_models.SimulateUnnamedResourcesAccessed | None


@dataclass(slots=True)
class _GroupAnalysis:
    transactions: list[_TransactionAnalysis]
    unnamed_resources_accessed: algod_models.SimulateUnnamedResourcesAccessed | None


class TransactionComposer:
    """Light-weight transaction composer built on top of algokit_transact."""

    def __init__(self, params: TransactionComposerParams) -> None:
        self._algod = params.algod
        self._get_signer = params.get_signer
        self._get_suggested_params = params.get_suggested_params or self._algod.suggested_params
        self._config = params.composer_config or TransactionComposerConfig()
        self._error_transformers = params.error_transformers or []
        self._default_validity_window = params.default_validity_window or 10
        self._default_validity_window_is_explicit = params.default_validity_window is not None
        self._app_manager = params.app_manager or AppManager(params.algod)

        self._queued: list[_QueuedTransaction] = []
        self._transactions_with_signers: list[TransactionWithSigner] | None = None
        self._signed_transactions: list[bytes] | None = None
        self._raw_built_transactions: list[Transaction] | None = None

    def clone(self, composer_config: TransactionComposerConfig | None = None) -> "TransactionComposer":
        """Create a shallow copy of this composer, optionally overriding config flags."""
        config_override = composer_config or self._config
        cloned = TransactionComposer(
            TransactionComposerParams(
                algod=self._algod,
                get_signer=self._get_signer,
                get_suggested_params=self._get_suggested_params,
                default_validity_window=self._default_validity_window
                if self._default_validity_window_is_explicit
                else None,
                app_manager=self._app_manager,
                error_transformers=list(self._error_transformers),
                composer_config=TransactionComposerConfig(
                    cover_app_call_inner_transaction_fees=config_override.cover_app_call_inner_transaction_fees,
                    populate_app_call_resources=config_override.populate_app_call_resources,
                ),
            )
        )
        cloned._queued = [self._clone_entry(entry) for entry in self._queued]
        cloned._raw_built_transactions = list(self._raw_built_transactions) if self._raw_built_transactions else None
        return cloned

    def register_error_transformer(self, transformer: ErrorTransformer) -> "TransactionComposer":
        self._error_transformers.append(transformer)
        return self

    def add_transaction(self, txn: Transaction, signer: TransactionSigner | None = None) -> "TransactionComposer":
        validate_transaction(txn)
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=self._sanitize_transaction(txn), signer=signer))
        return self

    def add_payment(self, params: PaymentParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_asset_create(self, params: AssetCreateParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_asset_config(self, params: AssetConfigParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_asset_freeze(self, params: AssetFreezeParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_asset_destroy(self, params: AssetDestroyParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_asset_transfer(self, params: AssetTransferParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_asset_opt_in(self, params: AssetOptInParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_asset_opt_out(self, params: AssetOptOutParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_app_create(self, params: AppCreateParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_app_update(self, params: AppUpdateParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_app_delete(self, params: AppDeleteParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_app_call(self, params: AppCallParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_app_create_method_call(self, params: AppCreateMethodCallParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_app_update_method_call(self, params: AppUpdateMethodCallParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_app_delete_method_call(self, params: AppDeleteMethodCallParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_app_call_method_call(self, params: AppCallMethodCallParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_online_key_registration(self, params: OnlineKeyRegistrationParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def add_offline_key_registration(self, params: OfflineKeyRegistrationParams) -> "TransactionComposer":
        self._ensure_not_built()
        self._queued.append(_QueuedTransaction(txn=params, signer=params.signer))
        return self

    def count(self) -> int:
        return len(self._queued)

    def rebuild(self) -> BuiltTransactions:
        self._transactions_with_signers = None
        self._signed_transactions = None
        self._raw_built_transactions = None
        return self.build()

    @staticmethod
    def arc2_note(note: Arc2TransactionNote) -> bytes:
        pattern = r"^[a-zA-Z0-9][a-zA-Z0-9_/@.-]{4,31}$"
        if not re.match(pattern, note["dapp_name"]):
            raise ValueError(
                "dapp_name must be 5-32 chars, start with alphanumeric, and contain only alphanumeric, _, /, @, ., or -"
            )

        data = note["data"]
        if note["format"] == "j" and isinstance(data, (dict | list)):
            data = json.dumps(data)

        arc2_payload = f"{note['dapp_name']}:{note['format']}{data}"
        return arc2_payload.encode("utf-8")

    def add_transaction_composer(self, composer: "TransactionComposer") -> "TransactionComposer":
        self._ensure_not_built()
        current_size = len(self._queued)
        composer_size = len(composer._queued)  # noqa: SLF001
        new_size = current_size + composer_size
        if new_size > MAX_TRANSACTION_GROUP_SIZE:
            raise ValueError(
                "Adding transactions from composer would exceed the maximum group size. "
                f"Current: {current_size}, Adding: {composer_size}, "
                f"Maximum: {MAX_TRANSACTION_GROUP_SIZE}"
            )
        for entry in composer._queued:  # noqa: SLF001
            self._queued.append(self._clone_entry(entry))
        return self

    def build(self) -> BuiltTransactions:
        """Build transactions with grouping, resource population, and fee adjustments applied."""
        self._ensure_built()
        assert self._transactions_with_signers is not None
        transactions = [entry.txn for entry in self._transactions_with_signers]
        signers = {index: entry.signer for index, entry in enumerate(self._transactions_with_signers)}
        method_calls = {
            index: entry.method for index, entry in enumerate(self._transactions_with_signers) if entry.method
        }
        return BuiltTransactions(transactions=transactions, method_calls=method_calls, signers=signers)

    def build_transactions(self) -> BuiltTransactions:
        """Build queued transactions without resource population or grouping.

        Returns raw transactions, method call metadata, and any explicit signers. This does not
        populate unnamed resources or adjust fees, and it leaves grouping unchanged.
        """
        if not self._queued:
            raise ValueError("Cannot build an empty transaction group")

        suggested_params = self._get_suggested_params()
        genesis_id = getattr(suggested_params, "genesis_id", None)
        if genesis_id is None:
            genesis_id = getattr(suggested_params, "gen", "")
        is_localnet = ClientManager.genesis_id_is_localnet(genesis_id or "")

        built_entries, method_calls = self._build_txn_specs(suggested_params, is_localnet=is_localnet)
        transactions = [entry.txn for entry in built_entries]
        self._raw_built_transactions = list(transactions)
        signers = {index: entry.signer for index, entry in enumerate(built_entries) if entry.signer is not None}
        return BuiltTransactions(transactions=transactions, method_calls=method_calls, signers=signers)

    def gather_signatures(self) -> list[bytes]:
        self._ensure_built()
        if self._signed_transactions is None:
            self._signed_transactions = self._sign_transactions(self._transactions_with_signers or [])
        return self._signed_transactions

    def send(self, params: SendParams | None = None) -> SendTransactionComposerResults:
        """Compose the transaction group and send it to the network."""
        params = params or SendParams()

        # Update config from params if provided, falling back to composer's config
        effective_cover = params.get(
            "cover_app_call_inner_transaction_fees", self._config.cover_app_call_inner_transaction_fees
        )
        effective_populate = params.get("populate_app_call_resources", self._config.populate_app_call_resources)

        if (
            effective_cover != self._config.cover_app_call_inner_transaction_fees
            or effective_populate != self._config.populate_app_call_resources
        ):
            self._config = TransactionComposerConfig(
                cover_app_call_inner_transaction_fees=effective_cover,
                populate_app_call_resources=effective_populate,
            )
            # Reset built state to force rebuild with new config
            self._transactions_with_signers = None
            self._signed_transactions = None
            self._raw_built_transactions = None

        # Build and sign transactions - let validation errors bubble up as-is
        signed_transactions = self.gather_signatures()

        if config.debug and config.trace_all and config.project_root:
            try:
                self.simulate(result_on_failure=True)
            except Exception:
                config.logger.debug(
                    "Failed to simulate and persist trace for debugging",
                    exc_info=True,
                    extra={"suppress_log": params.get("suppress_log")},
                )

        # Send transactions and handle network errors
        try:
            self._algod.send_raw_transaction(signed_transactions)

            tx_ids = [get_transaction_id(entry.txn) for entry in self._transactions_with_signers or []]
            group_id = self._group_id()
            if not params.get("suppress_log") and tx_ids:
                if len(tx_ids) > 1:
                    config.logger.info(
                        "Sent group of %s transactions (%s)",
                        len(tx_ids),
                        group_id or "no-group",
                        extra={"suppress_log": params.get("suppress_log")},
                    )
                    config.logger.debug(
                        "Transaction IDs (%s): %s",
                        group_id or "no-group",
                        tx_ids,
                        extra={"suppress_log": params.get("suppress_log")},
                    )
                else:
                    txn = (self._transactions_with_signers or [])[0].txn
                    config.logger.info(
                        "Sent transaction ID %s %s from %s",
                        tx_ids[0],
                        txn.transaction_type,
                        txn.sender,
                        extra={"suppress_log": params.get("suppress_log")},
                    )
            confirmations = self._wait_for_confirmations(tx_ids, params)
            abi_returns = self._parse_abi_return_values(confirmations)
            return SendTransactionComposerResults(
                tx_ids=tx_ids,
                transactions=[entry.txn for entry in self._transactions_with_signers or []],
                confirmations=confirmations,
                returns=abi_returns,
                group_id=group_id,
            )
        except Exception as err:
            sent_transactions = self._resolve_error_transactions()
            simulate_response: algod_models.SimulateResponse | None = None
            traces: list[SimulateTransactionResult] = []

            if config.debug and sent_transactions:
                simulate_response, traces = self._simulate_error_context(
                    sent_transactions,
                    suppress_log=params.get("suppress_log"),
                )

            if config.debug and config.project_root and not config.trace_all and simulate_response is None:
                from algokit_utils._debugging import simulate_and_persist_response

                try:
                    simulate_and_persist_response(
                        self,
                        config.project_root,
                        self._algod,
                        buffer_size_mb=config.trace_buffer_size_mb,
                    )
                except Exception:
                    config.logger.debug(
                        "Failed to simulate and persist trace for debugging",
                        exc_info=True,
                        extra={"suppress_log": params.get("suppress_log")},
                    )

            interpreted = self._interpret_error(err)
            composer_error = self._create_composer_error(interpreted, sent_transactions, simulate_response, traces)
            raise self._transform_error(composer_error) from err

    def simulate(
        self,
        *,
        skip_signatures: bool = False,
        result_on_failure: bool = False,
        **raw_options: Any,
    ) -> SendTransactionComposerResults:
        """Compose the transaction group and simulate execution without submitting to the network.

        Args:
            skip_signatures: Whether to skip signatures for all built transactions and use an empty signer instead.
                This will set `allow_empty_signatures` and `fix_signers` when sending the request to algod.
            result_on_failure: Whether to return the result on simulation failure instead of throwing an error.
                Defaults to False (throws on failure).
            **raw_options: Additional options to pass to the simulate request.

        Returns:
            SendTransactionComposerResults containing simulation results.
        """
        try:
            persist_trace = bool(raw_options.pop("_persist_trace", True))
            txns_with_signers: list[TransactionWithSigner]
            if "throw_on_failure" in raw_options:
                raw_options.pop("throw_on_failure")
            effective_throw_on_failure = not result_on_failure
            if skip_signatures:
                raw_options.setdefault("allow_empty_signatures", True)
                raw_options.setdefault("fix_signers", True)
            if "allow_more_logs" in raw_options:
                raw_options["allow_more_logging"] = raw_options.pop("allow_more_logs")
            if "simulation_round" in raw_options:
                raw_options["round_"] = raw_options.pop("simulation_round")

            txns_with_signers = self._build_transactions_for_simulation()

            if config.debug:
                raw_options.setdefault("allow_more_logging", True)
                raw_options.setdefault(
                    "exec_trace_config",
                    algod_models.SimulateTraceConfig(
                        enable=True,
                        scratch_change=True,
                        stack_change=True,
                        state_change=True,
                    ),
                )

            empty_signer: TransactionSigner = make_empty_transaction_signer()
            signing_entries = [
                TransactionWithSigner(
                    txn=entry.txn,
                    signer=empty_signer if skip_signatures else entry.signer,
                )
                for entry in txns_with_signers
            ]
            encoded_signed_transactions = self._sign_transactions(signing_entries)
            signed_transactions = decode_signed_transactions(encoded_signed_transactions)

            request = algod_models.SimulateRequest(
                txn_groups=[algod_models.SimulateRequestTransactionGroup(txns=signed_transactions)],
                **raw_options,
            )
            response = self._algod.simulate_transactions(request)

            if response.txn_groups and response.txn_groups[0].failure_message and effective_throw_on_failure:
                raise RuntimeError(response.txn_groups[0].failure_message)

            tx_ids = [get_transaction_id(entry.txn) for entry in txns_with_signers]
            group = response.txn_groups[0] if response.txn_groups else None
            confirmations = [result.txn_result for result in (group.txn_results if group else [])]
            method_calls = {index: entry.method for index, entry in enumerate(txns_with_signers) if entry.method}
            abi_returns = self._parse_abi_return_values(confirmations, method_calls)
            result = SendTransactionComposerResults(
                tx_ids=tx_ids,
                transactions=[entry.txn for entry in txns_with_signers],
                confirmations=confirmations,
                returns=abi_returns,
                group_id=(
                    base64.b64encode(txns_with_signers[0].txn.group).decode()
                    if txns_with_signers and txns_with_signers[0].txn.group
                    else None
                ),
                simulate_response=response,
            )

            if config.debug and config.project_root and config.trace_all and persist_trace:
                from algokit_utils._debugging import simulate_and_persist_response

                try:
                    simulate_and_persist_response(
                        self,
                        config.project_root,
                        self._algod,
                        buffer_size_mb=config.trace_buffer_size_mb,
                        result=result,
                    )
                except Exception:
                    config.logger.debug("Failed to persist simulation trace", exc_info=True)

            return result
        except Exception as err:
            interpreted = self._interpret_error(err)
            raise self._transform_error(interpreted) from err

    def _ensure_not_built(self) -> None:
        if self._transactions_with_signers is not None:
            raise RuntimeError("Transactions have already been built")
        if len(self._queued) >= MAX_TRANSACTION_GROUP_SIZE:
            raise ValueError("Transaction group size exceeds maximum limit")

    def _build_txn_specs(
        self,
        suggested_params: algod_models.SuggestedParams,
        *,
        is_localnet: bool,
    ) -> tuple[list[_BuiltTxnSpec], dict[int, ABIMethod]]:
        if not self._queued:
            raise ValueError("Cannot build an empty transaction group")

        built_entries: list[_BuiltTxnSpec] = []
        method_calls: dict[int, ABIMethod] = {}

        for entry in self._queued:
            sender = entry.txn.sender if hasattr(entry.txn, "sender") else None
            override_signer = self._resolve_param_signer(entry.signer, sender)
            if isinstance(entry.txn, Transaction):
                txn = self._sanitize_transaction(entry.txn)
                built_entries.append(
                    _BuiltTxnSpec(txn=txn, signer=override_signer, logical_max_fee=entry.max_fee, method=None)
                )
                continue

            specs = self._build_txn_from_params(entry.txn, suggested_params, is_localnet=is_localnet)
            for spec in specs:
                resolved_signer = spec.signer or override_signer
                if resolved_signer is None:
                    raise ValueError("Signer is required for transaction in composer queue")
                index = len(built_entries)
                built_entries.append(
                    _BuiltTxnSpec(
                        txn=self._sanitize_transaction(spec.txn),
                        signer=resolved_signer,
                        logical_max_fee=spec.logical_max_fee,
                        method=spec.method,
                    )
                )
                if spec.method:
                    method_calls[index] = spec.method

        return built_entries, method_calls

    def _ensure_built(self) -> None:
        if self._transactions_with_signers is not None:
            return

        suggested_params = self._get_suggested_params()
        genesis_id = getattr(suggested_params, "genesis_id", None)
        if genesis_id is None:
            genesis_id = getattr(suggested_params, "gen", "")
        is_localnet = ClientManager.genesis_id_is_localnet(genesis_id or "")

        built_entries, method_calls = self._build_txn_specs(suggested_params, is_localnet=is_localnet)
        transactions = [entry.txn for entry in built_entries]
        self._raw_built_transactions = list(transactions)
        logical_max_fees = [entry.logical_max_fee for entry in built_entries]

        needs_analysis = (
            self._config.cover_app_call_inner_transaction_fees or self._config.populate_app_call_resources
        ) and any(txn.transaction_type == TransactionType.AppCall for txn in transactions)
        if needs_analysis:
            group_analysis = self._analyze_group_requirements(
                transactions,
                logical_max_fees,
                suggested_params,
                self._config,
            )
            self._populate_transaction_and_group_resources(transactions, group_analysis, logical_max_fees)

        grouped = group_transactions(transactions)
        self._transactions_with_signers = [
            TransactionWithSigner(
                txn=grouped[index],
                signer=cast(TransactionSigner, entry.signer),
                method=method_calls.get(index),
            )
            for index, entry in enumerate(built_entries)
        ]

    def _build_transactions_for_simulation(self) -> list[TransactionWithSigner]:
        if self._transactions_with_signers is None:
            suggested_params = self._get_suggested_params()
            genesis_id = getattr(suggested_params, "genesis_id", None)
            if genesis_id is None:
                genesis_id = getattr(suggested_params, "gen", "")
            is_localnet = ClientManager.genesis_id_is_localnet(genesis_id or "")

            built_entries, method_calls = self._build_txn_specs(suggested_params, is_localnet=is_localnet)
            transactions = [entry.txn for entry in built_entries]
            if len(transactions) > 1:
                transactions = group_transactions(transactions)
            return [
                TransactionWithSigner(
                    txn=transactions[index],
                    signer=cast(TransactionSigner, entry.signer),
                    method=method_calls.get(index),
                )
                for index, entry in enumerate(built_entries)
            ]

        return self._transactions_with_signers

    def _analyze_group_requirements(  # noqa: C901, PLR0912
        self,
        transactions: list[Transaction],
        logical_max_fees: Sequence[AlgoAmount | None],
        suggested_params: algod_models.SuggestedParams,
        config: TransactionComposerConfig,
    ) -> _GroupAnalysis:
        app_call_indexes_without_max_fees: list[int] = []
        transactions_to_simulate: list[Transaction] = []
        for index, txn in enumerate(transactions):
            txn_to_simulate = replace(txn, group=None)
            if config.cover_app_call_inner_transaction_fees and txn.transaction_type == TransactionType.AppCall:
                logical_max_fee = logical_max_fees[index]
                if logical_max_fee is None:
                    app_call_indexes_without_max_fees.append(index)
                else:
                    txn_to_simulate = replace(txn_to_simulate, fee=logical_max_fee.micro_algo)
            transactions_to_simulate.append(txn_to_simulate)

        if config.cover_app_call_inner_transaction_fees and app_call_indexes_without_max_fees:
            indexes = ", ".join(str(index) for index in app_call_indexes_without_max_fees)
            raise ValueError(
                "Please provide a `max_fee` for each app call transaction when "
                "cover_app_call_inner_transaction_fees is enabled. "
                f"Required for transaction {indexes}"
            )

        if len(transactions_to_simulate) > 1:
            transactions_to_simulate = group_transactions(transactions_to_simulate)

        empty_signer: TransactionSigner = make_empty_transaction_signer()
        encoded_signed_transactions = self._sign_transactions(
            [TransactionWithSigner(txn=txn, signer=empty_signer) for txn in transactions_to_simulate]
        )
        signed_transactions = decode_signed_transactions(encoded_signed_transactions)

        simulate_request = algod_models.SimulateRequest(
            txn_groups=[algod_models.SimulateRequestTransactionGroup(txns=signed_transactions)],
            allow_unnamed_resources=True,
            allow_empty_signatures=True,
            fix_signers=True,
            allow_more_logging=True,
            exec_trace_config=algod_models.SimulateTraceConfig(
                enable=True,
                scratch_change=True,
                stack_change=True,
                state_change=True,
            ),
        )

        response = self._algod.simulate_transactions(simulate_request)
        group_response = response.txn_groups[0]

        if group_response.failure_message:
            if config.cover_app_call_inner_transaction_fees and "fee too small" in group_response.failure_message:
                raise ValueError(
                    "Fees were too small to resolve execution info via simulate. "
                    "You may need to increase an app call transaction maxFee."
                )
            raise ValueError(
                "Error resolving execution info via simulate in transaction "
                f"{group_response.failed_at or []}: {group_response.failure_message}"
            )

        txn_analysis_results: list[_TransactionAnalysis] = []
        for index, simulate_txn_result in enumerate(group_response.txn_results):
            txn = transactions[index]
            required_fee_delta: FeeDelta | None = None
            if config.cover_app_call_inner_transaction_fees:
                min_txn_fee = calculate_fee(txn, fee_per_byte=suggested_params.fee, min_fee=suggested_params.min_fee)
                txn_fee = txn.fee or 0
                txn_fee_delta = FeeDelta.from_int(min_txn_fee - txn_fee)
                if txn.transaction_type == TransactionType.AppCall:
                    inner_delta = calculate_inner_fee_delta(
                        simulate_txn_result.txn_result.inner_txns, suggested_params.min_fee
                    )
                    required_fee_delta = FeeDelta.add(inner_delta, txn_fee_delta)
                else:
                    required_fee_delta = txn_fee_delta

            unnamed_resources = (
                simulate_txn_result.unnamed_resources_accessed if config.populate_app_call_resources else None
            )
            txn_analysis_results.append(
                _TransactionAnalysis(
                    required_fee_delta=required_fee_delta,
                    unnamed_resources_accessed=unnamed_resources,
                )
            )

        group_resources = group_response.unnamed_resources_accessed if config.populate_app_call_resources else None
        if group_resources:
            group_resources.accounts = sorted(group_resources.accounts or [])
            group_resources.assets = sorted(group_resources.assets or [])
            group_resources.apps = sorted(group_resources.apps or [])
            group_resources.boxes = sorted(
                group_resources.boxes or [],
                key=lambda box: (box.app_id, box.name),
            )
            group_resources.app_locals = sorted(
                group_resources.app_locals or [],
                key=lambda entry: (entry.app_id, entry.address),
            )
            group_resources.asset_holdings = sorted(
                group_resources.asset_holdings or [],
                key=lambda entry: (entry.asset_id, entry.address),
            )

        return _GroupAnalysis(transactions=txn_analysis_results, unnamed_resources_accessed=group_resources)

    def _populate_transaction_and_group_resources(  # noqa: C901, PLR0912, PLR0915
        self,
        transactions: list[Transaction],
        group_analysis: _GroupAnalysis,
        logical_max_fees: Sequence[AlgoAmount | None],
    ) -> None:
        if not group_analysis:
            return

        surplus_group_fees = 0
        transaction_analysis_list: list[dict[str, Any]] = []

        for group_index, txn_analysis in enumerate(group_analysis.transactions):
            fee_delta = txn_analysis.required_fee_delta
            if fee_delta and FeeDelta.is_surplus(fee_delta):
                surplus_group_fees += FeeDelta.amount(fee_delta)

            txn = transactions[group_index]
            max_fee_source = logical_max_fees[group_index]
            max_fee_amount: int | None
            if max_fee_source is not None:
                max_fee_amount = max_fee_source.micro_algo
            elif not self._config.cover_app_call_inner_transaction_fees:
                txn_fee = txn.fee or 0
                max_fee_amount = txn_fee if txn_fee > 0 else None
            else:
                max_fee_amount = None
            is_immutable_fee = max_fee_amount is not None and max_fee_amount == (txn.fee or 0)

            priority = FeePriority.Covered
            if fee_delta and FeeDelta.is_deficit(fee_delta):
                deficit_amount = FeeDelta.amount(fee_delta)
                if is_immutable_fee or txn.transaction_type != TransactionType.AppCall:
                    priority = FeePriority.ImmutableDeficit(deficit_amount)
                else:
                    priority = FeePriority.ModifiableDeficit(deficit_amount)

            transaction_analysis_list.append(
                {
                    "group_index": group_index,
                    "required_fee_delta": fee_delta,
                    "priority": priority,
                    "unnamed_resources_accessed": txn_analysis.unnamed_resources_accessed,
                    "logical_max_fee": max_fee_amount,
                }
            )

        transaction_analysis_list.sort(key=lambda item: item["priority"], reverse=True)
        indexes_with_access_references: list[int] = []

        for item in transaction_analysis_list:
            group_index = item["group_index"]
            logical_max_fee = item["logical_max_fee"]
            required_fee_delta: FeeDelta | None = item["required_fee_delta"]
            unnamed_resources_accessed = item["unnamed_resources_accessed"]

            if required_fee_delta and FeeDelta.is_deficit(required_fee_delta):
                deficit_amount = FeeDelta.amount(required_fee_delta)
                additional_fee_delta: FeeDelta | None

                if surplus_group_fees == 0:
                    additional_fee_delta = required_fee_delta
                elif surplus_group_fees >= deficit_amount:
                    surplus_group_fees -= deficit_amount
                    additional_fee_delta = None
                else:
                    additional_fee_delta = FeeDelta.from_int(deficit_amount - surplus_group_fees)
                    surplus_group_fees = 0

                if additional_fee_delta and FeeDelta.is_deficit(additional_fee_delta):
                    additional_deficit_amount = FeeDelta.amount(additional_fee_delta)
                    txn = transactions[group_index]

                    if txn.transaction_type != TransactionType.AppCall:
                        raise ValueError(
                            "An additional fee of "
                            f"{additional_deficit_amount} µALGO is required for non app call transaction {group_index}",
                        )

                    current_fee = txn.fee or 0
                    transaction_fee = current_fee + additional_deficit_amount
                    if logical_max_fee is not None and transaction_fee > logical_max_fee:
                        raise ValueError(
                            "Calculated transaction fee "
                            f"{transaction_fee} µALGO is greater than max of {logical_max_fee} "
                            f"for transaction {group_index}"
                        )

                    transactions[group_index] = replace(txn, fee=transaction_fee)

            if unnamed_resources_accessed and transactions[group_index].transaction_type == TransactionType.AppCall:
                has_access_references = bool(transactions[group_index].application_call.access_references)
                if not has_access_references:
                    transactions[group_index] = populate_transaction_resources(
                        transactions[group_index], unnamed_resources_accessed, group_index
                    )
                else:
                    indexes_with_access_references.append(group_index)

        if indexes_with_access_references:
            config.logger.warning(
                "Resource population will be skipped for transaction indexes %s as they use access references.",
                indexes_with_access_references,
            )

        if group_analysis.unnamed_resources_accessed:
            populate_group_resources(transactions, group_analysis.unnamed_resources_accessed)

    def _build_txn_from_params(  # noqa: C901, PLR0911, PLR0912, PLR0915
        self,
        params: TxnParams,
        suggested_params: algod_models.SuggestedParams,
        *,
        is_localnet: bool,
    ) -> list[_BuiltTxnSpec]:
        builder_kwargs: _BuilderKwargs = {
            "suggested_params": suggested_params,
            "default_validity_window": self._default_validity_window,
            "default_validity_window_is_explicit": self._default_validity_window_is_explicit,
            "is_localnet": is_localnet,
        }

        if isinstance(params, PaymentParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_payment_transaction(params, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, AssetCreateParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_asset_create_transaction(params, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, AssetConfigParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_asset_config_transaction(params, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, AssetFreezeParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_asset_freeze_transaction(params, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, AssetDestroyParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_asset_destroy_transaction(params, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, AssetTransferParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_asset_transfer_transaction(params, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, AssetOptInParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_asset_opt_in_transaction(params, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, AssetOptOutParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_asset_opt_out_transaction(params, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, AppCreateParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_app_create_transaction(params, app_manager=self._app_manager, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, AppUpdateParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_app_update_transaction(params, app_manager=self._app_manager, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, AppDeleteParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_app_delete_transaction(params, app_manager=self._app_manager, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, AppCallParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_app_call_transaction(params, app_manager=self._app_manager, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, OnlineKeyRegistrationParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_online_key_registration_transaction(params, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, OfflineKeyRegistrationParams):
            signer = self._resolve_param_signer(params.signer, params.sender)
            built = build_offline_key_registration_transaction(params, **builder_kwargs)
            return [
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=signer,
                    logical_max_fee=built.logical_max_fee,
                )
            ]
        elif isinstance(params, MethodCallTxnParamTypes):
            extra_specs, flattened_params = self._extract_method_call_transactions(
                params, suggested_params, is_localnet=is_localnet
            )
            if isinstance(params, AppCreateMethodCallParams):
                create_params = cast(AppCreateMethodCallParams, flattened_params)
                built = build_app_create_method_call_transaction(
                    create_params,
                    suggested_params=suggested_params,
                    method_args=create_params.args,
                    app_manager=self._app_manager,
                    default_validity_window=self._default_validity_window,
                    default_validity_window_is_explicit=self._default_validity_window_is_explicit,
                    is_localnet=is_localnet,
                )
                return [
                    *extra_specs,
                    _BuiltTxnSpec(
                        txn=built.txn,
                        signer=self._resolve_param_signer(create_params.signer, create_params.sender),
                        logical_max_fee=built.logical_max_fee,
                        method=create_params.method,
                    ),
                ]
            if isinstance(params, AppUpdateMethodCallParams):
                update_params = cast(AppUpdateMethodCallParams, flattened_params)
                built = build_app_update_method_call_transaction(
                    update_params,
                    suggested_params=suggested_params,
                    method_args=update_params.args,
                    app_manager=self._app_manager,
                    default_validity_window=self._default_validity_window,
                    default_validity_window_is_explicit=self._default_validity_window_is_explicit,
                    is_localnet=is_localnet,
                )
                return [
                    *extra_specs,
                    _BuiltTxnSpec(
                        txn=built.txn,
                        signer=self._resolve_param_signer(update_params.signer, update_params.sender),
                        logical_max_fee=built.logical_max_fee,
                        method=update_params.method,
                    ),
                ]
            if isinstance(params, AppDeleteMethodCallParams):
                delete_params = cast(AppDeleteMethodCallParams, flattened_params)
                built = build_app_delete_method_call_transaction(
                    delete_params,
                    suggested_params=suggested_params,
                    method_args=delete_params.args,
                    app_manager=self._app_manager,
                    default_validity_window=self._default_validity_window,
                    default_validity_window_is_explicit=self._default_validity_window_is_explicit,
                    is_localnet=is_localnet,
                )
                return [
                    *extra_specs,
                    _BuiltTxnSpec(
                        txn=built.txn,
                        signer=self._resolve_param_signer(delete_params.signer, delete_params.sender),
                        logical_max_fee=built.logical_max_fee,
                        method=delete_params.method,
                    ),
                ]

            call_params = cast(AppCallMethodCallParams, flattened_params)
            built = build_app_call_method_call_transaction(
                call_params,
                suggested_params=suggested_params,
                method_args=call_params.args,
                app_manager=self._app_manager,
                default_validity_window=self._default_validity_window,
                default_validity_window_is_explicit=self._default_validity_window_is_explicit,
                is_localnet=is_localnet,
            )

            return [
                *extra_specs,
                _BuiltTxnSpec(
                    txn=built.txn,
                    signer=self._resolve_param_signer(call_params.signer, call_params.sender),
                    logical_max_fee=built.logical_max_fee,
                    method=call_params.method,
                ),
            ]

        raise ValueError(f"Unsupported transaction params type: {type(params)}")

    def _clone_entry(self, entry: _QueuedTransaction) -> _QueuedTransaction:
        if isinstance(entry.txn, Transaction):
            return _QueuedTransaction(txn=self._sanitize_transaction(entry.txn), signer=entry.signer)
        # TxnParams are immutable (frozen dataclasses) so we can share them
        return _QueuedTransaction(txn=entry.txn, signer=entry.signer)

    def _process_method_call_arg(
        self,
        arg: object | None,
        current_signer: TransactionSigner | None,
        suggested_params: algod_models.SuggestedParams,
        *,
        is_localnet: bool,
    ) -> tuple[list[_BuiltTxnSpec], object | None]:
        if arg is None:
            return [], None

        if isinstance(arg, TransactionWithSigner):
            return [
                _BuiltTxnSpec(
                    txn=self._sanitize_transaction(arg.txn),
                    signer=arg.signer,
                    logical_max_fee=None,
                )
            ], None

        if isinstance(arg, MethodCallTxnParamTypes):
            nested_params = arg
            if arg.signer is None and current_signer is not None:
                nested_params = replace(arg, signer=current_signer)
            return (
                self._build_txn_from_params(
                    nested_params,
                    suggested_params,
                    is_localnet=is_localnet,
                ),
                None,
            )

        if isinstance(arg, Transaction):
            return [
                _BuiltTxnSpec(
                    txn=self._sanitize_transaction(arg),
                    signer=current_signer,
                    logical_max_fee=None,
                )
            ], None

        if isinstance(arg, TxnParamTypes):
            return (
                self._build_txn_from_params(arg, suggested_params, is_localnet=is_localnet),
                None,
            )

        return [], arg

    def _extract_method_call_transactions(
        self,
        params: MethodCallTxnParamTypes,
        suggested_params: algod_models.SuggestedParams,
        *,
        is_localnet: bool,
    ) -> tuple[list[_BuiltTxnSpec], MethodCallTxnParamTypes]:
        """Flatten transaction arguments inside ABI method calls into queued specs."""
        if not params.args:
            return [], params

        def _to_signer(value: TransactionSigner | AddressWithTransactionSigner | None) -> TransactionSigner | None:
            if isinstance(value, AddressWithTransactionSigner):
                return value.signer
            return value

        current_signer = _to_signer(params.signer)
        extra_specs: list[_BuiltTxnSpec] = []
        processed_args: list[Any] = []

        for arg in params.args:
            specs, processed = self._process_method_call_arg(
                arg,
                current_signer,
                suggested_params,
                is_localnet=is_localnet,
            )
            extra_specs.extend(specs)
            processed_args.append(processed)

        return extra_specs, replace(params, args=processed_args)

    def _sanitize_transaction(self, txn: Transaction) -> Transaction:
        return replace(txn, group=None)

    def _resolve_param_signer(
        self,
        signer: TransactionSigner | AddressWithTransactionSigner | None,
        sender: str | None = None,
    ) -> TransactionSigner:
        if isinstance(signer, AddressWithTransactionSigner):
            return signer.signer
        if signer is None:
            if sender is None:
                raise ValueError("Sender is required to resolve signer")
            resolved = self._get_signer(sender)
            if resolved is None:
                raise ValueError(f"No signer found for address {sender}")
            return resolved
        return signer

    def _sign_transactions(self, txns_with_signers: Sequence[TransactionWithSigner]) -> list[bytes]:
        if not txns_with_signers:
            raise ValueError("No transactions available to sign")

        transactions = [entry.txn for entry in txns_with_signers]
        signer_groups: dict[int, tuple[TransactionSigner, list[int]]] = {}
        for index, entry in enumerate(txns_with_signers):
            key = id(entry.signer)
            if key not in signer_groups:
                signer_groups[key] = (entry.signer, [])
            signer_groups[key][1].append(index)

        signed_blobs: dict[int, list[bytes]] = {}
        for key, (signer, indexes) in signer_groups.items():
            blobs = signer(transactions, indexes)
            signed_blobs[key] = list(blobs)

        encoded_signed_transactions: list[bytes | None] = [None] * len(transactions)

        for key, (_, indexes) in signer_groups.items():
            blobs = signed_blobs[key]
            for blob_index, txn_index in enumerate(indexes):
                if blob_index < len(blobs):
                    encoded_signed_transactions[txn_index] = blobs[blob_index]

        unsigned_indexes = [i for i, item in enumerate(encoded_signed_transactions) if item is None]
        if unsigned_indexes:
            raise ValueError(f"Transactions at indexes [{', '.join(map(str, unsigned_indexes))}] were not signed")

        return cast(list[bytes], encoded_signed_transactions)  # The guard above ensures no None values

    def _group_id(self) -> str | None:
        txns = self._transactions_with_signers or []
        if not txns:
            return None
        group = txns[0].txn.group
        if group is None:
            return None
        return base64.b64encode(group).decode()

    def _wait_for_confirmations(
        self, tx_ids: Sequence[str], params: SendParams
    ) -> list[algod_models.PendingTransactionResponse]:
        confirmations: list[algod_models.PendingTransactionResponse] = []
        max_rounds = params.get("max_rounds_to_wait")

        if max_rounds is None:
            suggested = self._get_suggested_params()
            first = int(getattr(suggested, "first_valid", getattr(suggested, "first", 0)))
            last = max(entry.txn.last_valid for entry in self._transactions_with_signers or [])
            max_rounds = int(max(last - first + 1, 0))
        for tx_id in tx_ids:
            confirmations.append(_wait_for_confirmation(self._algod, tx_id, max_rounds))
        return confirmations

    def _transform_error(self, err: Exception) -> Exception:
        original_error = err
        transformed = err
        for transformer in self._error_transformers:
            try:
                transformed = transformer(transformed)
            except Exception as transformer_error:
                raise ErrorTransformerError("Error transformer raised an exception") from transformer_error
            if not isinstance(transformed, Exception):
                raise InvalidErrorTransformerValueError(original_error, transformed)
        return transformed

    def _parse_abi_return_values(
        self,
        confirmations: Sequence[algod_models.PendingTransactionResponse],
        method_calls: dict[int, ABIMethod] | None = None,
    ) -> list[ABIReturn]:
        abi_returns: list[ABIReturn] = []
        method_calls = method_calls or {
            index: entry.method for index, entry in enumerate(self._transactions_with_signers or []) if entry.method
        }
        for index, confirmation in enumerate(confirmations):
            method = method_calls.get(index)
            if not method:
                continue
            abi_return = self._app_manager.get_abi_return(confirmation, method)
            if abi_return is not None:
                abi_returns.append(abi_return)
        return abi_returns

    def _resolve_error_transactions(self) -> list[Transaction] | None:
        if self._transactions_with_signers is not None:
            return [entry.txn for entry in self._transactions_with_signers]
        if self._raw_built_transactions:
            transactions = list(self._raw_built_transactions)
            return group_transactions(transactions) if len(transactions) > 1 else transactions
        return None

    def _simulate_error_context(
        self,
        sent_transactions: Sequence[Transaction],
        *,
        suppress_log: bool | None,
    ) -> tuple[algod_models.SimulateResponse | None, list[SimulateTransactionResult]]:
        """Simulate transactions to get error context including traces.

        Returns:
            A tuple of (simulate_response, traces).
        """
        try:
            empty_signer: TransactionSigner = make_empty_transaction_signer()
            encoded_signed_transactions = self._sign_transactions(
                [TransactionWithSigner(txn=txn, signer=empty_signer) for txn in sent_transactions]
            )
            signed_transactions = decode_signed_transactions(encoded_signed_transactions)
            request = algod_models.SimulateRequest(
                txn_groups=[algod_models.SimulateRequestTransactionGroup(txns=signed_transactions)],
                allow_empty_signatures=True,
                fix_signers=True,
                allow_more_logging=True,
                exec_trace_config=algod_models.SimulateTraceConfig(
                    enable=True,
                    scratch_change=True,
                    stack_change=True,
                    state_change=True,
                ),
            )
            response = self._algod.simulate_transactions(request)

            # Extract traces from the response - use SimulateTransactionResult directly
            # aligned with TypeScript which uses algod client types directly
            traces: list[SimulateTransactionResult] = []
            if response.txn_groups and response.txn_groups[0].failed_at:
                traces = list(response.txn_groups[0].txn_results)

            return response, traces
        except Exception:
            config.logger.debug(
                "Failed to simulate transaction group after send error",
                exc_info=True,
                extra={"suppress_log": suppress_log},
            )
            return None, []

    def _create_composer_error(
        self,
        err: Exception,
        sent_transactions: Sequence[Transaction] | None,
        simulate_response: algod_models.SimulateResponse | None,
        traces: list[SimulateTransactionResult],
    ) -> TransactionComposerError:
        """Create a TransactionComposerError with full context."""
        return TransactionComposerError(
            str(err),
            cause=err,
            traces=traces if traces else None,
            sent_transactions=list(sent_transactions) if sent_transactions else None,
            simulate_response=simulate_response,
        )

    def set_max_fees(self, max_fees: dict[int, AlgoAmount]) -> "TransactionComposer":
        """Override max_fee for queued transactions by index before building."""
        if self._transactions_with_signers is not None:
            raise RuntimeError("Transactions have already been built")

        for index in max_fees:
            if index < 0 or index >= len(self._queued):
                raise ValueError(
                    f"Index {index} is out of range. The composer only contains {len(self._queued)} transactions"
                )

        for index, max_fee in max_fees.items():
            entry = self._queued[index]
            if isinstance(entry.txn, Transaction):
                self._queued[index] = replace(entry, max_fee=max_fee)
            elif hasattr(entry.txn, "max_fee"):
                self._queued[index] = replace(entry, txn=replace(entry.txn, max_fee=max_fee))
            else:
                raise ValueError(f"Transaction at index {index} does not support max_fee overrides")

        return self

    def _interpret_error(self, err: Exception) -> Exception:
        if isinstance(err, UnexpectedStatusError):
            payload_message = self._extract_algod_error_message(err.payload)
            if payload_message:
                return RuntimeError(payload_message)
        return err

    @staticmethod
    def _extract_algod_error_message(payload: object) -> str | None:  # noqa: PLR0911
        if payload is None:
            return None
        if isinstance(payload, bytes):
            text = payload.decode("utf-8", errors="ignore")
        else:
            text = str(payload)
        text = text.strip()
        if not text:
            return None
        try:
            decoded = json.loads(text)
        except Exception:
            return text
        if isinstance(decoded, dict):
            for key in ("message", "msg", "error", "detail", "description"):
                value = decoded.get(key)
                if isinstance(value, str) and value.strip():
                    return value
            return text
        if isinstance(decoded, list) and decoded:
            first = decoded[0]
            if isinstance(first, str) and first.strip():
                return first
        return text


def _wait_for_confirmation(
    algod: AlgodClient,
    tx_id: str,
    max_rounds: int,
) -> algod_models.PendingTransactionResponse:
    remaining = max_rounds
    status = algod.status()
    current_round = getattr(status, "last_round", 0)
    while remaining > 0:
        pending = algod.pending_transaction_information(tx_id)
        confirmed_round = getattr(pending, "confirmed_round", None)
        if confirmed_round is not None and confirmed_round > 0:
            return pending
        current_round += 1
        algod.status_after_block(current_round)
        remaining -= 1
    raise TimeoutError(f"Transaction {tx_id} not confirmed after {max_rounds} rounds")
