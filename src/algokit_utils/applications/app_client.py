from __future__ import annotations

import base64
import copy
import json
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

import algosdk
from algosdk.transaction import OnComplete, Transaction

from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.applications.app_manager import BoxABIValue, BoxName, BoxValue
from algokit_utils.applications.utils import (
    get_abi_decoded_value,
    get_abi_encoded_value,
    get_abi_tuple_from_abi_struct,
    get_arc56_method,
)
from algokit_utils.errors.logic_error import LogicError, parse_logic_error
from algokit_utils.models.application import (
    AppState,
    Arc56Contract,
    CompiledTeal,
    ProgramSourceInfo,
    SourceInfoDetail,
    StorageKey,
    StorageMap,
)
from algokit_utils.models.transaction import SendParams
from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCall,
    AppCallParams,
    AppDeleteMethodCall,
    AppMethodCallTransactionArgument,
    AppUpdateMethodCall,
    AppUpdateParams,
    BuiltTransactions,
    PaymentParams,
)
from algokit_utils.transactions.transaction_sender import SendAppTransactionResult, SendSingleTransactionResult

if TYPE_CHECKING:
    from collections.abc import Callable

    from algosdk.atomic_transaction_composer import TransactionSigner
    from algosdk.source_map import SourceMap

    from algokit_utils.applications.app_manager import (
        AppManager,
        BoxIdentifier,
        BoxReference,
        TealTemplateParams,
    )
    from algokit_utils.models.abi import ABIStruct, ABIType, ABIValue
    from algokit_utils.models.amount import AlgoAmount
    from algokit_utils.protocols.application import AlgorandClientProtocol
    from algokit_utils.transactions.transaction_composer import TransactionComposer

# TEAL opcodes for constant blocks
BYTE_CBLOCK = 0x20  # bytecblock opcode
INT_CBLOCK = 0x21  # intcblock opcode

T = TypeVar("T")  # For generic return type in _handle_call_errors


def get_constant_block_offset(program: bytes) -> int:  # noqa: C901
    """Calculate the offset after constant blocks in TEAL program.

    Args:
        program: The compiled TEAL program bytes

    Returns:
        The maximum offset after bytecblock/intcblock operations
    """
    bytes_list = list(program)
    program_size = len(bytes_list)

    # Remove version byte
    bytes_list.pop(0)

    # Track offsets
    bytecblock_offset: int | None = None
    intcblock_offset: int | None = None

    while bytes_list:
        # Get current byte
        byte = bytes_list.pop(0)

        # Check if byte is a constant block opcode
        if byte in (BYTE_CBLOCK, INT_CBLOCK):
            is_bytecblock = byte == BYTE_CBLOCK

            # Get number of values in constant block
            if not bytes_list:
                break
            values_remaining = bytes_list.pop(0)

            # Process each value in the block
            for _ in range(values_remaining):
                if is_bytecblock:
                    # For bytecblock, next byte is length of element
                    if not bytes_list:
                        break
                    length = bytes_list.pop(0)
                    # Remove the bytes for this element
                    bytes_list = bytes_list[length:]
                else:
                    # For intcblock, read until we find end of uvarint (MSB not set)
                    while bytes_list:
                        byte = bytes_list.pop(0)
                        if not (byte & 0x80):  # Check if MSB is not set
                            break

            # Update appropriate offset
            if is_bytecblock:
                bytecblock_offset = program_size - len(bytes_list) - 1
            else:
                intcblock_offset = program_size - len(bytes_list) - 1

            # If next byte isn't a constant block opcode, we're done
            if not bytes_list or bytes_list[0] not in (BYTE_CBLOCK, INT_CBLOCK):
                break

    # Return maximum offset
    return max(bytecblock_offset or 0, intcblock_offset or 0)


@dataclass(frozen=True, kw_only=True)
class AppClientCompilationParams:
    deploy_time_params: TealTemplateParams | None = None
    updatable: bool | None = None
    deletable: bool | None = None


@dataclass(frozen=True, kw_only=True)
class ExposedLogicErrorDetails:
    is_clear_state_program: bool = False
    approval_source_map: SourceMap | None = None
    clear_source_map: SourceMap | None = None
    program: bytes | None = None
    approval_source_info: ProgramSourceInfo | None = None
    clear_source_info: ProgramSourceInfo | None = None


@dataclass(kw_only=True, frozen=True)
class _AppClientParamsBase:
    """Base parameters for creating an app client"""

    app_id: int
    app_spec: (
        Arc56Contract | ApplicationSpecification | str
    )  # Using string quotes since these types may be defined elsewhere
    algorand: AlgorandClientProtocol  # Using string quotes since this type may be defined elsewhere


@dataclass(kw_only=True, frozen=True)
class AppClientParams(_AppClientParamsBase):
    """Full parameters for creating an app client"""

    app_name: str | None = None
    default_sender: str | bytes | None = None  # Address can be string or bytes
    default_signer: TransactionSigner | None = None
    approval_source_map: SourceMap | None = None
    clear_source_map: SourceMap | None = None


@dataclass(frozen=True, kw_only=True)
class AppClientCompilationResult:
    approval_program: bytes
    clear_state_program: bytes
    compiled_approval: CompiledTeal | None = None
    compiled_clear: CompiledTeal | None = None


@dataclass(frozen=True, kw_only=True)
class CommonTxnParams:
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
class FundAppAccountParams:
    sender: str | None = None
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
    amount: AlgoAmount
    close_remainder_to: str | None = None
    max_rounds_to_wait: int | None = None
    suppress_log: bool | None = None
    populate_app_call_resources: bool | None = None
    on_complete: algosdk.transaction.OnComplete | None = None


@dataclass(kw_only=True, frozen=True)
class AppClientCallParams:
    method: str | None = None  # If calling ABI method, name or signature
    args: list | None = None  # Arguments to pass to the method
    boxes: list | None = None  # Box references to load
    accounts: list[str] | None = None  # Account addresses to load
    apps: list[int] | None = None  # App IDs to load
    assets: list[int] | None = None  # Asset IDs to load
    lease: (str | bytes) | None = None  # Optional lease
    sender: str | None = None  # Optional sender account
    note: (bytes | dict | str) | None = None  # Transaction note
    send_params: dict | None = None  # Parameters to control transaction sending


@dataclass(frozen=True, kw_only=True)
class AppClientMethodCallParams:
    method: str
    args: list[ABIValue | ABIStruct | AppMethodCallTransactionArgument | None] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None
    extra_fee: AlgoAmount | None = None
    first_valid_round: int | None = None
    lease: bytes | None = None
    max_fee: AlgoAmount | None = None
    note: bytes | None = None
    rekey_to: str | None = None
    sender: str | None = None
    signer: TransactionSigner | None = None
    static_fee: AlgoAmount | None = None
    validity_window: int | None = None
    last_valid_round: int | None = None
    on_complete: algosdk.transaction.OnComplete | None = None


@dataclass(frozen=True, kw_only=True)
class AppClientMethodCallWithCompilationParams(AppClientMethodCallParams, AppClientCompilationParams):
    """Combined parameters for method calls with compilation"""


@dataclass(frozen=True, kw_only=True)
class AppClientMethodCallWithSendParams(AppClientMethodCallParams, SendParams):
    """Combined parameters for method calls with send options"""


@dataclass(frozen=True, kw_only=True)
class AppClientMethodCallWithCompilationAndSendParams(
    AppClientMethodCallParams, AppClientCompilationParams, SendParams
):
    """Combined parameters for method calls with compilation and send options"""


@dataclass(frozen=True, kw_only=True)
class AppClientBareCallParams:
    signer: TransactionSigner | None
    rekey_to: str | None
    lease: bytes | None
    static_fee: AlgoAmount | None
    extra_fee: AlgoAmount | None
    max_fee: AlgoAmount | None
    validity_window: int | None
    first_valid_round: int | None
    last_valid_round: int | None
    sender: str | None
    note: bytes | None
    args: list[bytes] | None
    account_references: list[str] | None
    app_references: list[int] | None
    asset_references: list[int] | None
    box_references: list[BoxReference | BoxIdentifier] | None


@dataclass(frozen=True, kw_only=True)
class CallOnComplete:
    on_complete: algosdk.transaction.OnComplete


@dataclass(frozen=True, kw_only=True)
class AppClientBareCallWithCompilationParams(AppClientBareCallParams, AppClientCompilationParams):
    """Combined parameters for bare calls with compilation"""


@dataclass(frozen=True, kw_only=True)
class AppClientBareCallWithSendParams(AppClientBareCallParams, SendParams):
    """Combined parameters for bare calls with send options"""


@dataclass(frozen=True, kw_only=True)
class AppClientBareCallWithCompilationAndSendParams(AppClientBareCallParams, AppClientCompilationParams, SendParams):
    """Combined parameters for bare calls with compilation and send options"""


@dataclass(frozen=True, kw_only=True)
class AppClientBareCallWithCallOnCompleteParams(AppClientBareCallParams, CallOnComplete):
    """Combined parameters for bare calls with an OnComplete value"""


@dataclass(frozen=True, kw_only=True)
class ResolveAppClientByNetwork:
    app_spec: Arc56Contract | ApplicationSpecification | str
    algorand: AlgorandClientProtocol
    app_name: str | None = None
    default_sender: str | bytes | None = None
    default_signer: TransactionSigner | None = None
    approval_source_map: SourceMap | None = None
    clear_source_map: SourceMap | None = None


@dataclass(frozen=True, kw_only=True)
class AppSourceMaps:
    approval_source_map: SourceMap | None = None
    clear_source_map: SourceMap | None = None


class _AppClientStateMethodsProtocol(Protocol):
    def get_all(self) -> dict[str, Any]: ...

    def get_value(self, name: str, app_state: dict[str, AppState] | None = None) -> ABIValue | None: ...

    def get_map_value(self, map_name: str, key: bytes | Any, app_state: dict[str, AppState] | None = None) -> Any: ...  # noqa: ANN401

    def get_map(self, map_name: str) -> dict[str, ABIValue]: ...


class _AppClientStateMethods(_AppClientStateMethodsProtocol):
    def __init__(
        self,
        *,
        get_all: Callable[[], dict[str, Any]],
        get_value: Callable[[str, dict[str, AppState] | None], ABIValue | None],
        get_map_value: Callable[[str, bytes | Any, dict[str, AppState] | None], Any],
        get_map: Callable[[str], dict[str, ABIValue]],
    ) -> None:
        self._get_all = get_all
        self._get_value = get_value
        self._get_map_value = get_map_value
        self._get_map = get_map

    def get_all(self) -> dict[str, Any]:
        return self._get_all()

    def get_value(self, name: str, app_state: dict[str, AppState] | None = None) -> ABIValue | None:
        return self._get_value(name, app_state)

    def get_map_value(self, map_name: str, key: bytes | Any, app_state: dict[str, AppState] | None = None) -> Any:  # noqa: ANN401
        return self._get_map_value(map_name, key, app_state)

    def get_map(self, map_name: str) -> dict[str, ABIValue]:
        return self._get_map(map_name)


class _AppClientStateAccessor:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec

    def local_state(self, address: str) -> _AppClientStateMethodsProtocol:
        """Methods to access local state for the current app for a given address"""
        return self._get_state_methods(
            state_getter=lambda: self._algorand.app.get_local_state(self._app_id, address),
            key_getter=lambda: self._app_spec.state.keys.get("local", {}),
            map_getter=lambda: self._app_spec.state.maps.get("local", {}),
        )

    @property
    def global_state(self) -> _AppClientStateMethodsProtocol:
        """Methods to access global state for the current app"""
        return self._get_state_methods(
            state_getter=lambda: self._algorand.app.get_global_state(self._app_id),
            key_getter=lambda: self._app_spec.state.keys.get("global", {}),
            map_getter=lambda: self._app_spec.state.maps.get("global", {}),
        )

    # @property
    # def box(self) -> AppClientStateMethods:
    #     """Methods to access box storage for the current app"""
    #     return self._get_state_methods(
    #         state_getter=lambda: self._algorand.app.get_box_state(self._app_id),
    #         key_getter=lambda: self._app_spec.state.keys.get("box", {}),
    #         map_getter=lambda: self._app_spec.state.maps.get("box", {}),
    #     )

    def _get_state_methods(  # noqa: C901
        self,
        state_getter: Callable[[], dict[str, AppState]],
        key_getter: Callable[[], dict[str, StorageKey]],
        map_getter: Callable[[], dict[str, StorageMap]],
    ) -> _AppClientStateMethodsProtocol:
        def get_all() -> dict[str, Any]:
            state = state_getter()
            keys = key_getter()
            return {key: get_value(key, state) for key in keys}

        def get_value(name: str, app_state: dict[str, AppState] | None = None) -> ABIValue | None:
            state = app_state or state_getter()
            key_info = key_getter()[name]
            value = next((s for s in state.values() if s.key_base64 == key_info.key), None)

            if value and value.value_raw:
                return get_abi_decoded_value(value.value_raw, key_info.value_type, self._app_spec.structs)

            return None

        def get_map_value(map_name: str, key: bytes | Any, app_state: dict[str, AppState] | None = None) -> Any:  # noqa: ANN401
            state = app_state or state_getter()
            metadata = map_getter()[map_name]

            prefix = bytes(metadata.prefix or "", "base64")
            encoded_key = get_abi_encoded_value(key, metadata.key_type, self._app_spec.structs)
            full_key = base64.b64encode(prefix + encoded_key).decode("utf-8")
            value = next((s for s in state.values() if s.key_base64 == full_key), None)
            if value and value.value_raw:
                return get_abi_decoded_value(value.value_raw, metadata.value_type, self._app_spec.structs)
            return None

        def get_map(map_name: str) -> dict[str, ABIValue]:
            state = state_getter()
            metadata = map_getter()[map_name]

            prefix = metadata.prefix or ""

            prefixed_state = {k: v for k, v in state.items() if k.startswith(prefix)}

            decoded_map = {}

            for key_encoded, value in prefixed_state.items():
                key_bytes = key_encoded[len(prefix) :]
                try:
                    decoded_key = get_abi_decoded_value(key_bytes, metadata.key_type, self._app_spec.structs)
                except Exception as e:
                    raise ValueError(f"Failed to decode key {key_encoded}") from e

                try:
                    if value and value.value_raw:
                        decoded_value = get_abi_decoded_value(
                            value.value_raw, metadata.value_type, self._app_spec.structs
                        )
                    else:
                        decoded_value = get_abi_decoded_value(value.value, metadata.value_type, self._app_spec.structs)
                except Exception as e:
                    raise ValueError(f"Failed to decode value {value}") from e

                decoded_map[str(decoded_key)] = decoded_value

            return decoded_map

        return _AppClientStateMethods(
            get_all=get_all,
            get_value=get_value,
            get_map_value=get_map_value,
            get_map=get_map,
        )

    def get_local_state(self, address: str) -> dict[str, AppState]:
        return self._algorand.app.get_local_state(self._app_id, address)

    def get_global_state(self) -> dict[str, AppState]:
        return self._algorand.app.get_global_state(self._app_id)


class _AppClientBareParamsAccessor:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec

    def _get_bare_params(
        self, params: dict[str, Any] | None, on_complete: algosdk.transaction.OnComplete
    ) -> dict[str, Any]:
        """Get bare parameters for application calls.

        Args:
            params: The parameters to process
            on_complete: The OnComplete value for the transaction

        Returns:
            The processed parameters with defaults filled in
        """
        params = params or {}
        sender = self._client._get_sender(params.get("sender"))
        return {
            **params,
            "app_id": self._app_id,
            "sender": sender,
            "signer": self._client._get_signer(params.get("sender"), params.get("signer")),
            "on_complete": on_complete,
        }

    def update(self, params: AppClientBareCallWithCompilationAndSendParams | None = None) -> AppUpdateParams:
        call_params: AppUpdateParams = AppUpdateParams(
            **self._get_bare_params(params.__dict__ if params else {}, OnComplete.UpdateApplicationOC)
        )
        return call_params

    def opt_in(self, params: AppClientBareCallWithSendParams | None = None) -> AppCallParams:
        call_params: AppCallParams = AppCallParams(**self._get_bare_params(params.__dict__, OnComplete.OptInOC))
        return call_params

    def delete(self, params: AppClientBareCallWithSendParams) -> AppCallParams:
        call_params: AppCallParams = AppCallParams(
            **self._get_bare_params(params.__dict__, OnComplete.DeleteApplicationOC)
        )
        return call_params

    def clear_state(self, params: AppClientBareCallWithSendParams) -> AppCallParams:
        call_params: AppCallParams = AppCallParams(**self._get_bare_params(params.__dict__, OnComplete.ClearStateOC))
        return call_params

    def close_out(self, params: AppClientBareCallWithSendParams) -> AppCallParams:
        call_params: AppCallParams = AppCallParams(**self._get_bare_params(params.__dict__, OnComplete.CloseOutOC))
        return call_params

    def call(self, params: AppClientBareCallWithCallOnCompleteParams) -> AppCallParams:
        call_params: AppCallParams = AppCallParams(**self._get_bare_params(params.__dict__, OnComplete.NoOpOC))
        return call_params


class _AppClientMethodCallParamsAccessor:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec
        self._bare_params_accessor = _AppClientBareParamsAccessor(client)

    @property
    def bare(self) -> _AppClientBareParamsAccessor:
        return self._bare_params_accessor

    def fund_app_account(self, params: FundAppAccountParams) -> PaymentParams:
        def random_note() -> bytes:
            return base64.b64encode(os.urandom(16))

        return PaymentParams(
            sender=self._client._get_sender(params.sender),
            signer=self._client._get_signer(params.sender, params.signer),
            receiver=self._client.app_address,
            amount=params.amount,
            rekey_to=params.rekey_to,
            note=params.note or random_note(),
            lease=params.lease,
            static_fee=params.static_fee,
            extra_fee=params.extra_fee,
            max_fee=params.max_fee,
            validity_window=params.validity_window,
            first_valid_round=params.first_valid_round,
            last_valid_round=params.last_valid_round,
            close_remainder_to=params.close_remainder_to,
        )

    def opt_in(self, params: AppClientMethodCallParams) -> AppCallMethodCall:
        input_params = self._get_abi_params(params.__dict__, on_complete=algosdk.transaction.OnComplete.OptInOC)
        return AppCallMethodCall(**input_params)

    def call(self, params: AppClientMethodCallParams) -> AppCallMethodCall:
        input_params = self._get_abi_params(params.__dict__, on_complete=algosdk.transaction.OnComplete.NoOpOC)
        return AppCallMethodCall(**input_params)

    def delete(self, params: AppClientMethodCallParams) -> AppDeleteMethodCall:
        input_params = self._get_abi_params(
            params.__dict__, on_complete=algosdk.transaction.OnComplete.DeleteApplicationOC
        )
        return AppDeleteMethodCall(**input_params)

    def update(self, params: AppClientMethodCallParams) -> AppUpdateMethodCall:
        input_params = self._get_abi_params(
            params.__dict__, on_complete=algosdk.transaction.OnComplete.UpdateApplicationOC
        )
        return AppUpdateMethodCall(**input_params)

    def close_out(self, params: AppClientMethodCallParams) -> AppCallMethodCall:
        input_params = self._get_abi_params(params.__dict__, on_complete=algosdk.transaction.OnComplete.CloseOutOC)
        return AppCallMethodCall(**input_params)

    def _get_abi_params(self, params: dict[str, Any], on_complete: algosdk.transaction.OnComplete) -> dict[str, Any]:
        input_params = copy.deepcopy(params)

        input_params["app_id"] = self._app_id
        input_params["on_complete"] = on_complete

        input_params["sender"] = self._client._get_sender(params["sender"])
        input_params["signer"] = self._client._get_signer(params["sender"], params["signer"])

        if params.get("method"):
            input_params["method"] = get_arc56_method(params["method"], self._app_spec)
            if params.get("args"):
                input_params["args"] = self._client._get_abi_args_with_default_values(
                    method_name_or_signature=params["method"],
                    args=params["args"],
                    sender=self._client._get_sender(input_params["sender"]),
                )

        return input_params


class _AppClientBareCreateTransactionMethods:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand

    def update(self, params: AppClientBareCallWithCompilationAndSendParams) -> Transaction:
        return self._algorand.create_transaction.app_update(self._client.params.bare.update(params))

    def opt_in(self, params: AppClientBareCallWithSendParams) -> Transaction:
        return self._algorand.create_transaction.app_call(self._client.params.bare.opt_in(params))

    def delete(self, params: AppClientBareCallWithSendParams) -> Transaction:
        return self._algorand.create_transaction.app_call(self._client.params.bare.delete(params))

    def clear_state(self, params: AppClientBareCallWithSendParams) -> Transaction:
        return self._algorand.create_transaction.app_call(self._client.params.bare.clear_state(params))

    def close_out(self, params: AppClientBareCallWithSendParams) -> Transaction:
        return self._algorand.create_transaction.app_call(self._client.params.bare.close_out(params))

    def call(self, params: AppClientBareCallWithCallOnCompleteParams) -> Transaction:
        return self._algorand.create_transaction.app_call(self._client.params.bare.call(params))


class _AppClientMethodCallTransactionCreator:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec
        self._bare_create_transaction_methods = _AppClientBareCreateTransactionMethods(client)

    @property
    def bare(self) -> _AppClientBareCreateTransactionMethods:
        return self._bare_create_transaction_methods

    def fund_app_account(self, params: FundAppAccountParams) -> Transaction:
        return self._algorand.create_transaction.payment(self._client.params.fund_app_account(params))

    def opt_in(self, params: AppClientMethodCallParams) -> BuiltTransactions:
        return self._algorand.create_transaction.app_call_method_call(self._client.params.opt_in(params))

    def update(self, params: AppClientMethodCallParams) -> BuiltTransactions:
        return self._algorand.create_transaction.app_update_method_call(self._client.params.update(params))

    def delete(self, params: AppClientMethodCallParams) -> BuiltTransactions:
        return self._algorand.create_transaction.app_delete_method_call(self._client.params.delete(params))

    def close_out(self, params: AppClientMethodCallParams) -> BuiltTransactions:
        return self._algorand.create_transaction.app_call_method_call(self._client.params.close_out(params))

    def call(self, params: AppClientMethodCallParams) -> BuiltTransactions:
        return self._algorand.create_transaction.app_call_method_call(self._client.params.call(params))


class _AppClientBareSendAccessor:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec

    def update(
        self,
        params: AppClientBareCallWithCompilationAndSendParams,
    ) -> SendAppTransactionResult:
        """Send an application update transaction.

        Args:
            params: The parameters for the update call
            compilation: Optional compilation parameters
            max_rounds_to_wait: The maximum number of rounds to wait for confirmation
            suppress_log: Whether to suppress log output
            populate_app_call_resources: Whether to populate app call resources

        Returns:
            The result of sending the transaction
        """
        compiled = self._client.compile_and_persist_sourcemaps(
            params.deploy_time_params, params.updatable, params.deletable
        )
        bare_params = self._client.params.bare.update(params)
        bare_params.__setattr__("approval_program", bare_params.approval_program or compiled.compiled_approval)
        bare_params.__setattr__("clear_state_program", bare_params.clear_state_program or compiled.compiled_clear)
        call_result = self._client._handle_call_errors(lambda: self._algorand.send.app_update(bare_params))
        return SendAppTransactionResult(**{**call_result.__dict__, **(compiled.__dict__ if compiled else {})})

    def opt_in(self, params: AppClientBareCallWithSendParams) -> SendAppTransactionResult:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call(self._client.params.bare.opt_in(params))
        )

    def delete(self, params: AppClientBareCallWithSendParams) -> SendAppTransactionResult:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call(self._client.params.bare.delete(params))
        )

    def clear_state(self, params: AppClientBareCallWithSendParams) -> SendAppTransactionResult:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call(self._client.params.bare.clear_state(params))
        )

    def close_out(self, params: AppClientBareCallWithSendParams) -> SendAppTransactionResult:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call(self._client.params.bare.close_out(params))
        )

    def call(self, params: AppClientBareCallWithCallOnCompleteParams) -> SendAppTransactionResult:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call(self._client.params.bare.call(params))
        )


class _AppClientSendAccessor:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec
        self._bare_send_accessor = _AppClientBareSendAccessor(client)

    @property
    def bare(self) -> _AppClientBareSendAccessor:
        return self._bare_send_accessor

    def fund_app_account(self, params: FundAppAccountParams) -> SendSingleTransactionResult:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.payment(self._client.params.fund_app_account(params))
        )

    def opt_in(self, params: AppClientMethodCallWithSendParams) -> SendAppTransactionResult:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call_method_call(self._client.params.opt_in(params))
        )

    def delete(self, params: AppClientMethodCallWithSendParams) -> SendAppTransactionResult:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_delete_method_call(self._client.params.delete(params))
        )

    def update(self, params: AppClientMethodCallWithCompilationAndSendParams) -> SendAppTransactionResult:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_update_method_call(self._client.params.update(params))
        )

    def close_out(self, params: AppClientMethodCallWithSendParams) -> SendAppTransactionResult:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call_method_call(self._client.params.close_out(params))
        )

    def call(self, params: AppClientMethodCallWithSendParams) -> SendAppTransactionResult:
        is_read_only_call = (
            params.on_complete == algosdk.transaction.OnComplete.NoOpOC
            or not params.on_complete
            and get_arc56_method(params.method, self._app_spec).method.readonly
        )

        if is_read_only_call:
            method_call_to_simulate = self._algorand.new_group().add_app_call_method_call(
                self._client.params.call(params)
            )

            simulate_response = self._client._handle_call_errors(
                lambda: method_call_to_simulate.simulate(
                    allow_unnamed_resources=params.populate_app_call_resources or True,
                    skip_signatures=True,
                    allow_more_logs=True,
                    allow_empty_signatures=True,
                    extra_opcode_budget=None,
                    exec_trace_config=None,
                    round=None,
                    fix_signers=None,  # TODO: double check on whether algosdk py even has this param
                )
            )

            return SendAppTransactionResult(
                tx_id=simulate_response.tx_ids[-1],
                tx_ids=simulate_response.tx_ids,
                transactions=simulate_response.transactions,
                transaction=simulate_response.transactions[-1],
                confirmation=simulate_response.confirmations[-1] if simulate_response.confirmations else b"",
                confirmations=simulate_response.confirmations,
                group_id=simulate_response.group_id or "",
                returns=simulate_response.returns,
                return_value=simulate_response.returns[-1].return_value,
            )

        return self._client._handle_call_errors(
            lambda: self._algorand.send.app_call_method_call(self._client.params.call(params))
        )


class AppClient:
    def __init__(self, params: AppClientParams) -> None:
        self._app_id = params.app_id
        self._app_spec = self.normalise_app_spec(params.app_spec)
        self._algorand = params.algorand
        self._app_address = algosdk.logic.get_application_address(self._app_id)
        self._app_name = params.app_name or self._app_spec.name
        self._default_sender = params.default_sender
        self._default_signer = params.default_signer
        self._approval_source_map = params.approval_source_map
        self._clear_source_map = params.clear_source_map
        self._state_accessor = _AppClientStateAccessor(self)
        self._params_accessor = _AppClientMethodCallParamsAccessor(self)
        self._send_accessor = _AppClientSendAccessor(self)
        self._create_transaction_accessor = _AppClientMethodCallTransactionCreator(self)

    @property
    def app_id(self) -> int:
        return self._app_id

    @property
    def app_address(self) -> str:
        return self._app_address

    @property
    def app_name(self) -> str:
        return self._app_name

    @property
    def app_spec(self) -> Arc56Contract:
        return self._app_spec

    @property
    def state(self) -> _AppClientStateAccessor:
        return self._state_accessor

    @property
    def params(self) -> _AppClientMethodCallParamsAccessor:
        return self._params_accessor

    @property
    def send(self) -> _AppClientSendAccessor:
        return self._send_accessor

    @property
    def create_transaction(self) -> _AppClientMethodCallTransactionCreator:
        return self._create_transaction_accessor

    @staticmethod
    def normalise_app_spec(app_spec: Arc56Contract | ApplicationSpecification | str) -> Arc56Contract:
        if isinstance(app_spec, str):
            spec = json.loads(app_spec)
            if "hints" in spec:
                spec = ApplicationSpecification.from_json(app_spec)
        else:
            spec = app_spec

        if isinstance(spec, Arc56Contract):
            return spec

        elif isinstance(spec, ApplicationSpecification):
            # Convert ARC-32 to ARC-56
            from algokit_utils.applications.utils import arc32_to_arc56

            return arc32_to_arc56(spec)
        elif isinstance(spec, dict):
            return Arc56Contract(**spec)
        else:
            raise ValueError("Invalid app spec format")

    @staticmethod
    def from_network(
        app_spec: Arc56Contract | ApplicationSpecification | str,
        algorand: AlgorandClientProtocol,
        app_name: str | None = None,
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
        network = algorand.client.network()
        app_spec = AppClient.normalise_app_spec(app_spec)
        network_names = [network.genesis_hash]

        if network.is_local_net:
            network_names.append("localnet")
        if network.is_main_net:
            network_names.append("mainnet")
        if network.is_test_net:
            network_names.append("testnet")

        available_app_spec_networks = list(app_spec.networks.keys()) if app_spec.networks else []
        network_index = next((i for i, n in enumerate(available_app_spec_networks) if n in network_names), None)

        if network_index is None:
            raise Exception(f"No app ID found for network {json.dumps(network_names)} in the app spec")

        app_id = app_spec.networks[available_app_spec_networks[network_index]]["app_id"]  # type: ignore[index]

        return AppClient(
            AppClientParams(
                app_id=app_id,
                app_spec=app_spec,
                algorand=algorand,
                app_name=app_name,
                default_sender=default_sender,
                default_signer=default_signer,
                approval_source_map=approval_source_map,
                clear_source_map=clear_source_map,
            )
        )

    @staticmethod
    def compile(
        app_spec: Arc56Contract,
        app_manager: AppManager,
        deploy_time_params: TealTemplateParams | None = None,
        updatable: bool | None = None,
        deletable: bool | None = None,
    ) -> AppClientCompilationResult:
        if not app_spec.source:
            if not app_spec.byte_code or not app_spec.byte_code.get("approval") or not app_spec.byte_code.get("clear"):
                raise ValueError(f"Attempt to compile app {app_spec.name} without source or byte_code")

            return AppClientCompilationResult(
                approval_program=base64.b64decode(app_spec.byte_code.get("approval", "")),
                clear_state_program=base64.b64decode(app_spec.byte_code.get("clear", "")),
            )

        approval_template: str = base64.b64decode(app_spec.source.get("approval", "")).decode("utf-8")  # type: ignore[assignment]
        deployment_metadata = (
            {"updatable": updatable or False, "deletable": deletable or False}
            if updatable is not None or deletable is not None
            else None
        )
        compiled_approval = app_manager.compile_teal_template(
            approval_template,
            template_params=deploy_time_params,
            deployment_metadata=deployment_metadata,
        )

        clear_template: str = base64.b64decode(app_spec.source.get("clear", "")).decode("utf-8")  # type: ignore[assignment]
        compiled_clear = app_manager.compile_teal_template(
            clear_template,
            template_params=deploy_time_params,
        )

        # TODO: Add invocation of persisting sourcemaps
        return AppClientCompilationResult(
            approval_program=compiled_approval.compiled_base64_to_bytes,
            compiled_approval=compiled_approval,
            clear_state_program=compiled_clear.compiled_base64_to_bytes,
            compiled_clear=compiled_clear,
        )

    @staticmethod
    def expose_logic_error_static(
        e: Exception, app_spec: Arc56Contract, details: ExposedLogicErrorDetails
    ) -> Exception:
        """Takes an error that may include a logic error and re-exposes it with source info."""
        source_map = details.clear_source_map if details.is_clear_state_program else details.approval_source_map

        error_details = parse_logic_error(str(e))
        if not error_details:
            return e

        # The PC value to find in the ARC56 SourceInfo
        arc56_pc = error_details["pc"]

        program_source_info = (
            details.clear_source_info if details.is_clear_state_program else details.approval_source_info
        )

        # The offset to apply to the PC if using the cblocks pc offset method
        cblocks_offset = 0

        # If the program uses cblocks offset, then we need to adjust the PC accordingly
        if program_source_info and program_source_info.pc_offset_method == "cblocks":
            if not details.program:
                raise Exception("Program bytes are required to calculate the ARC56 cblocks PC offset")

            cblocks_offset = get_constant_block_offset(details.program)
            arc56_pc = error_details["pc"] - cblocks_offset

        # Find the source info for this PC and get the error message
        source_info = None
        if program_source_info and program_source_info.source_info:
            source_info = next(
                (s for s in program_source_info.source_info if isinstance(s, SourceInfoDetail) and arc56_pc in s.pc),
                None,
            )
        error_message = source_info.error_message if source_info else None

        # If we have the source we can display the TEAL in the error message
        if hasattr(app_spec, "source"):
            program_source = (
                (app_spec.source.get("clear") if details.is_clear_state_program else app_spec.source.get("approval"))
                if app_spec.source
                else None
            )
            if program_source:
                e = LogicError(
                    logic_error_str=str(e),
                    program=program_source,
                    source_map=source_map,
                    transaction_id=error_details["transaction_id"],
                    message=error_details["message"],
                    pc=error_details["pc"],
                    logic_error=e,
                    traces=None,
                )

        if error_message:
            import re

            app_id = re.search(r"(?<=app=)\d+", str(e))
            tx_id = re.search(r"(?<=transaction )\S+(?=:)", str(e))
            error = Exception(
                f"Runtime error when executing {app_spec.name} "
                f"(appId: {app_id.group() if app_id else ''}) in transaction "
                f"{tx_id.group() if tx_id else ''}: {error_message}"
            )
            error.__cause__ = e
            return error

        return e

    # NOTE: No method overloads hence slightly different name, in TS its both instance/static methods named 'compile'
    def compile_and_persist_sourcemaps(
        self,
        deploy_time_params: TealTemplateParams | None = None,
        updatable: bool | None = None,
        deletable: bool | None = None,
    ) -> AppClientCompilationResult:
        result = AppClient.compile(self._app_spec, self._algorand.app, deploy_time_params, updatable, deletable)

        if result.compiled_approval:
            self._approval_source_map = result.compiled_approval.source_map
        if result.compiled_clear:
            self._clear_source_map = result.compiled_clear.source_map

        return result

    def clone(
        self,
        app_name: str | None = None,
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
        return AppClient(
            AppClientParams(
                app_id=self._app_id,
                algorand=self._algorand,
                app_spec=self._app_spec,
                app_name=app_name or self._app_name,
                default_sender=default_sender or self._default_sender,
                default_signer=default_signer or self._default_signer,
                approval_source_map=approval_source_map or self._approval_source_map,
                clear_source_map=clear_source_map or self._clear_source_map,
            )
        )

    def export_source_maps(self) -> AppSourceMaps:
        if not self._approval_source_map or not self._clear_source_map:
            raise ValueError(
                "Unable to export source maps; they haven't been loaded into this client - "
                "you need to call create, update, or deploy first"
            )

        return AppSourceMaps(
            approval_source_map=self._approval_source_map,
            clear_source_map=self._clear_source_map,
        )

    def import_source_maps(self, source_maps: AppSourceMaps) -> None:
        self._approval_source_map = source_maps.approval_source_map
        self._clear_source_map = source_maps.clear_source_map

    def get_local_state(self, address: str) -> dict[str, AppState]:
        return self._state_accessor.get_local_state(address)

    def get_global_state(self) -> dict[str, AppState]:
        return self._state_accessor.get_global_state()

    def get_box_names(self) -> list[BoxName]:
        return self._algorand.app.get_box_names(self._app_id)

    def get_box_value(self, name: BoxIdentifier) -> bytes:
        return self._algorand.app.get_box_value(self._app_id, name)

    def get_box_value_from_abi_type(self, name: BoxIdentifier, abi_type: ABIType) -> Any:
        return self._algorand.app.get_box_value_from_abi_type(self._app_id, name, abi_type)

    def get_box_values(self, filter_func: Callable[[BoxName], bool] | None = None) -> list[BoxValue]:
        names = self.get_box_names()
        if filter_func:
            names = [name for name in names if filter_func(name)]

        # Get values for filtered names
        values = self._algorand.app.get_box_values(self.app_id, [name.name_raw for name in names])

        # Return list of BoxValue objects
        return [BoxValue(name=name, value=values[i]) for i, name in enumerate(names)]

    def get_box_values_from_abi_type(
        self, abi_type: ABIType, filter_func: Callable[[BoxName], bool] | None = None
    ) -> list[BoxABIValue]:
        # Get box names and apply filter if provided
        names = self.get_box_names()
        if filter_func:
            names = [name for name in names if filter_func(name)]

        # Get values for filtered names and decode them
        values = self._algorand.app.get_box_values_from_abi_type(
            self.app_id, [name.name_raw for name in names], abi_type
        )

        # Return list of BoxABIValue objects
        return [BoxABIValue(name=name, value=values[i]) for i, name in enumerate(names)]

    def new_group(self) -> TransactionComposer:
        return self._algorand.new_group()

    def fund_app_account(self, params: FundAppAccountParams) -> SendSingleTransactionResult:
        return self.send.fund_app_account(params)

    def expose_logic_error(self, e: Exception, is_clear_state_program: bool = False) -> Exception:  # noqa: FBT001, FBT002
        """Takes an error that may include a logic error from a call to the current app and re-exposes the
        error to include source code information via the source map and ARC-56 spec.

        Args:
            e: The error to parse
            is_clear_state_program: Whether the code was running the clear state program (defaults to approval program)

        Returns:
            The new error, or if there was no logic error or source map then the wrapped error with source details
        """

        # Get source info based on program type
        source_info = None
        if hasattr(self._app_spec, "source_info") and self._app_spec.source_info:
            source_info = (
                self._app_spec.source_info.get("clear")
                if is_clear_state_program
                else self._app_spec.source_info.get("approval")
            )

        pc_offset_method = source_info.pc_offset_method if source_info else None

        program: bytes | None = None
        if pc_offset_method == "cblocks":
            # TODO: Cache this if we deploy the app and it's not updateable
            app_info = self._algorand.app.get_by_id(self.app_id)
            program = app_info.clear_state_program if is_clear_state_program else app_info.approval_program

        return AppClient.expose_logic_error_static(
            e,
            self._app_spec,
            ExposedLogicErrorDetails(
                is_clear_state_program=is_clear_state_program,
                approval_source_map=self._approval_source_map,
                clear_source_map=self._clear_source_map,
                program=program,
                approval_source_info=(
                    self._app_spec.source_info.get("approval")
                    if self._app_spec.source_info and hasattr(self._app_spec, "source_info")
                    else None
                ),
                clear_source_info=(
                    self._app_spec.source_info.get("clear")
                    if self._app_spec.source_info and hasattr(self._app_spec, "source_info")
                    else None
                ),
            ),
        )

    def _handle_call_errors(self, call: Callable[[], T]) -> T:
        """Make the given call and catch any errors, augmenting with debugging information before re-throwing."""
        try:
            return call()
        except Exception as e:
            raise self.expose_logic_error(e=e) from None

    def _get_sender(self, sender: str | None) -> str:
        if not sender and not self._default_sender:
            raise Exception(
                f"No sender provided and no default sender present in app client for call to app {self.app_name}"
            )
        return sender or self._default_sender  # type: ignore[return-value]

    def _get_signer(self, sender: str | None, signer: TransactionSigner | None) -> TransactionSigner | None:
        return signer or self._default_signer if sender else None

    def _get_bare_params(self, params: dict[str, Any], on_complete: algosdk.transaction.OnComplete) -> dict[str, Any]:
        """Get bare parameters for application calls.

        Args:
            params: The parameters to process
            on_complete: The OnComplete value for the transaction

        Returns:
            The processed parameters with defaults filled in
        """
        sender = self._get_sender(params.get("sender"))
        return {
            **params,
            "app_id": self._app_id,
            "sender": sender,
            "signer": self._get_signer(params.get("sender"), params.get("signer")),
            "on_complete": on_complete,
        }

    def _get_abi_args_with_default_values(  # noqa: C901, PLR0912
        self,
        *,
        method_name_or_signature: str,
        args: list[ABIValue | ABIStruct | AppMethodCallTransactionArgument | None] | None,
        sender: str,
    ) -> list[Any]:
        """Get ABI args with default values filled in.

        Args:
            method_name_or_signature: Method name or ABI signature
            args: Optional list of argument values
            sender: Sender address

        Returns:
            List of argument values with defaults filled in

        Raises:
            ValueError: If required argument is missing or default value lookup fails
        """
        method = get_arc56_method(method_name_or_signature, self._app_spec)
        result = []

        for i, method_arg in enumerate(method.args):
            # Get provided arg value if any
            arg_value = args[i] if args and i < len(args) else None

            if arg_value is not None:
                # Convert struct to tuple if needed
                if method_arg.struct and isinstance(arg_value, dict):
                    arg_value = get_abi_tuple_from_abi_struct(
                        arg_value, self._app_spec.structs[method_arg.struct], self._app_spec.structs
                    )
                result.append(arg_value)
                continue

            # Handle default value if arg not provided
            default_value = method_arg.default_value
            if default_value:
                match default_value.source:
                    case "literal":
                        value_raw = base64.b64decode(default_value.data)
                        value_type = default_value.type or method_arg.type
                        result.append(get_abi_decoded_value(value_raw, value_type, self._app_spec.structs))

                    case "method":
                        # Get method return value
                        default_method = get_arc56_method(default_value.data, self._app_spec)
                        empty_args = [None] * len(default_method.args)
                        call_result = self.send.app_call_method_call(
                            {"method": default_value.data, "args": empty_args, "sender": sender}
                        )

                        if not call_result.return_value:
                            raise ValueError("Default value method call did not return a value")

                        if isinstance(call_result.return_value, dict):
                            # Convert struct return value to tuple
                            result.append(
                                get_abi_tuple_from_abi_struct(
                                    call_result.return_value,
                                    self._app_spec.structs[default_method.returns.struct],
                                    self._app_spec.structs,
                                )
                            )
                        else:
                            result.append(call_result.return_value)

                    case "local" | "global":
                        # Get state value
                        state = (
                            self.get_global_state()
                            if default_value.source == "global"
                            else self.get_local_state(sender)
                        )
                        value = next((s for s in state.values() if s.key_base64 == default_value.data), None)
                        if not value:
                            raise ValueError(
                                f"Key '{default_value.data}' not found in {default_value.source} "
                                f"storage for argument {method_arg.name or f'arg{i+1}'}"
                            )

                        if value.value_raw:
                            value_type = default_value.type or method_arg.type
                            result.append(get_abi_decoded_value(value.value_raw, value_type, self._app_spec.structs))
                        else:
                            result.append(value.value)

                    case "box":
                        # Get box value
                        box_name = base64.b64decode(default_value.data)
                        box_value = self._algorand.app.get_box_value(self._app_id, box_name)
                        value_type = default_value.type or method_arg.type
                        result.append(get_abi_decoded_value(box_value, value_type, self._app_spec.structs))

            elif not algosdk.abi.is_abi_transaction_type(method_arg.type):
                # Error if required non-txn arg missing
                raise ValueError(
                    f"No value provided for required argument "
                    f"{method_arg.name or f'arg{i+1}'} in call to method {method.name}"
                )

        return result

    def _get_abi_params(self, params: dict[str, Any], on_complete: algosdk.transaction.OnComplete) -> dict[str, Any]:
        sender = self._get_sender(params.get("sender"))
        method = get_arc56_method(params["method"], self._app_spec)
        args = self._get_abi_args_with_default_values(params["method"], params.get("args"), sender)
        return {
            **params,
            "appId": self._app_id,
            "sender": sender,
            "signer": self._get_signer(params.get("sender"), params.get("signer")),
            "method": method,
            "onComplete": on_complete,
            "args": args,
        }
