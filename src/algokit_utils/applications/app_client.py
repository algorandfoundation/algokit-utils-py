from __future__ import annotations

import base64
import copy
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

import algosdk
from algosdk.source_map import SourceMap
from algosdk.transaction import OnComplete, Transaction
from typing_extensions import Self

from algokit_utils._debugging import PersistSourceMapInput, persist_sourcemaps
from algokit_utils.applications.abi import (
    ABIReturn,
    BoxABIValue,
    get_abi_decoded_value,
    get_abi_encoded_value,
    get_abi_tuple_from_abi_struct,
)
from algokit_utils.applications.app_spec.arc32 import Arc32Contract
from algokit_utils.applications.app_spec.arc56 import (
    Arc56Contract,
    PcOffsetMethod,
    ProgramSourceInfo,
    SourceInfo,
    StorageKey,
    StorageMap,
)
from algokit_utils.config import config
from algokit_utils.errors.logic_error import LogicError, parse_logic_error
from algokit_utils.models.application import (
    AppSourceMaps,
    AppState,
    CompiledTeal,
)
from algokit_utils.models.state import BoxName, BoxValue
from algokit_utils.models.transaction import SendParams
from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCallParams,
    AppCallParams,
    AppDeleteMethodCallParams,
    AppMethodCallTransactionArgument,
    AppUpdateMethodCallParams,
    AppUpdateParams,
    BuiltTransactions,
    PaymentParams,
)
from algokit_utils.transactions.transaction_sender import (
    SendAppTransactionResult,
    SendAppUpdateTransactionResult,
    SendSingleTransactionResult,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from algosdk.atomic_transaction_composer import TransactionSigner

    from algokit_utils.applications.abi import ABIStruct, ABIType, ABIValue
    from algokit_utils.applications.app_deployer import AppLookup
    from algokit_utils.applications.app_manager import AppManager
    from algokit_utils.models.amount import AlgoAmount
    from algokit_utils.models.state import BoxIdentifier, BoxReference, TealTemplateParams
    from algokit_utils.protocols.client import AlgorandClientProtocol

__all__ = [
    "AppClient",
    "AppClientBareCallParams",
    "AppClientBareCallWithCallOnCompleteParams",
    "AppClientBareCallWithCompilationAndSendParams",
    "AppClientBareCallWithCompilationParams",
    "AppClientBareCallWithSendParams",
    "AppClientCallParams",
    "AppClientCompilationParams",
    "AppClientCompilationResult",
    "AppClientMethodCallParams",
    "AppClientMethodCallWithCompilationAndSendParams",
    "AppClientMethodCallWithCompilationParams",
    "AppClientMethodCallWithSendParams",
    "AppClientParams",
    "AppSourceMaps",
    "FundAppAccountParams",
    "TypedAppClientProtocol",
]

# TEAL opcodes for constant blocks
BYTE_CBLOCK = 38  # bytecblock opcode
INT_CBLOCK = 32  # intcblock opcode

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


class TypedAppClientProtocol(Protocol):
    @classmethod
    def from_creator_and_name(
        cls,
        *,
        creator_address: str,
        app_name: str,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: AppLookup | None = None,
        algorand: AlgorandClientProtocol,
    ) -> Self: ...

    @classmethod
    def from_network(
        cls,
        *,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
        algorand: AlgorandClientProtocol,
    ) -> Self: ...

    def __init__(
        self,
        *,
        app_id: int,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        algorand: AlgorandClientProtocol,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> None: ...


@dataclass(kw_only=True, frozen=True)
class AppClientCompilationResult:
    approval_program: bytes
    clear_state_program: bytes
    compiled_approval: CompiledTeal | None = None
    compiled_clear: CompiledTeal | None = None


@dataclass(kw_only=True, frozen=True)
class AppClientCompilationParams:
    deploy_time_params: TealTemplateParams | None = None
    updatable: bool | None = None
    deletable: bool | None = None


@dataclass(kw_only=True)
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


@dataclass(kw_only=True)
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


@dataclass(kw_only=True, frozen=True)
class AppClientMethodCallParams:
    method: str
    args: Sequence[ABIValue | ABIStruct | AppMethodCallTransactionArgument | None] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: Sequence[BoxReference | BoxIdentifier] | None = None
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


@dataclass(kw_only=True, frozen=True)
class AppClientMethodCallWithCompilationParams(AppClientMethodCallParams, AppClientCompilationParams):
    """Combined parameters for method calls with compilation"""


@dataclass(kw_only=True, frozen=True)
class AppClientMethodCallWithSendParams(AppClientMethodCallParams, SendParams):
    """Combined parameters for method calls with send options"""


@dataclass(kw_only=True, frozen=True)
class AppClientMethodCallWithCompilationAndSendParams(
    AppClientMethodCallParams, AppClientCompilationParams, SendParams
):
    """Combined parameters for method calls with compilation and send options"""


@dataclass(kw_only=True, frozen=True)
class AppClientBareCallParams:
    signer: TransactionSigner | None = None
    rekey_to: str | None = None
    lease: bytes | None = None
    static_fee: AlgoAmount | None = None
    extra_fee: AlgoAmount | None = None
    max_fee: AlgoAmount | None = None
    validity_window: int | None = None
    first_valid_round: int | None = None
    last_valid_round: int | None = None
    sender: str | None = None
    note: bytes | None = None
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None


@dataclass(kw_only=True, frozen=True)
class _CallOnComplete:
    on_complete: algosdk.transaction.OnComplete


@dataclass(kw_only=True, frozen=True)
class AppClientBareCallWithCompilationParams(AppClientBareCallParams, AppClientCompilationParams):
    """Combined parameters for bare calls with compilation"""


@dataclass(kw_only=True, frozen=True)
class AppClientBareCallWithSendParams(AppClientBareCallParams, SendParams):
    """Combined parameters for bare calls with send options"""


@dataclass(kw_only=True, frozen=True)
class AppClientBareCallWithCompilationAndSendParams(AppClientBareCallParams, AppClientCompilationParams, SendParams):
    """Combined parameters for bare calls with compilation and send options"""


@dataclass(kw_only=True, frozen=True)
class AppClientBareCallWithCallOnCompleteParams(AppClientBareCallParams, _CallOnComplete):
    """Combined parameters for bare calls with an OnComplete value"""


class _AppClientStateMethodsProtocol(Protocol):
    def get_all(self) -> dict[str, Any]: ...

    def get_value(self, name: str, app_state: dict[str, AppState] | None = None) -> ABIValue | None: ...

    def get_map_value(self, map_name: str, key: bytes | Any, app_state: dict[str, AppState] | None = None) -> Any: ...  # noqa: ANN401

    def get_map(self, map_name: str) -> dict[str, ABIValue]: ...


class _AppClientBoxMethodsProtocol(Protocol):
    def get_all(self) -> dict[str, Any]: ...

    def get_value(self, name: str) -> ABIValue | None: ...

    def get_map_value(self, map_name: str, key: bytes | Any) -> Any: ...  # noqa: ANN401

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


class _AppClientBoxMethods(_AppClientBoxMethodsProtocol):
    def __init__(
        self,
        *,
        get_all: Callable[[], dict[str, Any]],
        get_value: Callable[[str], ABIValue | None],
        get_map_value: Callable[[str, bytes | Any], Any],
        get_map: Callable[[str], dict[str, ABIValue]],
    ) -> None:
        self._get_all = get_all
        self._get_value = get_value
        self._get_map_value = get_map_value
        self._get_map = get_map

    def get_all(self) -> dict[str, Any]:
        return self._get_all()

    def get_value(self, name: str) -> ABIValue | None:
        return self._get_value(name)

    def get_map_value(self, map_name: str, key: bytes | Any) -> Any:  # noqa: ANN401
        return self._get_map_value(map_name, key)

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
            key_getter=lambda: self._app_spec.state.keys.local_state,
            map_getter=lambda: self._app_spec.state.maps.local_state,
        )

    @property
    def global_state(self) -> _AppClientStateMethodsProtocol:
        """Methods to access global state for the current app"""
        return self._get_state_methods(
            state_getter=lambda: self._algorand.app.get_global_state(self._app_id),
            key_getter=lambda: self._app_spec.state.keys.global_state,
            map_getter=lambda: self._app_spec.state.maps.global_state,
        )

    @property
    def box(self) -> _AppClientBoxMethodsProtocol:
        """Methods to access box storage for the current app"""
        return self._get_box_methods()

    def _get_box_methods(self) -> _AppClientBoxMethodsProtocol:
        """Get methods to access box storage for the current app."""

        def get_all() -> dict[str, Any]:
            """Returns all single-key box values in a dict keyed by the key name."""
            return {key: get_value(key) for key in self._app_spec.state.keys.box}

        def get_value(name: str) -> ABIValue | None:
            """Returns a single box value for the current app with the value a decoded ABI value.

            Args:
                name: The name of the box value to retrieve
            """
            metadata = self._app_spec.state.keys.box[name]
            value = self._algorand.app.get_box_value(self._app_id, base64.b64decode(metadata.key))
            return get_abi_decoded_value(value, metadata.value_type, self._app_spec.structs)

        def get_map_value(map_name: str, key: bytes | Any) -> Any:  # noqa: ANN401
            """Get a value from a box map.

            Args:
                map_name: The name of the map to read from
                key: The key within the map (without any map prefix) as either bytes or a value
                    that will be converted to bytes by encoding it using the specified ABI key type
            """
            metadata = self._app_spec.state.maps.box[map_name]
            prefix = base64.b64decode(metadata.prefix or "")
            encoded_key = get_abi_encoded_value(key, metadata.key_type, self._app_spec.structs)
            full_key = base64.b64encode(prefix + encoded_key).decode("utf-8")
            value = self._algorand.app.get_box_value(self._app_id, base64.b64decode(full_key))
            return get_abi_decoded_value(value, metadata.value_type, self._app_spec.structs)

        def get_map(map_name: str) -> dict[str, ABIValue]:
            """Get all key-value pairs from a box map.

            Args:
                map_name: The name of the map to read from
            """
            metadata = self._app_spec.state.maps.box[map_name]
            prefix = base64.b64decode(metadata.prefix or "")
            box_names = self._algorand.app.get_box_names(self._app_id)

            result = {}
            for box in box_names:
                if not box.name_raw.startswith(prefix):
                    continue

                encoded_key = prefix + box.name_raw
                base64_key = base64.b64encode(encoded_key).decode("utf-8")

                try:
                    key = get_abi_decoded_value(box.name_raw[len(prefix) :], metadata.key_type, self._app_spec.structs)
                    value = get_abi_decoded_value(
                        self._algorand.app.get_box_value(self._app_id, base64.b64decode(base64_key)),
                        metadata.value_type,
                        self._app_spec.structs,
                    )
                    result[str(key)] = value
                except Exception as e:
                    if "Failed to decode key" in str(e):
                        raise ValueError(f"Failed to decode key {base64_key}") from e
                    raise ValueError(f"Failed to decode value for key {base64_key}") from e

            return result

        return _AppClientBoxMethods(
            get_all=get_all,
            get_value=get_value,
            get_map_value=get_map_value,
            get_map=get_map,
        )

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

            return value.value if value else None

        def get_map_value(map_name: str, key: bytes | Any, app_state: dict[str, AppState] | None = None) -> Any:  # noqa: ANN401
            state = app_state or state_getter()
            metadata = map_getter()[map_name]

            prefix = bytes(metadata.prefix or "", "base64")
            encoded_key = get_abi_encoded_value(key, metadata.key_type, self._app_spec.structs)
            full_key = base64.b64encode(prefix + encoded_key).decode("utf-8")
            value = next((s for s in state.values() if s.key_base64 == full_key), None)
            if value and value.value_raw:
                return get_abi_decoded_value(value.value_raw, metadata.value_type, self._app_spec.structs)
            return value.value if value else None

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

    def opt_in(self, params: AppClientMethodCallParams) -> AppCallMethodCallParams:
        input_params = self._get_abi_params(params.__dict__, on_complete=algosdk.transaction.OnComplete.OptInOC)
        return AppCallMethodCallParams(**input_params)

    def call(self, params: AppClientMethodCallParams) -> AppCallMethodCallParams:
        input_params = self._get_abi_params(params.__dict__, on_complete=algosdk.transaction.OnComplete.NoOpOC)
        return AppCallMethodCallParams(**input_params)

    def delete(self, params: AppClientMethodCallParams) -> AppDeleteMethodCallParams:
        input_params = self._get_abi_params(
            params.__dict__, on_complete=algosdk.transaction.OnComplete.DeleteApplicationOC
        )
        return AppDeleteMethodCallParams(**input_params)

    def update(
        self, params: AppClientMethodCallParams | AppClientMethodCallWithCompilationAndSendParams
    ) -> AppUpdateMethodCallParams:
        compile_params = (
            self._client.compile(
                app_spec=self._client.app_spec,
                app_manager=self._algorand.app,
                deploy_time_params=params.deploy_time_params,
                updatable=params.updatable,
                deletable=params.deletable,
            ).__dict__
            if isinstance(params, AppClientMethodCallWithCompilationAndSendParams)
            else {}
        )

        input_params = {
            **self._get_abi_params(params.__dict__, on_complete=algosdk.transaction.OnComplete.UpdateApplicationOC),
            **compile_params,
        }
        # Filter input_params to include only fields valid for AppUpdateMethodCallParams
        app_update_method_call_fields = {field.name for field in fields(AppUpdateMethodCallParams)}
        filtered_input_params = {k: v for k, v in input_params.items() if k in app_update_method_call_fields}
        return AppUpdateMethodCallParams(**filtered_input_params)

    def close_out(self, params: AppClientMethodCallParams) -> AppCallMethodCallParams:
        input_params = self._get_abi_params(params.__dict__, on_complete=algosdk.transaction.OnComplete.CloseOutOC)
        return AppCallMethodCallParams(**input_params)

    def _get_abi_params(self, params: dict[str, Any], on_complete: algosdk.transaction.OnComplete) -> dict[str, Any]:
        input_params = copy.deepcopy(params)

        input_params["app_id"] = self._app_id
        input_params["on_complete"] = on_complete

        input_params["sender"] = self._client._get_sender(params["sender"])
        input_params["signer"] = self._client._get_signer(params["sender"], params["signer"])

        if params.get("method"):
            input_params["method"] = self._app_spec.get_arc56_method(params["method"]).to_abi_method()
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
    ) -> SendAppTransactionResult[ABIReturn]:
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
        compiled = self._client.compile_sourcemaps(params.deploy_time_params, params.updatable, params.deletable)
        bare_params = self._client.params.bare.update(params)
        bare_params.__setattr__("approval_program", bare_params.approval_program or compiled.compiled_approval)
        bare_params.__setattr__("clear_state_program", bare_params.clear_state_program or compiled.compiled_clear)
        call_result = self._client._handle_call_errors(lambda: self._algorand.send.app_update(bare_params))
        return SendAppTransactionResult[ABIReturn](
            **{**call_result.__dict__, **(compiled.__dict__ if compiled else {})},
            abi_return=AppManager.get_abi_return(call_result.confirmation, getattr(params, "method", None)),
        )

    def opt_in(self, params: AppClientBareCallWithSendParams) -> SendAppTransactionResult[ABIReturn]:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call(self._client.params.bare.opt_in(params))
        )

    def delete(self, params: AppClientBareCallWithSendParams) -> SendAppTransactionResult[ABIReturn]:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call(self._client.params.bare.delete(params))
        )

    def clear_state(self, params: AppClientBareCallWithSendParams) -> SendAppTransactionResult[ABIReturn]:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call(self._client.params.bare.clear_state(params))
        )

    def close_out(self, params: AppClientBareCallWithSendParams) -> SendAppTransactionResult[ABIReturn]:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call(self._client.params.bare.close_out(params))
        )

    def call(self, params: AppClientBareCallWithCallOnCompleteParams) -> SendAppTransactionResult[ABIReturn]:
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

    def opt_in(self, params: AppClientMethodCallWithSendParams) -> SendAppTransactionResult[ABIReturn]:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call_method_call(self._client.params.opt_in(params))
        )

    def delete(self, params: AppClientMethodCallWithSendParams) -> SendAppTransactionResult[ABIReturn]:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_delete_method_call(self._client.params.delete(params))
        )

    def update(
        self, params: AppClientMethodCallWithCompilationAndSendParams
    ) -> SendAppUpdateTransactionResult[ABIReturn]:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_update_method_call(self._client.params.update(params))
        )

    def close_out(self, params: AppClientMethodCallWithSendParams) -> SendAppTransactionResult[ABIReturn]:
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.app_call_method_call(self._client.params.close_out(params))
        )

    def call(self, params: AppClientMethodCallWithSendParams) -> SendAppTransactionResult[ABIReturn]:
        is_read_only_call = (
            params.on_complete == algosdk.transaction.OnComplete.NoOpOC or params.on_complete is None
        ) and self._app_spec.get_arc56_method(params.method).readonly

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
                    simulation_round=None,
                )
            )

            return SendAppTransactionResult[ABIReturn](
                tx_ids=simulate_response.tx_ids,
                transactions=simulate_response.transactions,
                transaction=simulate_response.transactions[-1],
                confirmation=simulate_response.confirmations[-1] if simulate_response.confirmations else b"",
                confirmations=simulate_response.confirmations,
                group_id=simulate_response.group_id or "",
                returns=simulate_response.returns,
                abi_return=simulate_response.returns[-1],
            )

        return self._client._handle_call_errors(
            lambda: self._algorand.send.app_call_method_call(self._client.params.call(params))
        )


@dataclass(kw_only=True, frozen=True)
class AppClientParams:
    """Full parameters for creating an app client"""

    app_spec: Arc56Contract | Arc32Contract | str  # Using string quotes since these types may be defined elsewhere
    algorand: AlgorandClientProtocol  # Using string quotes since this type may be defined elsewhere
    app_id: int
    app_name: str | None = None
    default_sender: str | bytes | None = None  # Address can be string or bytes
    default_signer: TransactionSigner | None = None
    approval_source_map: SourceMap | None = None
    clear_source_map: SourceMap | None = None


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
    def algorand(self) -> AlgorandClientProtocol:
        return self._algorand

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
    def normalise_app_spec(app_spec: Arc56Contract | Arc32Contract | str) -> Arc56Contract:
        if isinstance(app_spec, str):
            spec_dict = json.loads(app_spec)
            spec = Arc32Contract.from_json(app_spec) if "hints" in spec_dict else spec_dict
        else:
            spec = app_spec

        match spec:
            case Arc56Contract():
                return spec
            case Arc32Contract():
                return Arc56Contract.from_arc32(spec.to_json())
            case dict():
                return Arc56Contract.from_dict(spec)
            case _:
                raise ValueError("Invalid app spec format")

    @staticmethod
    def from_network(
        app_spec: Arc56Contract | Arc32Contract | str,
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

        if network.is_localnet:
            network_names.append("localnet")
        if network.is_mainnet:
            network_names.append("mainnet")
        if network.is_testnet:
            network_names.append("testnet")

        available_app_spec_networks = list(app_spec.networks.keys()) if app_spec.networks else []
        network_index = next((i for i, n in enumerate(available_app_spec_networks) if n in network_names), None)

        if network_index is None:
            raise Exception(f"No app ID found for network {json.dumps(network_names)} in the app spec")

        app_id = app_spec.networks[available_app_spec_networks[network_index]].app_id  # type: ignore[index]

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
    def from_creator_and_name(
        creator_address: str,
        app_name: str,
        app_spec: Arc56Contract | Arc32Contract | str,
        algorand: AlgorandClientProtocol,
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: AppLookup | None = None,
    ) -> AppClient:
        app_spec_ = AppClient.normalise_app_spec(app_spec)
        app_lookup = app_lookup_cache or algorand.app_deployer.get_creator_apps_by_name(
            creator_address=creator_address, ignore_cache=ignore_cache or False
        )
        app_metadata = app_lookup.apps.get(app_name or app_spec_.name)
        if not app_metadata:
            raise ValueError(f"App not found for creator {creator_address} and name {app_name or app_spec_.name}")

        return AppClient(
            AppClientParams(
                app_id=app_metadata.app_id,
                app_spec=app_spec_,
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
        def is_base64(s: str) -> bool:
            try:
                return base64.b64encode(base64.b64decode(s)).decode() == s
            except Exception:
                return False

        if not app_spec.source:
            if not app_spec.byte_code or not app_spec.byte_code.approval or not app_spec.byte_code.clear:
                raise ValueError(f"Attempt to compile app {app_spec.name} without source or byte_code")

            return AppClientCompilationResult(
                approval_program=base64.b64decode(app_spec.byte_code.approval),
                clear_state_program=base64.b64decode(app_spec.byte_code.clear),
            )

        compiled_approval = app_manager.compile_teal_template(
            app_spec.source.get_decoded_approval(),
            template_params=deploy_time_params,
            deployment_metadata=(
                {"updatable": updatable, "deletable": deletable}
                if updatable is not None or deletable is not None
                else None
            ),
        )

        compiled_clear = app_manager.compile_teal_template(
            app_spec.source.get_decoded_clear(),
            template_params=deploy_time_params,
        )

        if config.debug and config.project_root:
            persist_sourcemaps(
                sources=[
                    PersistSourceMapInput(
                        compiled_teal=compiled_approval, app_name=app_spec.name, file_name="approval.teal"
                    ),
                    PersistSourceMapInput(compiled_teal=compiled_clear, app_name=app_spec.name, file_name="clear.teal"),
                ],
                project_root=config.project_root,
                client=app_manager._algod,
                with_sources=True,
            )

        return AppClientCompilationResult(
            approval_program=compiled_approval.compiled_base64_to_bytes,
            compiled_approval=compiled_approval,
            clear_state_program=compiled_clear.compiled_base64_to_bytes,
            compiled_clear=compiled_clear,
        )

    @staticmethod
    def _expose_logic_error_static(  # noqa: C901
        *,
        e: Exception,
        app_spec: Arc56Contract,
        is_clear_state_program: bool = False,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
        program: bytes | None = None,
        approval_source_info: ProgramSourceInfo | None = None,
        clear_source_info: ProgramSourceInfo | None = None,
    ) -> Exception:
        """Takes an error that may include a logic error and re-exposes it with source info."""
        source_map = clear_source_map if is_clear_state_program else approval_source_map

        error_details = parse_logic_error(str(e))
        if not error_details:
            return e

        # The PC value to find in the ARC56 SourceInfo
        arc56_pc = error_details["pc"]

        program_source_info = clear_source_info if is_clear_state_program else approval_source_info

        # The offset to apply to the PC if using the cblocks pc offset method
        cblocks_offset = 0

        # If the program uses cblocks offset, then we need to adjust the PC accordingly
        if program_source_info and program_source_info.pc_offset_method == PcOffsetMethod.CBLOCKS:
            if not program:
                raise Exception("Program bytes are required to calculate the ARC56 cblocks PC offset")

            cblocks_offset = get_constant_block_offset(program)
            arc56_pc = error_details["pc"] - cblocks_offset

        # Find the source info for this PC and get the error message
        source_info = None
        if program_source_info and program_source_info.source_info:
            source_info = next(
                (s for s in program_source_info.source_info if isinstance(s, SourceInfo) and arc56_pc in s.pc),
                None,
            )
        error_message = source_info.error_message if source_info else None

        # If we have the source we can display the TEAL in the error message
        if hasattr(app_spec, "source"):
            program_source = (
                (
                    app_spec.source.get_decoded_clear()
                    if is_clear_state_program
                    else app_spec.source.get_decoded_approval()
                )
                if app_spec.source
                else None
            )
            custom_get_line_for_pc = None

            def get_line_for_pc(input_pc: int) -> int | None:
                if not program_source_info:
                    return None
                teal = [line.teal for line in program_source_info.source_info if input_pc - cblocks_offset in line.pc]
                return teal[0] if teal else None

            if not source_map:
                custom_get_line_for_pc = get_line_for_pc

            if program_source:
                e = LogicError(
                    logic_error_str=str(e),
                    program=program_source,
                    source_map=source_map,
                    transaction_id=error_details["transaction_id"],
                    message=error_details["message"],
                    pc=error_details["pc"],
                    logic_error=e,
                    get_line_for_pc=custom_get_line_for_pc,
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
    def compile_sourcemaps(
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
        if not source_maps.approval_source_map:
            raise ValueError("Approval source map is required")
        if not source_maps.clear_source_map:
            raise ValueError("Clear source map is required")

        if not isinstance(source_maps.approval_source_map, dict | SourceMap):
            raise ValueError(
                "Approval source map supplied is of invalid type. Must be a raw dict or `algosdk.source_map.SourceMap`"
            )
        if not isinstance(source_maps.clear_source_map, dict | SourceMap):
            raise ValueError(
                "Clear source map supplied is of invalid type. Must be a raw dict or `algosdk.source_map.SourceMap`"
            )

        self._approval_source_map = (
            SourceMap(source_map=source_maps.approval_source_map)
            if isinstance(source_maps.approval_source_map, dict)
            else source_maps.approval_source_map
        )
        self._clear_source_map = (
            SourceMap(source_map=source_maps.clear_source_map)
            if isinstance(source_maps.clear_source_map, dict)
            else source_maps.clear_source_map
        )

    def get_local_state(self, address: str) -> dict[str, AppState]:
        return self._state_accessor.get_local_state(address)

    def get_global_state(self) -> dict[str, AppState]:
        return self._state_accessor.get_global_state()

    def get_box_names(self) -> list[BoxName]:
        return self._algorand.app.get_box_names(self._app_id)

    def get_box_value(self, name: BoxIdentifier) -> bytes:
        return self._algorand.app.get_box_value(self._app_id, name)

    def get_box_value_from_abi_type(self, name: BoxIdentifier, abi_type: ABIType) -> ABIValue:
        return self._algorand.app.get_box_value_from_abi_type(self._app_id, name, abi_type)

    def get_box_values(self, filter_func: Callable[[BoxName], bool] | None = None) -> list[BoxValue]:
        names = [n for n in self.get_box_names() if not filter_func or filter_func(n)]
        values = self._algorand.app.get_box_values(self.app_id, [n.name_raw for n in names])
        return [BoxValue(name=n, value=v) for n, v in zip(names, values, strict=False)]

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

    def fund_app_account(self, params: FundAppAccountParams) -> SendSingleTransactionResult:
        return self.send.fund_app_account(params)

    def _expose_logic_error(self, e: Exception, is_clear_state_program: bool = False) -> Exception:  # noqa: FBT001, FBT002
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
                self._app_spec.source_info.clear if is_clear_state_program else self._app_spec.source_info.approval
            )

        pc_offset_method = source_info.pc_offset_method if source_info else None

        program: bytes | None = None
        if pc_offset_method == "cblocks":
            # TODO: Cache this if we deploy the app and it's not updateable
            app_info = self._algorand.app.get_by_id(self.app_id)
            program = app_info.clear_state_program if is_clear_state_program else app_info.approval_program

        return AppClient._expose_logic_error_static(
            e=e,
            app_spec=self._app_spec,
            is_clear_state_program=is_clear_state_program,
            approval_source_map=self._approval_source_map,
            clear_source_map=self._clear_source_map,
            program=program,
            approval_source_info=(self._app_spec.source_info.approval if self._app_spec.source_info else None),
            clear_source_info=(self._app_spec.source_info.clear if self._app_spec.source_info else None),
        )

    def _handle_call_errors(self, call: Callable[[], T]) -> T:
        """Make the given call and catch any errors, augmenting with debugging information before re-throwing."""
        try:
            return call()
        except Exception as e:
            raise self._expose_logic_error(e=e) from None

    def _get_sender(self, sender: str | None) -> str:
        if not sender and not self._default_sender:
            raise Exception(
                f"No sender provided and no default sender present in app client for call to app {self.app_name}"
            )
        return sender or self._default_sender  # type: ignore[return-value]

    def _get_signer(self, sender: str | None, signer: TransactionSigner | None) -> TransactionSigner | None:
        return signer or self._default_signer if not sender or sender == self._default_sender else None

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
        args: Sequence[ABIValue | ABIStruct | AppMethodCallTransactionArgument | None] | None,
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
        method = self._app_spec.get_arc56_method(method_name_or_signature)
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
                        default_method = self._app_spec.get_arc56_method(default_value.data)
                        empty_args = [None] * len(default_method.args)
                        call_result = self._algorand.send.app_call_method_call(
                            AppCallMethodCallParams(
                                app_id=self._app_id,
                                method=algosdk.abi.Method.from_signature(default_value.data),
                                args=empty_args,
                                sender=sender,
                            )
                        )

                        if not call_result.abi_return:
                            raise ValueError("Default value method call did not return a value")

                        if isinstance(call_result.abi_return, dict):
                            # Convert struct return value to tuple
                            result.append(
                                get_abi_tuple_from_abi_struct(
                                    call_result.abi_return,
                                    self._app_spec.structs[str(default_method.returns.type)],
                                    self._app_spec.structs,
                                )
                            )
                        elif call_result.abi_return.value:
                            result.append(call_result.abi_return.value)

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
        method = self._app_spec.get_arc56_method(params["method"])
        args = self._get_abi_args_with_default_values(
            method_name_or_signature=params["method"], args=params.get("args"), sender=sender
        )
        return {
            **params,
            "appId": self._app_id,
            "sender": sender,
            "signer": self._get_signer(params.get("sender"), params.get("signer")),
            "method": method,
            "onComplete": on_complete,
            "args": args,
        }
