from __future__ import annotations

import base64
import copy
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any, Generic, Literal, TypedDict, TypeVar

import algosdk
from algosdk.source_map import SourceMap
from algosdk.transaction import OnComplete, Transaction

from algokit_utils._debugging import PersistSourceMapInput, persist_sourcemaps
from algokit_utils.applications.abi import (
    ABIReturn,
    ABIStruct,
    ABIType,
    ABIValue,
    Arc56ReturnValueType,
    BoxABIValue,
    get_abi_decoded_value,
    get_abi_encoded_value,
    get_abi_tuple_from_abi_struct,
)
from algokit_utils.applications.app_spec.arc32 import Arc32Contract
from algokit_utils.applications.app_spec.arc56 import (
    Arc56Contract,
    Method,
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
    AppCreateSchema,
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

    from algokit_utils.algorand import AlgorandClient
    from algokit_utils.applications.app_deployer import AppLookup
    from algokit_utils.applications.app_manager import AppManager
    from algokit_utils.models.amount import AlgoAmount
    from algokit_utils.models.state import BoxIdentifier, BoxReference, TealTemplateParams

__all__ = [
    "AppClient",
    "AppClientBareCallCreateParams",
    "AppClientBareCallParams",
    "AppClientCallParams",
    "AppClientCompilationParams",
    "AppClientCompilationResult",
    "AppClientCreateSchema",
    "AppClientMethodCallCreateParams",
    "AppClientMethodCallParams",
    "AppClientParams",
    "AppSourceMaps",
    "BaseAppClientMethodCallParams",
    "CreateOnComplete",
    "FundAppAccountParams",
    "get_constant_block_offset",
]

# TEAL opcodes for constant blocks
BYTE_CBLOCK = 38  # bytecblock opcode
INT_CBLOCK = 32  # intcblock opcode

T = TypeVar("T")  # For generic return type in _handle_call_errors

# Sentinel to detect missing arguments in clone() method of AppClient
_MISSING = object()


def get_constant_block_offset(program: bytes) -> int:  # noqa: C901
    """Calculate the offset after constant blocks in TEAL program.

    Analyzes a compiled TEAL program to find the ending offset position after any bytecblock and intcblock operations.

    :param program: The compiled TEAL program as bytes
    :return: The maximum offset position after any constant block operations
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


CreateOnComplete = Literal[
    OnComplete.NoOpOC,
    OnComplete.UpdateApplicationOC,
    OnComplete.DeleteApplicationOC,
    OnComplete.OptInOC,
    OnComplete.CloseOutOC,
]


@dataclass(kw_only=True, frozen=True)
class AppClientCompilationResult:
    """Result of compiling an application's TEAL code.

    Contains the compiled approval and clear state programs along with optional compilation artifacts.

    :ivar approval_program: The compiled approval program bytes
    :ivar clear_state_program: The compiled clear state program bytes
    :ivar compiled_approval: Optional compilation artifacts for approval program
    :ivar compiled_clear: Optional compilation artifacts for clear state program
    """

    approval_program: bytes
    clear_state_program: bytes
    compiled_approval: CompiledTeal | None = None
    compiled_clear: CompiledTeal | None = None


class AppClientCompilationParams(TypedDict, total=False):
    """Parameters for compiling an application's TEAL code.

    :ivar deploy_time_params: Optional template parameters to use during compilation
    :ivar updatable: Optional flag indicating if app should be updatable
    :ivar deletable: Optional flag indicating if app should be deletable
    """

    deploy_time_params: TealTemplateParams | None
    updatable: bool | None
    deletable: bool | None


@dataclass(kw_only=True)
class FundAppAccountParams:
    """Parameters for funding an application's account.

    :ivar sender: Optional sender address
    :ivar signer: Optional transaction signer
    :ivar rekey_to: Optional address to rekey to
    :ivar note: Optional transaction note
    :ivar lease: Optional lease
    :ivar static_fee: Optional static fee
    :ivar extra_fee: Optional extra fee
    :ivar max_fee: Optional maximum fee
    :ivar validity_window: Optional validity window in rounds
    :ivar first_valid_round: Optional first valid round
    :ivar last_valid_round: Optional last valid round
    :ivar amount: Amount to fund
    :ivar close_remainder_to: Optional address to close remainder to
    :ivar max_rounds_to_wait: Optional maximum rounds to wait
    :ivar suppress_log: Optional flag to suppress logging
    :ivar populate_app_call_resources: Optional flag to populate app call resources
    :ivar cover_app_call_inner_txn_fees: Optional flag to cover app call inner transaction fees
    :ivar on_complete: Optional on complete action
    """

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
    cover_app_call_inner_txn_fees: bool | None = None
    on_complete: algosdk.transaction.OnComplete | None = None


@dataclass(kw_only=True)
class AppClientCallParams:
    """Parameters for calling an application.

    :ivar method: Optional ABI method name or signature
    :ivar args: Optional arguments to pass to method
    :ivar boxes: Optional box references to load
    :ivar accounts: Optional account addresses to load
    :ivar apps: Optional app IDs to load
    :ivar assets: Optional asset IDs to load
    :ivar lease: Optional lease
    :ivar sender: Optional sender address
    :ivar note: Optional transaction note
    :ivar send_params: Optional parameters to control transaction sending
    """

    method: str | None = None
    args: list | None = None
    boxes: list | None = None
    accounts: list[str] | None = None
    apps: list[int] | None = None
    assets: list[int] | None = None
    lease: (str | bytes) | None = None
    sender: str | None = None
    note: (bytes | dict | str) | None = None
    send_params: dict | None = None


ArgsT = TypeVar("ArgsT")
MethodT = TypeVar("MethodT")


@dataclass(kw_only=True, frozen=True)
class BaseAppClientMethodCallParams(Generic[ArgsT, MethodT]):
    """Base parameters for application method calls.

    :ivar method: Method to call
    :ivar args: Optional arguments to pass to method
    :ivar account_references: Optional account references
    :ivar app_references: Optional application references
    :ivar asset_references: Optional asset references
    :ivar box_references: Optional box references
    :ivar extra_fee: Optional extra fee
    :ivar first_valid_round: Optional first valid round
    :ivar lease: Optional lease
    :ivar max_fee: Optional maximum fee
    :ivar note: Optional note
    :ivar rekey_to: Optional rekey to address
    :ivar sender: Optional sender address
    :ivar signer: Optional transaction signer
    :ivar static_fee: Optional static fee
    :ivar validity_window: Optional validity window
    :ivar last_valid_round: Optional last valid round
    :ivar on_complete: Optional on complete action
    """

    method: MethodT
    args: ArgsT | None = None
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
class AppClientMethodCallParams(
    BaseAppClientMethodCallParams[
        Sequence[ABIValue | ABIStruct | AppMethodCallTransactionArgument | None],
        str,
    ]
):
    """Parameters for application method calls."""


@dataclass(kw_only=True, frozen=True)
class AppClientBareCallParams:
    """Parameters for bare application calls.

    :ivar signer: Optional transaction signer
    :ivar rekey_to: Optional rekey to address
    :ivar lease: Optional lease
    :ivar static_fee: Optional static fee
    :ivar extra_fee: Optional extra fee
    :ivar max_fee: Optional maximum fee
    :ivar validity_window: Optional validity window
    :ivar first_valid_round: Optional first valid round
    :ivar last_valid_round: Optional last valid round
    :ivar sender: Optional sender address
    :ivar note: Optional note
    :ivar args: Optional arguments
    :ivar account_references: Optional account references
    :ivar app_references: Optional application references
    :ivar asset_references: Optional asset references
    :ivar box_references: Optional box references
    """

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


@dataclass(frozen=True)
class AppClientCreateSchema:
    """Schema for application creation.

    :ivar extra_program_pages: Optional number of extra program pages
    :ivar schema: Optional application creation schema
    """

    extra_program_pages: int | None = None
    schema: AppCreateSchema | None = None


@dataclass(frozen=True)
class AppClientBareCallCreateParams(AppClientCreateSchema, AppClientBareCallParams):
    """Parameters for creating application with bare call."""

    on_complete: OnComplete | None = None


@dataclass(frozen=True)
class AppClientMethodCallCreateParams(AppClientCreateSchema, AppClientMethodCallParams):
    """Parameters for creating application with method call."""

    on_complete: CreateOnComplete | None = None


class _AppClientStateMethods:
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


class _AppClientBoxMethods:
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


class _StateAccessor:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec

    def local_state(self, address: str) -> _AppClientStateMethods:
        """Methods to access local state for the current app for a given address"""
        return self._get_state_methods(
            state_getter=lambda: self._algorand.app.get_local_state(self._app_id, address),
            key_getter=lambda: self._app_spec.state.keys.local_state,
            map_getter=lambda: self._app_spec.state.maps.local_state,
        )

    @property
    def global_state(self) -> _AppClientStateMethods:
        """Methods to access global state for the current app"""
        return self._get_state_methods(
            state_getter=lambda: self._algorand.app.get_global_state(self._app_id),
            key_getter=lambda: self._app_spec.state.keys.global_state,
            map_getter=lambda: self._app_spec.state.maps.global_state,
        )

    @property
    def box(self) -> _AppClientBoxMethods:
        """Methods to access box storage for the current app"""
        return self._get_box_methods()

    def _get_box_methods(self) -> _AppClientBoxMethods:
        def get_all() -> dict[str, Any]:
            """Returns all single-key box values in a dict keyed by the key name."""
            return {key: get_value(key) for key in self._app_spec.state.keys.box}

        def get_value(name: str) -> ABIValue | None:
            """Returns a single box value for the current app with the value a decoded ABI value.

            :param name: The name of the box value to retrieve
            :return: The decoded ABI value from the box storage, or None if not found
            """
            metadata = self._app_spec.state.keys.box[name]
            value = self._algorand.app.get_box_value(self._app_id, base64.b64decode(metadata.key))
            return get_abi_decoded_value(value, metadata.value_type, self._app_spec.structs)

        def get_map_value(map_name: str, key: bytes | Any) -> Any:  # noqa: ANN401
            """Get a value from a box map.

            Retrieves a value from a box map storage using the provided map name and key.

            :param map_name: The name of the map to read from
            :param key: The key within the map (without any map prefix) as either bytes or a value
                     that will be converted to bytes by encoding it using the specified ABI key type
            :return: The decoded value from the box map storage
            """
            metadata = self._app_spec.state.maps.box[map_name]
            prefix = base64.b64decode(metadata.prefix or "")
            encoded_key = get_abi_encoded_value(key, metadata.key_type, self._app_spec.structs)
            full_key = base64.b64encode(prefix + encoded_key).decode("utf-8")
            value = self._algorand.app.get_box_value(self._app_id, base64.b64decode(full_key))
            return get_abi_decoded_value(value, metadata.value_type, self._app_spec.structs)

        def get_map(map_name: str) -> dict[str, ABIValue]:
            """Get all key-value pairs from a box map.

            Retrieves all key-value pairs stored in a box map for the current app.

            :param map_name: The name of the map to read from
            :return: A dictionary mapping string keys to their corresponding ABI-decoded values
            :raises ValueError: If there is an error decoding any key or value in the map
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
    ) -> _AppClientStateMethods:
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

            prefix = base64.b64decode(metadata.prefix or "")
            encoded_key = get_abi_encoded_value(key, metadata.key_type, self._app_spec.structs)
            full_key = base64.b64encode(prefix + encoded_key).decode("utf-8")
            value = next((s for s in state.values() if s.key_base64 == full_key), None)
            if value and value.value_raw:
                return get_abi_decoded_value(value.value_raw, metadata.value_type, self._app_spec.structs)
            return value.value if value else None

        def get_map(map_name: str) -> dict[str, ABIValue]:
            state = state_getter()
            metadata = map_getter()[map_name]

            prefix = base64.b64decode(metadata.prefix or "").decode("utf-8")

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


class _BareParamsBuilder:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec

    def _get_bare_params(
        self, params: dict[str, Any] | None, on_complete: algosdk.transaction.OnComplete | None = None
    ) -> dict[str, Any]:
        params = params or {}
        sender = self._client._get_sender(params.get("sender"))
        return {
            **params,
            "app_id": self._app_id,
            "sender": sender,
            "signer": self._client._get_signer(params.get("sender"), params.get("signer")),
            "on_complete": on_complete or OnComplete.NoOpOC,
        }

    def update(
        self,
        params: AppClientBareCallParams | None = None,
    ) -> AppUpdateParams:
        """Create parameters for updating an application.

        :param params: Optional compilation and send parameters, defaults to None
        :return: Parameters for updating the application
        """
        call_params: AppUpdateParams = AppUpdateParams(
            **self._get_bare_params(params.__dict__ if params else {}, OnComplete.UpdateApplicationOC)
        )
        return call_params

    def opt_in(self, params: AppClientBareCallParams | None = None) -> AppCallParams:
        """Create parameters for opting into an application.

        :param params: Optional send parameters, defaults to None
        :return: Parameters for opting into the application
        """
        call_params: AppCallParams = AppCallParams(
            **self._get_bare_params(params.__dict__ if params else {}, OnComplete.OptInOC)
        )
        return call_params

    def delete(self, params: AppClientBareCallParams | None = None) -> AppCallParams:
        """Create parameters for deleting an application.

        :param params: Optional send parameters, defaults to None
        :return: Parameters for deleting the application
        """
        call_params: AppCallParams = AppCallParams(
            **self._get_bare_params(params.__dict__ if params else {}, OnComplete.DeleteApplicationOC)
        )
        return call_params

    def clear_state(self, params: AppClientBareCallParams | None = None) -> AppCallParams:
        """Create parameters for clearing application state.

        :param params: Optional send parameters, defaults to None
        :return: Parameters for clearing application state
        """
        call_params: AppCallParams = AppCallParams(
            **self._get_bare_params(params.__dict__ if params else {}, OnComplete.ClearStateOC)
        )
        return call_params

    def close_out(self, params: AppClientBareCallParams | None = None) -> AppCallParams:
        """Create parameters for closing out of an application.

        :param params: Optional send parameters, defaults to None
        :return: Parameters for closing out of the application
        """
        call_params: AppCallParams = AppCallParams(
            **self._get_bare_params(params.__dict__ if params else {}, OnComplete.CloseOutOC)
        )
        return call_params

    def call(
        self, params: AppClientBareCallParams | None = None, on_complete: OnComplete | None = OnComplete.NoOpOC
    ) -> AppCallParams:
        """Create parameters for calling an application.

        :param params: Optional call parameters with on complete action, defaults to None
        :param on_complete: The OnComplete action, defaults to OnComplete.NoOpOC
        :return: Parameters for calling the application
        """
        call_params: AppCallParams = AppCallParams(
            **self._get_bare_params(params.__dict__ if params else {}, on_complete or OnComplete.NoOpOC)
        )
        return call_params


class _MethodParamsBuilder:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec
        self._bare_params_accessor = _BareParamsBuilder(client)

    @property
    def bare(self) -> _BareParamsBuilder:
        return self._bare_params_accessor

    def fund_app_account(self, params: FundAppAccountParams) -> PaymentParams:
        """Create parameters for funding an application account.

        :param params: Parameters for funding the application account
        :return: Parameters for sending a payment transaction to fund the application account
        """

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
        """Create parameters for opting into an application.

        :param params: Parameters for the opt-in call
        :return: Parameters for opting into the application
        """
        input_params = self._get_abi_params(
            params.__dict__, on_complete=params.on_complete or algosdk.transaction.OnComplete.OptInOC
        )
        return AppCallMethodCallParams(**input_params)

    def call(self, params: AppClientMethodCallParams) -> AppCallMethodCallParams:
        """Create parameters for calling an application method.

        :param params: Parameters for the method call
        :return: Parameters for calling the application method
        """
        input_params = self._get_abi_params(
            params.__dict__, on_complete=params.on_complete or algosdk.transaction.OnComplete.NoOpOC
        )
        return AppCallMethodCallParams(**input_params)

    def delete(self, params: AppClientMethodCallParams) -> AppDeleteMethodCallParams:
        """Create parameters for deleting an application.

        :param params: Parameters for the delete call
        :return: Parameters for deleting the application
        """
        input_params = self._get_abi_params(
            params.__dict__, on_complete=params.on_complete or algosdk.transaction.OnComplete.DeleteApplicationOC
        )
        return AppDeleteMethodCallParams(**input_params)

    def update(
        self, params: AppClientMethodCallParams, compilation_params: AppClientCompilationParams | None = None
    ) -> AppUpdateMethodCallParams:
        """Create parameters for updating an application.

        :param params: Parameters for the update call, optionally including compilation parameters
        :param compilation_params: Parameters for the compilation, defaults to None
        :return: Parameters for updating the application
        """
        compile_params = (
            self._client.compile(
                app_spec=self._client.app_spec,
                app_manager=self._algorand.app,
                deploy_time_params=compilation_params.get("deploy_time_params"),
                updatable=compilation_params.get("updatable"),
                deletable=compilation_params.get("deletable"),
            ).__dict__
            if compilation_params
            else {}
        )

        input_params = {
            **self._get_abi_params(
                params.__dict__, on_complete=params.on_complete or algosdk.transaction.OnComplete.UpdateApplicationOC
            ),
            **compile_params,
        }
        # Filter input_params to include only fields valid for AppUpdateMethodCallParams
        app_update_method_call_fields = {field.name for field in fields(AppUpdateMethodCallParams)}
        filtered_input_params = {k: v for k, v in input_params.items() if k in app_update_method_call_fields}
        return AppUpdateMethodCallParams(**filtered_input_params)

    def close_out(self, params: AppClientMethodCallParams) -> AppCallMethodCallParams:
        """Create parameters for closing out of an application.

        :param params: Parameters for the close-out call
        :return: Parameters for closing out of the application
        """
        input_params = self._get_abi_params(
            params.__dict__, on_complete=params.on_complete or algosdk.transaction.OnComplete.CloseOutOC
        )
        return AppCallMethodCallParams(**input_params)

    def _get_abi_params(self, params: dict[str, Any], on_complete: algosdk.transaction.OnComplete) -> dict[str, Any]:
        input_params = copy.deepcopy(params)

        input_params["app_id"] = self._app_id
        input_params["on_complete"] = on_complete
        input_params["sender"] = self._client._get_sender(params["sender"])
        input_params["signer"] = self._client._get_signer(params["sender"], params["signer"])

        if params.get("method"):
            input_params["method"] = self._app_spec.get_arc56_method(params["method"]).to_abi_method()
            input_params["args"] = self._client._get_abi_args_with_default_values(
                method_name_or_signature=params["method"],
                args=params.get("args"),
                sender=self._client._get_sender(input_params["sender"]),
            )

        return input_params


class _AppClientBareCallCreateTransactionMethods:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand

    def update(self, params: AppClientBareCallParams | None = None) -> Transaction:
        """Create a transaction to update an application.

        Creates a transaction that will update an existing application with new approval and clear state programs.

        :param params: Parameters for the update call including compilation and transaction options, defaults to None
        :return: The constructed application update transaction
        """
        return self._algorand.create_transaction.app_update(
            self._client.params.bare.update(params or AppClientBareCallParams())
        )

    def opt_in(self, params: AppClientBareCallParams | None = None) -> Transaction:
        """Create a transaction to opt into an application.

        Creates a transaction that will opt the sender account into using this application.

        :param params: Parameters for the opt-in call including transaction options, defaults to None
        :return: The constructed opt-in transaction
        """
        return self._algorand.create_transaction.app_call(
            self._client.params.bare.opt_in(params or AppClientBareCallParams())
        )

    def delete(self, params: AppClientBareCallParams | None = None) -> Transaction:
        """Create a transaction to delete an application.

        Creates a transaction that will delete this application from the blockchain.

        :param params: Parameters for the delete call including transaction options, defaults to None
        :return: The constructed delete transaction
        """
        return self._algorand.create_transaction.app_call(
            self._client.params.bare.delete(params or AppClientBareCallParams())
        )

    def clear_state(self, params: AppClientBareCallParams | None = None) -> Transaction:
        """Create a transaction to clear application state.

        Creates a transaction that will clear the sender's local state for this application.

        :param params: Parameters for the clear state call including transaction options, defaults to None
        :return: The constructed clear state transaction
        """
        return self._algorand.create_transaction.app_call(
            self._client.params.bare.clear_state(params or AppClientBareCallParams())
        )

    def close_out(self, params: AppClientBareCallParams | None = None) -> Transaction:
        """Create a transaction to close out of an application.

        Creates a transaction that will close out the sender's participation in this application.

        :param params: Parameters for the close out call including transaction options, defaults to None
        :return: The constructed close out transaction
        """
        return self._algorand.create_transaction.app_call(
            self._client.params.bare.close_out(params or AppClientBareCallParams())
        )

    def call(
        self, params: AppClientBareCallParams | None = None, on_complete: OnComplete | None = OnComplete.NoOpOC
    ) -> Transaction:
        """Create a transaction to call an application.

        Creates a transaction that will call this application with the specified parameters.

        :param params: Parameters for the application call including on complete action, defaults to None
        :param on_complete: The OnComplete action, defaults to OnComplete.NoOpOC
        :return: The constructed application call transaction
        """
        return self._algorand.create_transaction.app_call(
            self._client.params.bare.call(params or AppClientBareCallParams(), on_complete or OnComplete.NoOpOC)
        )


class _TransactionCreator:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec
        self._bare_create_transaction_methods = _AppClientBareCallCreateTransactionMethods(client)

    @property
    def bare(self) -> _AppClientBareCallCreateTransactionMethods:
        return self._bare_create_transaction_methods

    def fund_app_account(self, params: FundAppAccountParams) -> Transaction:
        """Create a transaction to fund an application account.

        Creates a payment transaction to fund the application account with the specified parameters.

        :param params: Parameters for funding the application account including amount and transaction options
        :return: The constructed payment transaction
        """
        return self._algorand.create_transaction.payment(self._client.params.fund_app_account(params))

    def opt_in(self, params: AppClientMethodCallParams) -> BuiltTransactions:
        """Create a transaction to opt into an application.

        Creates a transaction that will opt the sender into this application with the specified parameters.

        :param params: Parameters for the opt-in call including method arguments and transaction options
        :return: The constructed opt-in transaction(s)
        """
        return self._algorand.create_transaction.app_call_method_call(self._client.params.opt_in(params))

    def update(self, params: AppClientMethodCallParams) -> BuiltTransactions:
        """Create a transaction to update an application.

        Creates a transaction that will update this application with new approval and clear state programs.

        :param params: Parameters for the update call including method arguments and transaction options
        :return: The constructed update transaction(s)
        """
        return self._algorand.create_transaction.app_update_method_call(self._client.params.update(params))

    def delete(self, params: AppClientMethodCallParams) -> BuiltTransactions:
        """Create a transaction to delete an application.

        Creates a transaction that will delete this application.

        :param params: Parameters for the delete call including method arguments and transaction options
        :return: The constructed delete transaction(s)
        """
        return self._algorand.create_transaction.app_delete_method_call(self._client.params.delete(params))

    def close_out(self, params: AppClientMethodCallParams) -> BuiltTransactions:
        """Create a transaction to close out of an application.

        Creates a transaction that will close out the sender's participation in this application.

        :param params: Parameters for the close out call including method arguments and transaction options
        :return: The constructed close out transaction(s)
        """
        return self._algorand.create_transaction.app_call_method_call(self._client.params.close_out(params))

    def call(self, params: AppClientMethodCallParams) -> BuiltTransactions:
        """Create a transaction to call an application.

        Creates a transaction that will call this application with the specified parameters.

        :param params: Parameters for the application call including method arguments and transaction options
        :return: The constructed application call transaction(s)
        """
        return self._algorand.create_transaction.app_call_method_call(self._client.params.call(params))


class _AppClientBareSendAccessor:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec

    def update(
        self,
        params: AppClientBareCallParams | None = None,
        send_params: SendParams | None = None,
        compilation_params: AppClientCompilationParams | None = None,
    ) -> SendAppTransactionResult[ABIReturn]:
        """Send an application update transaction.

        Sends a transaction to update an existing application with new approval and clear state programs.

        :param params: The parameters for the update call, including optional compilation parameters,
        deploy time parameters, and transaction configuration
        :param send_params: Send parameters, defaults to None
        :param compilation_params: Parameters for the compilation, defaults to None
        :return: The result of sending the transaction, including compilation artifacts and ABI return
        value if applicable
        """
        params = params or AppClientBareCallParams()
        compilation = compilation_params or AppClientCompilationParams()
        compiled = self._client.compile_app(
            compilation.get("deploy_time_params"), compilation.get("updatable"), compilation.get("deletable")
        )
        bare_params = self._client.params.bare.update(params)
        bare_params.__setattr__("approval_program", bare_params.approval_program or compiled.compiled_approval)
        bare_params.__setattr__("clear_state_program", bare_params.clear_state_program or compiled.compiled_clear)
        call_result = self._client._handle_call_errors(lambda: self._algorand.send.app_update(bare_params, send_params))
        return SendAppTransactionResult[ABIReturn](
            **{**call_result.__dict__, **(compiled.__dict__ if compiled else {})},
            abi_return=AppManager.get_abi_return(call_result.confirmation, getattr(params, "method", None)),
        )

    def opt_in(
        self, params: AppClientBareCallParams | None = None, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[ABIReturn]:
        """Send an application opt-in transaction.

        Creates and sends a transaction that will opt the sender's account into this application.

        :param params: Parameters for the opt-in call including transaction options, defaults to None
        :param send_params: Send parameters, defaults to None
        :return: The result of sending the transaction, including ABI return value if applicable
        """
        return self._client._handle_call_errors(
            lambda: self._algorand.send.app_call(
                self._client.params.bare.opt_in(params or AppClientBareCallParams()), send_params
            )
        )

    def delete(
        self, params: AppClientBareCallParams | None = None, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[ABIReturn]:
        """Send an application delete transaction.

        Creates and sends a transaction that will delete this application.

        :param params: Parameters for the delete call including transaction options, defaults to None
        :param send_params: Send parameters, defaults to None
        :return: The result of sending the transaction, including ABI return value if applicable
        """
        return self._client._handle_call_errors(
            lambda: self._algorand.send.app_call(
                self._client.params.bare.delete(params or AppClientBareCallParams()), send_params
            )
        )

    def clear_state(
        self, params: AppClientBareCallParams | None = None, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[ABIReturn]:
        """Send an application clear state transaction.

        Creates and sends a transaction that will clear the sender's local state for this application.

        :param params: Parameters for the clear state call including transaction options, defaults to None
        :param send_params: Send parameters, defaults to None
        :return: The result of sending the transaction, including ABI return value if applicable
        """
        return self._client._handle_call_errors(
            lambda: self._algorand.send.app_call(
                self._client.params.bare.clear_state(params or AppClientBareCallParams()), send_params
            )
        )

    def close_out(
        self, params: AppClientBareCallParams | None = None, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[ABIReturn]:
        """Send an application close out transaction.

        Creates and sends a transaction that will close out the sender's participation in this application.

        :param params: Parameters for the close out call including transaction options, defaults to None
        :param send_params: Send parameters, defaults to None
        :return: The result of sending the transaction, including ABI return value if applicable
        """
        return self._client._handle_call_errors(
            lambda: self._algorand.send.app_call(
                self._client.params.bare.close_out(params or AppClientBareCallParams()), send_params
            )
        )

    def call(
        self,
        params: AppClientBareCallParams | None = None,
        on_complete: OnComplete | None = None,
        send_params: SendParams | None = None,
    ) -> SendAppTransactionResult[ABIReturn]:
        """Send an application call transaction.

        Creates and sends a transaction that will call this application with the specified parameters.

        :param params: Parameters for the application call including transaction options, defaults to None
        :param on_complete: The OnComplete action, defaults to None
        :param send_params: Send parameters, defaults to None
        :return: The result of sending the transaction, including ABI return value if applicable
        """
        return self._client._handle_call_errors(
            lambda: self._algorand.send.app_call(
                self._client.params.bare.call(params or AppClientBareCallParams(), on_complete), send_params
            )
        )


class _TransactionSender:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec
        self._bare_send_accessor = _AppClientBareSendAccessor(client)

    @property
    def bare(self) -> _AppClientBareSendAccessor:
        """Get accessor for bare application calls.

        :return: Accessor for making bare application calls without ABI encoding
        """
        return self._bare_send_accessor

    def fund_app_account(
        self, params: FundAppAccountParams, send_params: SendParams | None = None
    ) -> SendSingleTransactionResult:
        """Send funds to the application account.

        Creates and sends a payment transaction to fund the application account.

        :param params: Parameters for funding the app account including amount and transaction options
        :param send_params: Send parameters, defaults to None
        :return: The result of sending the payment transaction
        """
        return self._client._handle_call_errors(  # type: ignore[no-any-return]
            lambda: self._algorand.send.payment(self._client.params.fund_app_account(params), send_params)
        )

    def opt_in(
        self, params: AppClientMethodCallParams, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[Arc56ReturnValueType]:
        """Send an application opt-in transaction.

        Creates and sends a transaction that will opt the sender into this application.

        :param params: Parameters for the opt-in call including method and transaction options
        :param send_params: Send parameters, defaults to None
        :return: The result of sending the transaction, including ABI return value if applicable
        """
        return self._client._handle_call_errors(
            lambda: self._client._process_method_call_return(
                lambda: self._algorand.send.app_call_method_call(self._client.params.opt_in(params), send_params),
                self._app_spec.get_arc56_method(params.method),
            )
        )

    def delete(
        self, params: AppClientMethodCallParams, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[Arc56ReturnValueType]:
        """Send an application delete transaction.

        Creates and sends a transaction that will delete this application.

        :param params: Parameters for the delete call including method and transaction options
        :param send_params: Send parameters, defaults to None
        :return: The result of sending the transaction, including ABI return value if applicable
        """
        return self._client._handle_call_errors(
            lambda: self._client._process_method_call_return(
                lambda: self._algorand.send.app_delete_method_call(self._client.params.delete(params), send_params),
                self._app_spec.get_arc56_method(params.method),
            )
        )

    def update(
        self,
        params: AppClientMethodCallParams,
        compilation_params: AppClientCompilationParams | None = None,
        send_params: SendParams | None = None,
    ) -> SendAppUpdateTransactionResult[Arc56ReturnValueType]:
        """Send an application update transaction.

        Creates and sends a transaction that will update this application's program.

        :param params: Parameters for the update call including method, compilation and transaction options
        :param compilation_params: Parameters for the compilation, defaults to None
        :param send_params: Send parameters, defaults to None
        :return: The result of sending the transaction, including ABI return value if applicable
        """
        result = self._client._handle_call_errors(
            lambda: self._client._process_method_call_return(
                lambda: self._algorand.send.app_update_method_call(
                    self._client.params.update(params, compilation_params), send_params
                ),
                self._app_spec.get_arc56_method(params.method),
            )
        )
        assert isinstance(result, SendAppUpdateTransactionResult)
        return result

    def close_out(
        self, params: AppClientMethodCallParams, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[Arc56ReturnValueType]:
        """Send an application close out transaction.

        Creates and sends a transaction that will close out the sender's participation in this application.

        :param params: Parameters for the close out call including method and transaction options
        :param send_params: Send parameters, defaults to None
        :return: The result of sending the transaction, including ABI return value if applicable
        """
        return self._client._handle_call_errors(
            lambda: self._client._process_method_call_return(
                lambda: self._algorand.send.app_call_method_call(self._client.params.close_out(params), send_params),
                self._app_spec.get_arc56_method(params.method),
            )
        )

    def call(
        self, params: AppClientMethodCallParams, send_params: SendParams | None = None
    ) -> SendAppTransactionResult[Arc56ReturnValueType]:
        """Send an application call transaction.

        Creates and sends a transaction that will call this application with the specified parameters.
        For read-only calls, simulates the transaction instead of sending it.

        :param params: Parameters for the application call including method and transaction options
        :param send_params: Send parameters
        :return: The result of sending or simulating the transaction, including ABI return value if applicable
        """
        is_read_only_call = (
            params.on_complete == algosdk.transaction.OnComplete.NoOpOC or params.on_complete is None
        ) and self._app_spec.get_arc56_method(params.method).readonly

        if is_read_only_call:
            method_call_to_simulate = self._algorand.new_group().add_app_call_method_call(
                self._client.params.call(params)
            )
            send_params = send_params or SendParams()
            simulate_response = self._client._handle_call_errors(
                lambda: method_call_to_simulate.simulate(
                    allow_unnamed_resources=send_params.get("populate_app_call_resources") or True,
                    skip_signatures=True,
                    allow_more_logs=True,
                    allow_empty_signatures=True,
                    extra_opcode_budget=None,
                    exec_trace_config=None,
                    simulation_round=None,
                )
            )

            return SendAppTransactionResult[Arc56ReturnValueType](
                tx_ids=simulate_response.tx_ids,
                transactions=simulate_response.transactions,
                transaction=simulate_response.transactions[-1],
                confirmation=simulate_response.confirmations[-1] if simulate_response.confirmations else b"",
                confirmations=simulate_response.confirmations,
                group_id=simulate_response.group_id or "",
                returns=simulate_response.returns,
                abi_return=simulate_response.returns[-1].get_arc56_value(
                    self._app_spec.get_arc56_method(params.method), self._app_spec.structs
                ),
            )

        return self._client._handle_call_errors(
            lambda: self._client._process_method_call_return(
                lambda: self._algorand.send.app_call_method_call(self._client.params.call(params), send_params),
                self._app_spec.get_arc56_method(params.method),
            )
        )


@dataclass(kw_only=True, frozen=True)
class AppClientParams:
    """Full parameters for creating an app client"""

    app_spec: Arc56Contract | Arc32Contract | str
    algorand: AlgorandClient
    app_id: int
    app_name: str | None = None
    default_sender: str | bytes | None = None
    default_signer: TransactionSigner | None = None
    approval_source_map: SourceMap | None = None
    clear_source_map: SourceMap | None = None


class AppClient:
    """A client for interacting with an Algorand smart contract application.

    Provides a high-level interface for interacting with Algorand smart contracts, including
    methods for calling application methods, managing state, and handling transactions.

    :param params: Parameters for creating the app client
    """

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
        self._state_accessor = _StateAccessor(self)
        self._params_accessor = _MethodParamsBuilder(self)
        self._send_accessor = _TransactionSender(self)
        self._create_transaction_accessor = _TransactionCreator(self)

    @property
    def algorand(self) -> AlgorandClient:
        """Get the Algorand client instance.

        :return: The Algorand client used by this app client
        """
        return self._algorand

    @property
    def app_id(self) -> int:
        """Get the application ID.

        :return: The ID of the Algorand application
        """
        return self._app_id

    @property
    def app_address(self) -> str:
        """Get the application's Algorand address.

        :return: The Algorand address associated with this application
        """
        return self._app_address

    @property
    def app_name(self) -> str:
        """Get the application name.

        :return: The name of the application
        """
        return self._app_name

    @property
    def app_spec(self) -> Arc56Contract:
        """Get the application specification.

        :return: The ARC-56 contract specification for this application
        """
        return self._app_spec

    @property
    def state(self) -> _StateAccessor:
        """Get the state accessor.

        :return: The state accessor for this application
        """
        return self._state_accessor

    @property
    def params(self) -> _MethodParamsBuilder:
        """Get the method parameters builder.

        :return: The method parameters builder for this application
        """
        return self._params_accessor

    @property
    def send(self) -> _TransactionSender:
        """Get the transaction sender.

        :return: The transaction sender for this application
        """
        return self._send_accessor

    @property
    def create_transaction(self) -> _TransactionCreator:
        """Get the transaction creator.

        :return: The transaction creator for this application
        """
        return self._create_transaction_accessor

    @staticmethod
    def normalise_app_spec(app_spec: Arc56Contract | Arc32Contract | str) -> Arc56Contract:
        """Normalize an application specification to ARC-56 format.

        :param app_spec: The application specification to normalize
        :return: The normalized ARC-56 contract specification
        :raises ValueError: If the app spec format is invalid
        """
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
        algorand: AlgorandClient,
        app_name: str | None = None,
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
        """Create an AppClient instance from network information.

        :param app_spec: The application specification
        :param algorand: The Algorand client instance
        :param app_name: Optional application name
        :param default_sender: Optional default sender address
        :param default_signer: Optional default transaction signer
        :param approval_source_map: Optional approval program source map
        :param clear_source_map: Optional clear program source map
        :return: A new AppClient instance
        :raises Exception: If no app ID is found for the network
        """
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
        algorand: AlgorandClient,
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: AppLookup | None = None,
    ) -> AppClient:
        """Create an AppClient instance from creator address and application name.

        :param creator_address: The address of the application creator
        :param app_name: The name of the application
        :param app_spec: The application specification
        :param algorand: The Algorand client instance
        :param default_sender: Optional default sender address
        :param default_signer: Optional default transaction signer
        :param approval_source_map: Optional approval program source map
        :param clear_source_map: Optional clear program source map
        :param ignore_cache: Optional flag to ignore cache
        :param app_lookup_cache: Optional app lookup cache
        :return: A new AppClient instance
        :raises ValueError: If the app is not found for the creator and name
        """
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
        """Compile the application's TEAL code.

        :param app_spec: The application specification
        :param app_manager: The application manager instance
        :param deploy_time_params: Optional deployment time parameters
        :param updatable: Optional flag indicating if app is updatable
        :param deletable: Optional flag indicating if app is deletable
        :return: The compilation result
        :raises ValueError: If attempting to compile without source or byte code
        """

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

    def compile_app(
        self,
        deploy_time_params: TealTemplateParams | None = None,
        updatable: bool | None = None,
        deletable: bool | None = None,
    ) -> AppClientCompilationResult:
        """Compile the application's TEAL code.

        :param deploy_time_params: Optional deployment time parameters
        :param updatable: Optional flag indicating if app is updatable
        :param deletable: Optional flag indicating if app is deletable
        :return: The compilation result
        """
        result = AppClient.compile(self._app_spec, self._algorand.app, deploy_time_params, updatable, deletable)

        if result.compiled_approval:
            self._approval_source_map = result.compiled_approval.source_map
        if result.compiled_clear:
            self._clear_source_map = result.compiled_clear.source_map

        return result

    def clone(
        self,
        app_name: str | None = _MISSING,  # type: ignore[assignment]
        default_sender: str | bytes | None = _MISSING,  # type: ignore[assignment]
        default_signer: TransactionSigner | None = _MISSING,  # type: ignore[assignment]
        approval_source_map: SourceMap | None = _MISSING,  # type: ignore[assignment]
        clear_source_map: SourceMap | None = _MISSING,  # type: ignore[assignment]
    ) -> AppClient:
        """Create a cloned AppClient instance with optionally overridden parameters.

        :param app_name: Optional new application name
        :param default_sender: Optional new default sender
        :param default_signer: Optional new default signer
        :param approval_source_map: Optional new approval source map
        :param clear_source_map: Optional new clear source map
        :return: A new AppClient instance with the specified parameters
        """
        return AppClient(
            AppClientParams(
                app_id=self._app_id,
                algorand=self._algorand,
                app_spec=self._app_spec,
                app_name=self._app_name if app_name is _MISSING else app_name,
                default_sender=self._default_sender if default_sender is _MISSING else default_sender,
                default_signer=self._default_signer if default_signer is _MISSING else default_signer,
                approval_source_map=(
                    self._approval_source_map if approval_source_map is _MISSING else approval_source_map
                ),
                clear_source_map=(self._clear_source_map if clear_source_map is _MISSING else clear_source_map),
            )
        )

    def export_source_maps(self) -> AppSourceMaps:
        """Export the application's source maps.

        :return: The application's source maps
        :raises ValueError: If source maps haven't been loaded
        """
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
        """Import source maps for the application.

        :param source_maps: The source maps to import
        :raises ValueError: If source maps are invalid or missing
        """
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
        """Get local state for an account.

        :param address: The account address
        :return: The account's local state for this application
        """
        return self._state_accessor.get_local_state(address)

    def get_global_state(self) -> dict[str, AppState]:
        """Get the application's global state.

        :return: The application's global state
        """
        return self._state_accessor.get_global_state()

    def get_box_names(self) -> list[BoxName]:
        """Get all box names for the application.

        :return: List of box names
        """
        return self._algorand.app.get_box_names(self._app_id)

    def get_box_value(self, name: BoxIdentifier) -> bytes:
        """Get the value of a box.

        :param name: The box identifier
        :return: The box value as bytes
        """
        return self._algorand.app.get_box_value(self._app_id, name)

    def get_box_value_from_abi_type(self, name: BoxIdentifier, abi_type: ABIType) -> ABIValue:
        """Get a box value decoded according to an ABI type.

        :param name: The box identifier
        :param abi_type: The ABI type to decode as
        :return: The decoded box value
        """
        return self._algorand.app.get_box_value_from_abi_type(self._app_id, name, abi_type)

    def get_box_values(self, filter_func: Callable[[BoxName], bool] | None = None) -> list[BoxValue]:
        """Get values for multiple boxes.

        :param filter_func: Optional function to filter box names
        :return: List of box values
        """
        names = [n for n in self.get_box_names() if not filter_func or filter_func(n)]
        values = self._algorand.app.get_box_values(self.app_id, [n.name_raw for n in names])
        return [BoxValue(name=n, value=v) for n, v in zip(names, values, strict=False)]

    def get_box_values_from_abi_type(
        self, abi_type: ABIType, filter_func: Callable[[BoxName], bool] | None = None
    ) -> list[BoxABIValue]:
        """Get multiple box values decoded according to an ABI type.

        :param abi_type: The ABI type to decode as
        :param filter_func: Optional function to filter box names
        :return: List of decoded box values
        """
        names = self.get_box_names()
        if filter_func:
            names = [name for name in names if filter_func(name)]

        values = self._algorand.app.get_box_values_from_abi_type(
            self.app_id, [name.name_raw for name in names], abi_type
        )

        return [BoxABIValue(name=name, value=values[i]) for i, name in enumerate(names)]

    def fund_app_account(
        self, params: FundAppAccountParams, send_params: SendParams | None = None
    ) -> SendSingleTransactionResult:
        """Fund the application's account.

        :param params: The funding parameters
        :param send_params: Send parameters, defaults to None
        :return: The transaction result
        """
        return self.send.fund_app_account(params, send_params)

    def _expose_logic_error(self, e: Exception, *, is_clear_state_program: bool = False) -> Exception:
        source_info = None
        if hasattr(self._app_spec, "source_info") and self._app_spec.source_info:
            source_info = (
                self._app_spec.source_info.clear if is_clear_state_program else self._app_spec.source_info.approval
            )

        pc_offset_method = source_info.pc_offset_method if source_info else None

        program: bytes | None = None
        if pc_offset_method == "cblocks":
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
        return signer or (self._default_signer if not sender or sender == self._default_sender else None)

    def _get_bare_params(self, params: dict[str, Any], on_complete: algosdk.transaction.OnComplete) -> dict[str, Any]:
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
        method = self._app_spec.get_arc56_method(method_name_or_signature)
        result: list[ABIValue | ABIStruct | AppMethodCallTransactionArgument | None] = []

        for i, method_arg in enumerate(method.args):
            arg_value = args[i] if args and i < len(args) else None

            if arg_value is not None:
                if method_arg.struct and isinstance(arg_value, dict):
                    arg_value = get_abi_tuple_from_abi_struct(
                        arg_value, self._app_spec.structs[method_arg.struct], self._app_spec.structs
                    )
                result.append(arg_value)
                continue

            default_value = method_arg.default_value
            if default_value:
                match default_value.source:
                    case "literal":
                        value_raw = base64.b64decode(default_value.data)
                        value_type = default_value.type or method_arg.type
                        result.append(get_abi_decoded_value(value_raw, value_type, self._app_spec.structs))

                    case "method":
                        default_method = self._app_spec.get_arc56_method(default_value.data)
                        empty_args = [None] * len(default_method.args)
                        call_result = self.send.call(
                            AppClientMethodCallParams(
                                method=default_value.data,
                                args=empty_args,
                                sender=sender,
                            )
                        )

                        if not call_result.abi_return:
                            raise ValueError("Default value method call did not return a value")

                        if isinstance(call_result.abi_return, dict):
                            result.append(
                                get_abi_tuple_from_abi_struct(
                                    call_result.abi_return,
                                    self._app_spec.structs[str(default_method.returns.struct)],
                                    self._app_spec.structs,
                                )
                            )
                        elif call_result.abi_return:
                            result.append(call_result.abi_return)

                    case "local" | "global":
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
                        box_name = base64.b64decode(default_value.data)
                        box_value = self._algorand.app.get_box_value(self._app_id, box_name)
                        value_type = default_value.type or method_arg.type
                        result.append(get_abi_decoded_value(box_value, value_type, self._app_spec.structs))

            elif not algosdk.abi.is_abi_transaction_type(method_arg.type):
                raise ValueError(
                    f"No value provided for required argument "
                    f"{method_arg.name or f'arg{i+1}'} in call to method {method.name}"
                )
            elif arg_value is None and default_value is None:
                # At this point only allow explicit None values if no default value was identified
                result.append(None)

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

    def _process_method_call_return(
        self,
        result: Callable[[], SendAppUpdateTransactionResult[ABIReturn] | SendAppTransactionResult[ABIReturn]],
        method: Method,
    ) -> SendAppUpdateTransactionResult[Arc56ReturnValueType] | SendAppTransactionResult[Arc56ReturnValueType]:
        result_value = result()
        abi_return = (
            result_value.abi_return.get_arc56_value(method, self._app_spec.structs)
            if isinstance(result_value.abi_return, ABIReturn)
            else None
        )

        if isinstance(result_value, SendAppUpdateTransactionResult):
            return SendAppUpdateTransactionResult[Arc56ReturnValueType](
                **{**result_value.__dict__, "abi_return": abi_return}
            )
        return SendAppTransactionResult[Arc56ReturnValueType](**{**result_value.__dict__, "abi_return": abi_return})
