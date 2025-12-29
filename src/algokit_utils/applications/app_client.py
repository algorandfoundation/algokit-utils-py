import base64
import copy
import json
import os
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, fields, replace
from typing import TYPE_CHECKING, Any, Generic, Literal, TypedDict, TypeVar

from typing_extensions import assert_never

from algokit_abi import abi, arc32, arc56
from algokit_common import ProgramSourceMap, get_application_address
from algokit_transact.models.common import OnApplicationComplete
from algokit_transact.models.transaction import Transaction
from algokit_transact.signer import AddressWithTransactionSigner
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
)
from algokit_utils.config import config
from algokit_utils.errors.logic_error import LogicError, parse_logic_error
from algokit_utils.models.amount import AlgoAmount
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
    SendTransactionComposerResults,
)
from algokit_utils.transactions.transaction_sender import (
    SendAppTransactionResult,
    SendAppUpdateTransactionResult,
    SendSingleTransactionResult,
)

if TYPE_CHECKING:
    from algokit_utils.algorand import AlgorandClient
    from algokit_utils.applications.app_deployer import ApplicationLookup
    from algokit_utils.applications.app_manager import AppManager
    from algokit_utils.models.state import BoxIdentifier, BoxReference, TealTemplateParams
    from algokit_utils.protocols.signer import TransactionSigner
else:
    AlgorandClient = ApplicationLookup = AppManager = TransactionSigner = Any  # type: ignore[assignment]
    BoxIdentifier = BoxReference = TealTemplateParams = Any  # type: ignore[assignment]

__all__ = [
    "AppClient",
    "AppClientBareCallCreateParams",
    "AppClientBareCallParams",
    "AppClientCompilationParams",
    "AppClientCompilationResult",
    "AppClientCreateSchema",
    "AppClientMethodCallCreateParams",
    "AppClientMethodCallParams",
    "AppClientParams",
    "AppSourceMaps",
    "BaseAppClientMethodCallParams",
    "CommonAppCallCreateParams",
    "CommonAppCallParams",
    "CreateOnComplete",
    "FundAppAccountParams",
    "get_constant_block_offset",
]

# TEAL opcodes for constant blocks
BYTE_CBLOCK = 38  # bytecblock opcode
INT_CBLOCK = 32  # intcblock opcode
MAX_SIMULATE_OPCODE_BUDGET = (
    20_000 * 16
)  # https://github.com/algorand/go-algorand/blob/807b29a91c371d225e12b9287c5d56e9b33c4e4c/ledger/simulation/trace.go#L104

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
    OnApplicationComplete.NoOp,
    OnApplicationComplete.UpdateApplication,
    OnApplicationComplete.DeleteApplication,
    OnApplicationComplete.OptIn,
    OnApplicationComplete.CloseOut,
]


@dataclass(kw_only=True, frozen=True)
class AppClientCompilationResult:
    """Result of compiling an application's TEAL code.

    Contains the compiled approval and clear state programs along with optional compilation artifacts.
    """

    approval_program: bytes
    """The compiled approval program bytes"""
    clear_state_program: bytes
    """The compiled clear state program bytes"""
    compiled_approval: CompiledTeal | None = None
    """Optional compilation artifacts for approval program"""
    compiled_clear: CompiledTeal | None = None
    """Optional compilation artifacts for clear state program"""


class AppClientCompilationParams(TypedDict, total=False):
    """Parameters for compiling an application's TEAL code.

    :ivar deploy_time_params: Optional template parameters to use during compilation
    :ivar updatable: Optional flag indicating if app should be updatable
    :ivar deletable: Optional flag indicating if app should be deletable
    """

    deploy_time_params: TealTemplateParams | None
    updatable: bool | None
    deletable: bool | None


ArgsT = TypeVar("ArgsT")
MethodT = TypeVar("MethodT")


@dataclass(kw_only=True, frozen=True)
class CommonAppCallParams:
    """Common configuration for app call transaction parameters"""

    account_references: list[str] | None = None
    """List of account addresses to reference"""
    app_references: list[int] | None = None
    """List of app IDs to reference"""
    asset_references: list[int] | None = None
    """List of asset IDs to reference"""
    box_references: list[BoxReference | BoxIdentifier] | None = None
    """List of box references to include"""
    extra_fee: AlgoAmount | None = None
    """Additional fee to add to transaction"""
    lease: bytes | None = None
    """Transaction lease value"""
    max_fee: AlgoAmount | None = None
    """Maximum fee allowed for transaction"""
    note: bytes | None = None
    """Custom note for the transaction"""
    rekey_to: str | None = None
    """Address to rekey account to"""
    sender: str | None = None
    """Sender address override"""
    signer: TransactionSigner | None = None
    """Custom transaction signer"""
    static_fee: AlgoAmount | None = None
    """Fixed fee for transaction"""
    validity_window: int | None = None
    """Number of rounds valid"""
    first_valid_round: int | None = None
    """First valid round number"""
    last_valid_round: int | None = None
    """Last valid round number"""
    on_complete: OnApplicationComplete | None = None
    """Optional on complete action"""


@dataclass(frozen=True)
class AppClientCreateSchema:
    """Schema for application creation."""

    extra_program_pages: int | None = None
    """Optional number of extra program pages"""
    schema: AppCreateSchema | None = None
    """Optional application creation schema"""


@dataclass(kw_only=True, frozen=True)
class CommonAppCallCreateParams(AppClientCreateSchema, CommonAppCallParams):
    """Common configuration for app create call transaction parameters."""

    on_complete: CreateOnComplete | None = None
    """Optional on complete action"""


@dataclass(kw_only=True, frozen=True)
class FundAppAccountParams(CommonAppCallParams):
    """Parameters for funding an application's account."""

    amount: AlgoAmount
    """Amount to fund"""
    close_remainder_to: str | None = None
    """Optional address to close remainder to"""


@dataclass(kw_only=True, frozen=True)
class AppClientBareCallParams(CommonAppCallParams):
    """Parameters for bare application calls."""

    args: list[bytes] | None = None
    """Optional arguments"""


@dataclass(frozen=True)
class AppClientBareCallCreateParams(CommonAppCallCreateParams):
    """Parameters for creating application with bare call."""

    args: list[bytes] | None = None
    """Optional arguments"""
    on_complete: CreateOnComplete | None = None
    """Optional on complete action"""


@dataclass(kw_only=True, frozen=True)
class BaseAppClientMethodCallParams(Generic[ArgsT, MethodT], CommonAppCallParams):
    """Base parameters for application method calls."""

    method: MethodT
    """Method to call"""
    args: ArgsT | None = None
    """Arguments to pass to the application method call"""


@dataclass(kw_only=True, frozen=True)
class AppClientMethodCallParams(
    BaseAppClientMethodCallParams[
        Sequence[ABIValue | ABIStruct | AppMethodCallTransactionArgument | None],
        str,
    ]
):
    """Parameters for application method calls."""


@dataclass(frozen=True)
class AppClientMethodCallCreateParams(AppClientCreateSchema, AppClientMethodCallParams):
    """Parameters for creating application with method call"""

    on_complete: CreateOnComplete | None = None
    """Optional on complete action"""


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
    def __init__(self, client: "AppClient") -> None:
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
            return get_abi_decoded_value(value, metadata.value_type)

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
            encoded_key = get_abi_encoded_value(key, metadata.key_type)
            full_key = base64.b64encode(prefix + encoded_key).decode("utf-8")
            value = self._algorand.app.get_box_value(self._app_id, base64.b64decode(full_key))
            return get_abi_decoded_value(value, metadata.value_type)

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

                try:
                    key = get_abi_decoded_value(box.name_raw[len(prefix) :], metadata.key_type)
                    value = get_abi_decoded_value(
                        self._algorand.app.get_box_value(self._app_id, box.name_raw),
                        metadata.value_type,
                    )
                    result[str(key)] = value
                except Exception as e:
                    raise ValueError(f"Failed to decode value for key {box.name_raw.decode('utf-8')}") from e

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
        key_getter: Callable[[], dict[str, arc56.StorageKey]],
        map_getter: Callable[[], dict[str, arc56.StorageMap]],
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
                return get_abi_decoded_value(value.value_raw, key_info.value_type)

            return value.value if value else None

        def get_map_value(map_name: str, key: bytes | Any, app_state: dict[str, AppState] | None = None) -> Any:  # noqa: ANN401
            state = app_state or state_getter()
            metadata = map_getter()[map_name]

            prefix = base64.b64decode(metadata.prefix or "")
            encoded_key = get_abi_encoded_value(key, metadata.key_type)
            full_key = base64.b64encode(prefix + encoded_key).decode("utf-8")
            value = next((s for s in state.values() if s.key_base64 == full_key), None)
            if value and value.value_raw:
                return get_abi_decoded_value(value.value_raw, metadata.value_type)
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
                    decoded_key = get_abi_decoded_value(key_bytes, metadata.key_type)
                except Exception as e:
                    raise ValueError(f"Failed to decode key {key_encoded}") from e

                try:
                    if value and value.value_raw:
                        decoded_value = get_abi_decoded_value(value.value_raw, metadata.value_type)
                    else:
                        decoded_value = get_abi_decoded_value(value.value, metadata.value_type)
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
    def __init__(self, client: "AppClient") -> None:
        self._client = client
        self._algorand = client._algorand
        self._app_id = client._app_id
        self._app_spec = client._app_spec

    def _get_bare_params(
        self, params: dict[str, Any] | None, on_complete: OnApplicationComplete | None = None
    ) -> dict[str, Any]:
        params = params or {}
        sender = self._client._get_sender(params.get("sender"))
        return {
            **params,
            "app_id": self._app_id,
            "sender": sender,
            "signer": self._client._get_signer(params.get("sender"), params.get("signer")),
            "on_complete": on_complete or OnApplicationComplete.NoOp,
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
            **self._get_bare_params(params.__dict__ if params else {}, OnApplicationComplete.UpdateApplication)
        )
        return call_params

    def opt_in(self, params: AppClientBareCallParams | None = None) -> AppCallParams:
        """Create parameters for opting into an application.

        :param params: Optional send parameters, defaults to None
        :return: Parameters for opting into the application
        """
        call_params: AppCallParams = AppCallParams(
            **self._get_bare_params(params.__dict__ if params else {}, OnApplicationComplete.OptIn)
        )
        return call_params

    def delete(self, params: AppClientBareCallParams | None = None) -> AppCallParams:
        """Create parameters for deleting an application.

        :param params: Optional send parameters, defaults to None
        :return: Parameters for deleting the application
        """
        call_params: AppCallParams = AppCallParams(
            **self._get_bare_params(params.__dict__ if params else {}, OnApplicationComplete.DeleteApplication)
        )
        return call_params

    def clear_state(self, params: AppClientBareCallParams | None = None) -> AppCallParams:
        """Create parameters for clearing application state.

        :param params: Optional send parameters, defaults to None
        :return: Parameters for clearing application state
        """
        call_params: AppCallParams = AppCallParams(
            **self._get_bare_params(params.__dict__ if params else {}, OnApplicationComplete.ClearState)
        )
        return call_params

    def close_out(self, params: AppClientBareCallParams | None = None) -> AppCallParams:
        """Create parameters for closing out of an application.

        :param params: Optional send parameters, defaults to None
        :return: Parameters for closing out of the application
        """
        call_params: AppCallParams = AppCallParams(
            **self._get_bare_params(params.__dict__ if params else {}, OnApplicationComplete.CloseOut)
        )
        return call_params

    def call(
        self,
        params: AppClientBareCallParams | None = None,
        on_complete: OnApplicationComplete | None = OnApplicationComplete.NoOp,
    ) -> AppCallParams:
        """Create parameters for calling an application.

        :param params: Optional call parameters with on complete action, defaults to None
        :param on_complete: The OnApplicationComplete action, defaults to OnApplicationComplete.NoOp
        :return: Parameters for calling the application
        """
        call_params: AppCallParams = AppCallParams(
            **self._get_bare_params(params.__dict__ if params else {}, on_complete or OnApplicationComplete.NoOp)
        )
        return call_params


class _MethodParamsBuilder:
    def __init__(self, client: "AppClient") -> None:
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
            params.__dict__, on_complete=params.on_complete or OnApplicationComplete.OptIn
        )
        return AppCallMethodCallParams(**input_params)

    def call(self, params: AppClientMethodCallParams) -> AppCallMethodCallParams:
        """Create parameters for calling an application method.

        :param params: Parameters for the method call
        :return: Parameters for calling the application method
        """
        input_params = self._get_abi_params(
            params.__dict__, on_complete=params.on_complete or OnApplicationComplete.NoOp
        )
        return AppCallMethodCallParams(**input_params)

    def delete(self, params: AppClientMethodCallParams) -> AppDeleteMethodCallParams:
        """Create parameters for deleting an application.

        :param params: Parameters for the delete call
        :return: Parameters for deleting the application
        """
        input_params = self._get_abi_params(
            params.__dict__, on_complete=params.on_complete or OnApplicationComplete.DeleteApplication
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
        compile_params = asdict(
            self._client.compile(
                app_spec=self._client.app_spec,
                app_manager=self._algorand.app,
                compilation_params=compilation_params,
            )
        )

        input_params = {
            **self._get_abi_params(
                params.__dict__, on_complete=params.on_complete or OnApplicationComplete.UpdateApplication
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
            params.__dict__, on_complete=params.on_complete or OnApplicationComplete.CloseOut
        )
        return AppCallMethodCallParams(**input_params)

    def _get_abi_params(self, params: dict[str, Any], on_complete: OnApplicationComplete) -> dict[str, Any]:
        input_params = copy.deepcopy(params)

        input_params["app_id"] = self._app_id
        input_params["on_complete"] = on_complete
        input_params["sender"] = self._client._get_sender(params["sender"])
        input_params["signer"] = self._client._get_signer(params["sender"], params["signer"])

        if params.get("method"):
            input_params["method"] = self._app_spec.get_abi_method(params["method"])
            input_params["args"] = self._client._get_abi_args_with_default_values(
                method_name_or_signature=params["method"],
                args=params.get("args"),
                sender=self._client._get_sender(input_params["sender"]),
            )

        return input_params


class _AppClientBareCallCreateTransactionMethods:
    def __init__(self, client: "AppClient") -> None:
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
        self,
        params: AppClientBareCallParams | None = None,
        on_complete: OnApplicationComplete | None = OnApplicationComplete.NoOp,
    ) -> Transaction:
        """Create a transaction to call an application.

        Creates a transaction that will call this application with the specified parameters.

        :param params: Parameters for the application call including on complete action, defaults to None
        :param on_complete: The OnApplicationComplete action, defaults to OnApplicationComplete.NoOp
        :return: The constructed application call transaction
        """
        return self._algorand.create_transaction.app_call(
            self._client.params.bare.call(
                params or AppClientBareCallParams(), on_complete or OnApplicationComplete.NoOp
            )
        )


class _TransactionCreator:
    def __init__(self, client: "AppClient") -> None:
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
    def __init__(self, client: "AppClient") -> None:
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
            {
                "deploy_time_params": compilation.get("deploy_time_params"),
                "updatable": compilation.get("updatable"),
                "deletable": compilation.get("deletable"),
            }
        )
        bare_call_params = self._client.params.bare.call(params, on_complete=OnApplicationComplete.UpdateApplication)
        bare_update_params = AppUpdateParams(
            **bare_call_params.__dict__,
            approval_program=compiled.approval_program,
            clear_state_program=compiled.clear_state_program,
        )
        return self._client._handle_call_errors(lambda: self._algorand.send.app_update(bare_update_params, send_params))

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
        on_complete: OnApplicationComplete | None = None,
        send_params: SendParams | None = None,
    ) -> SendAppTransactionResult[ABIReturn]:
        """Send an application call transaction.

        Creates and sends a transaction that will call this application with the specified parameters.

        :param params: Parameters for the application call including transaction options, defaults to None
        :param on_complete: The OnApplicationComplete action, defaults to None
        :param send_params: Send parameters, defaults to None
        :return: The result of sending the transaction, including ABI return value if applicable
        """
        return self._client._handle_call_errors(
            lambda: self._algorand.send.app_call(
                self._client.params.bare.call(params or AppClientBareCallParams(), on_complete), send_params
            )
        )


class _TransactionSender:
    def __init__(self, client: "AppClient") -> None:
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
                self._app_spec.get_abi_method(params.method),
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
                self._app_spec.get_abi_method(params.method),
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
                self._app_spec.get_abi_method(params.method),
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
                self._app_spec.get_abi_method(params.method),
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
            params.on_complete == OnApplicationComplete.NoOp or params.on_complete is None
        ) and self._app_spec.get_abi_method(params.method).readonly

        if is_read_only_call:
            readonly_params = params
            readonly_send_params = send_params or SendParams()
            reported_fee = (
                params.static_fee.micro_algo if params.static_fee else self._algorand.get_suggested_params().min_fee
            )
            reset_reported_fee = False

            # Read-only calls do not require fees to be paid, as they are only simulated on the network.
            # With maximum opcode budget provided, ensure_budget won't create inner transactions,
            # so fee coverage is no longer a concern for read-only calls.
            # If max_fee is provided, use it as static_fee for potential benefits.
            if readonly_send_params.get("cover_app_call_inner_transaction_fees") and params.max_fee is not None:
                readonly_params = replace(readonly_params, static_fee=params.max_fee, extra_fee=None)
            elif readonly_params.static_fee is None:
                fallback_fee = params.max_fee or AlgoAmount.from_micro_algo(MAX_SIMULATE_OPCODE_BUDGET)
                readonly_params = replace(readonly_params, static_fee=fallback_fee, extra_fee=None)
                reset_reported_fee = True

            method_call_to_simulate = self._algorand.new_group().add_app_call_method_call(
                self._client.params.call(readonly_params)
            )

            def run_simulate() -> SendTransactionComposerResults:
                try:
                    return method_call_to_simulate.simulate(
                        allow_unnamed_resources=readonly_send_params.get("populate_app_call_resources") or True,
                        skip_signatures=True,
                        allow_more_logs=True,
                        allow_empty_signatures=True,
                        extra_opcode_budget=MAX_SIMULATE_OPCODE_BUDGET,
                        exec_trace_config=None,
                        simulation_round=None,
                    )
                except Exception as e:
                    # For read-only calls with max opcode budget, fee issues should be rare
                    # but we can still provide helpful error message if they occur
                    if readonly_send_params.get("cover_app_call_inner_transaction_fees") and "fee too small" in str(e):
                        raise ValueError(
                            "Fees were too small. You may need to increase the transaction `maxFee`."
                        ) from e
                    raise

            simulate_response = self._client._handle_call_errors(run_simulate)

            wrapped_transactions = simulate_response.transactions
            if reset_reported_fee:
                wrapped_transactions = [replace(txn, fee=reported_fee) for txn in wrapped_transactions]
            return SendAppTransactionResult[Arc56ReturnValueType](
                tx_ids=simulate_response.tx_ids,
                transactions=wrapped_transactions,
                transaction=wrapped_transactions[-1],
                confirmation=simulate_response.confirmations[-1],
                confirmations=simulate_response.confirmations,
                group_id=simulate_response.group_id or "",
                returns=simulate_response.returns,
                abi_return=simulate_response.returns[-1].value,
            )

        return self._client._handle_call_errors(
            lambda: self._client._process_method_call_return(
                lambda: self._algorand.send.app_call_method_call(self._client.params.call(params), send_params),
                self._app_spec.get_abi_method(params.method),
            )
        )


@dataclass(kw_only=True, frozen=True)
class AppClientParams:
    """Full parameters for creating an app client"""

    app_spec: arc56.Arc56Contract | arc32.Arc32Contract | str
    """The application specification"""
    algorand: AlgorandClient
    """The Algorand client"""
    app_id: int
    """The application ID"""
    app_name: str | None = None
    """The application name"""
    default_sender: str | None = None
    """The default sender address"""
    default_signer: TransactionSigner | None = None
    """The default transaction signer"""
    approval_source_map: ProgramSourceMap | None = None
    """The approval source map"""
    clear_source_map: ProgramSourceMap | None = None
    """The clear source map"""


class AppClient:
    """A client for interacting with an Algorand smart contract application.

    Provides a high-level interface for interacting with Algorand smart contracts, including
    methods for calling application methods, managing state, and handling transactions.

    :param params: Parameters for creating the app client

    :example:
        >>> params = AppClientParams(
        ...     app_spec=Arc56Contract.from_json(app_spec_json),
        ...     algorand=algorand,
        ...     app_id=1234567890,
        ...     app_name="My App",
        ...     default_sender="SENDERADDRESS",
        ...     default_signer=TransactionSigner(
        ...         account="SIGNERACCOUNT",
        ...         private_key="SIGNERPRIVATEKEY",
        ...     ),
        ...     approval_source_map=ProgramSourceMap(
        ...         source="APPROVALSOURCE",
        ...     ),
        ...     clear_source_map=ProgramSourceMap(
        ...         source="CLEARSOURCE",
        ...     ),
        ... )
        >>> client = AppClient(params)
    """

    def __init__(self, params: AppClientParams) -> None:
        self._app_id = params.app_id
        self._app_spec = self.normalise_app_spec(params.app_spec)
        self._algorand = params.algorand
        self._app_address = get_application_address(self._app_id)
        self._app_name = params.app_name or self._app_spec.name
        self._default_sender = params.default_sender
        self._default_signer = params.default_signer
        self._approval_source_map = params.approval_source_map
        self._clear_source_map = params.clear_source_map
        self._last_compiled: dict[str, bytes] = {}  # Track compiled programs for error filtering
        self._state_accessor = _StateAccessor(self)
        self._params_accessor = _MethodParamsBuilder(self)
        self._send_accessor = _TransactionSender(self)
        self._create_transaction_accessor = _TransactionCreator(self)

        # Register the error transformer to handle app-specific logic errors
        self._algorand.register_error_transformer(self._handle_call_errors_transform)

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
    def app_spec(self) -> arc56.Arc56Contract:
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

        :example:
            >>> # Create a transaction in the future using Algorand Client
            >>> my_method_call = app_client.params.call(AppClientMethodCallParams(
                    method='my_method',
                    args=[123, 'hello']))
            >>> # ...
            >>> await algorand.send.AppMethodCall(my_method_call)
            >>> # Define a nested transaction as an ABI argument
            >>> my_method_call = app_client.params.call(AppClientMethodCallParams(
                    method='my_method',
                    args=[123, 'hello']))
            >>> app_client.send.call(AppClientMethodCallParams(method='my_method2', args=[my_method_call]))
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
    def normalise_app_spec(app_spec: arc56.Arc56Contract | arc32.Arc32Contract | str) -> arc56.Arc56Contract:
        """Normalize an application specification to ARC-56 format.

        :param app_spec: The application specification to normalize. Can be raw arc32 or arc56 json,
            or an Arc32Contract or Arc56Contract instance
        :return: The normalized ARC-56 contract specification
        :raises ValueError: If the app spec format is invalid

        :example:
            >>> spec = AppClient.normalise_app_spec(app_spec_json)
        """
        if isinstance(app_spec, str):
            spec_dict = json.loads(app_spec)
            spec = arc32.Arc32Contract.from_json(app_spec) if "hints" in spec_dict else spec_dict
        else:
            spec = app_spec

        match spec:
            case arc56.Arc56Contract():
                return spec
            case arc32.Arc32Contract():
                from algokit_abi import arc32_to_arc56

                return arc32_to_arc56(spec.to_json())
            case dict():
                return arc56.Arc56Contract.from_dict(spec)
            case _:
                raise ValueError("Invalid app spec format")

    @staticmethod
    def from_network(
        app_spec: arc56.Arc56Contract | arc32.Arc32Contract | str,
        algorand: AlgorandClient,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: ProgramSourceMap | None = None,
        clear_source_map: ProgramSourceMap | None = None,
    ) -> "AppClient":
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

        :example:
            >>> client = AppClient.from_network(
            ...     app_spec=Arc56Contract.from_json(app_spec_json),
            ...     algorand=algorand,
            ...     app_name="My App",
            ...     default_sender="SENDERADDRESS",
            ...     default_signer=TransactionSigner(
            ...         account="SIGNERACCOUNT",
            ...         private_key="SIGNERPRIVATEKEY",
            ...     ),
            ...     approval_source_map=ProgramSourceMap(
            ...         source="APPROVALSOURCE",
            ...     ),
            ...     clear_source_map=ProgramSourceMap(
            ...         source="CLEARSOURCE",
            ...     ),
            ... )
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
        app_spec: arc56.Arc56Contract | arc32.Arc32Contract | str,
        algorand: AlgorandClient,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: ProgramSourceMap | None = None,
        clear_source_map: ProgramSourceMap | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: ApplicationLookup | None = None,
    ) -> "AppClient":
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

        :example:
            >>> client = AppClient.from_creator_and_name(
            ...     creator_address="CREATORADDRESS",
            ...     app_name="APPNAME",
            ...     app_spec=Arc56Contract.from_json(app_spec_json),
            ...     algorand=algorand,
            ... )
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
        app_spec: arc56.Arc56Contract,
        app_manager: AppManager,
        compilation_params: AppClientCompilationParams | None = None,
    ) -> AppClientCompilationResult:
        """Compile the application's TEAL code.

        :param app_spec: The application specification
        :param app_manager: The application manager instance
        :param compilation_params: Optional compilation parameters
        :return: The compilation result
        :raises ValueError: If attempting to compile without source or byte code
        """
        compilation_params = compilation_params or AppClientCompilationParams()
        deploy_time_params = compilation_params.get("deploy_time_params")
        updatable = compilation_params.get("updatable")
        deletable = compilation_params.get("deletable")

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
        app_spec: arc56.Arc56Contract,
        is_clear_state_program: bool = False,
        approval_source_map: ProgramSourceMap | None = None,
        clear_source_map: ProgramSourceMap | None = None,
        program: bytes | None = None,
        approval_source_info: arc56.ProgramSourceInfo | None = None,
        clear_source_info: arc56.ProgramSourceInfo | None = None,
    ) -> LogicError | Exception:
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
        if program_source_info and program_source_info.pc_offset_method == arc56.PcOffsetMethod.CBLOCKS:
            if not program:
                raise Exception("Program bytes are required to calculate the ARC56 cblocks PC offset")

            cblocks_offset = get_constant_block_offset(program)
            arc56_pc = error_details["pc"] - cblocks_offset

        # Find the source info for this PC and get the error message
        source_info = None
        if program_source_info and program_source_info.source_info:
            source_info = next(
                (s for s in program_source_info.source_info if isinstance(s, arc56.SourceInfo) and arc56_pc in s.pc),
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
                # Preserve traces from TransactionComposerError if available
                traces = getattr(e, "traces", None)
                e = LogicError(
                    logic_error_str=str(e),
                    program=program_source,
                    source_map=source_map,
                    transaction_id=error_details["transaction_id"],
                    message=error_details["message"],
                    pc=error_details["pc"],
                    logic_error=e,
                    get_line_for_pc=custom_get_line_for_pc,
                    traces=traces,
                )
        if error_message:
            import re

            message = e.logic_error_str if isinstance(e, LogicError) else str(e)
            app_id = re.search(r"(?<=app=)\d+", message)
            tx_id = re.search(r"(?<=transaction )\S+(?=:)", message)
            runtime_error_message = (
                f"Runtime error when executing {app_spec.name} "
                f"(appId: {app_id.group() if app_id else 'N/A'}) in transaction "
                f"{tx_id.group() if tx_id else 'N/A'}: {error_message}"
            )
            if isinstance(e, LogicError):
                e.message = runtime_error_message
                return e
            else:
                error = Exception(runtime_error_message)
                error.__cause__ = e
                return error

        return e

    def compile_app(
        self,
        compilation_params: AppClientCompilationParams | None = None,
    ) -> AppClientCompilationResult:
        """Compile the application's TEAL code.

        :param compilation_params: Optional compilation parameters
        :return: The compilation result
        """
        result = AppClient.compile(self._app_spec, self._algorand.app, compilation_params)

        if result.compiled_approval:
            self._approval_source_map = result.compiled_approval.source_map
        if result.compiled_clear:
            self._clear_source_map = result.compiled_clear.source_map

        # Store compiled programs for new app error filtering
        self._last_compiled["approval"] = result.approval_program
        self._last_compiled["clear"] = result.clear_state_program

        return result

    def clone(
        self,
        app_name: str | None = _MISSING,  # type: ignore[assignment]
        default_sender: str | None = _MISSING,  # type: ignore[assignment]
        default_signer: TransactionSigner | None = _MISSING,  # type: ignore[assignment]
        approval_source_map: ProgramSourceMap | None = _MISSING,  # type: ignore[assignment]
        clear_source_map: ProgramSourceMap | None = _MISSING,  # type: ignore[assignment]
    ) -> "AppClient":
        """Create a cloned AppClient instance with optionally overridden parameters.

        :param app_name: Optional new application name
        :param default_sender: Optional new default sender
        :param default_signer: Optional new default signer
        :param approval_source_map: Optional new approval source map
        :param clear_source_map: Optional new clear source map
        :return: A new AppClient instance

        :example:
            >>> client = AppClient(params)
            >>> cloned_client = client.clone(app_name="Cloned App", default_sender="NEW_SENDER")
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

        if not isinstance(source_maps.approval_source_map, dict | ProgramSourceMap):
            raise ValueError("Approval source map supplied is of invalid type. Must be a raw dict or `SourceMap`")
        if not isinstance(source_maps.clear_source_map, dict | ProgramSourceMap):
            raise ValueError("Clear source map supplied is of invalid type. Must be a raw dict or `SourceMap`")

        self._approval_source_map = (
            ProgramSourceMap(source_map=source_maps.approval_source_map)
            if isinstance(source_maps.approval_source_map, dict)
            else source_maps.approval_source_map
        )
        self._clear_source_map = (
            ProgramSourceMap(source_map=source_maps.clear_source_map)
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
        :example:
            >>> global_state = client.get_global_state()
        """
        return self._state_accessor.get_global_state()

    def get_box_names(self) -> list[BoxName]:
        """Get all box names for the application.

        :return: List of box names

        :example:
            >>> box_names = client.get_box_names()
        """
        return self._algorand.app.get_box_names(self._app_id)

    def get_box_value(self, name: BoxIdentifier) -> bytes:
        """Get the value of a box.

        :param name: The box identifier
        :return: The box value as bytes

        :example:
            >>> box_value = client.get_box_value(box_name)
        """
        return self._algorand.app.get_box_value(self._app_id, name)

    def get_box_value_from_abi_type(self, name: BoxIdentifier, abi_type: ABIType) -> ABIValue:
        """Get a box value decoded according to an ABI type.

        :param name: The box identifier
        :param abi_type: The ABI type to decode as
        :return: The decoded box value

        :example:
            >>> box_value = client.get_box_value_from_abi_type(box_name, abi_type)
        """
        return self._algorand.app.get_box_value_from_abi_type(self._app_id, name, abi_type)

    def get_box_values(self, filter_func: Callable[[BoxName], bool] | None = None) -> list[BoxValue]:
        """Get values for multiple boxes.

        :param filter_func: Optional function to filter box names
        :return: List of box values

        :example:
            >>> box_values = client.get_box_values()
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

        :example:
            >>> box_values = client.get_box_values_from_abi_type(abi_type)
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

        :example:
            >>> result = client.fund_app_account(params)
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

    def _is_new_app_error_for_this_app(self, error: Exception) -> bool:
        """Check if an error from a new app (app_id=0) is for this specific app by comparing program bytecode."""
        if not hasattr(error, "sent_transactions") or not error.sent_transactions:
            return False

        # Find the transaction that caused the error
        txn = None
        for t in error.sent_transactions:
            if hasattr(t, "get_txid") and t.get_txid() in str(error):
                txn = t
                break

        app_call = getattr(txn, "app_call", None)
        if not txn or app_call is None:
            return False

        return bool(
            app_call.clear_state_program == self._last_compiled.get("clear")
            and app_call.approval_program == self._last_compiled.get("approval")
        )

    def _handle_call_errors_transform(self, error: Exception) -> Exception:
        """Error transformer function for app-specific logic errors.

        This will be called by the transaction composer when errors occur during
        simulate or send operations to provide better error messages with source maps.

        :param error: The error to potentially transform
        :return: The transformed error if it's an app logic error, otherwise the original error
        """
        try:
            # Check if this is a logic error that we can parse
            from algokit_utils.errors.logic_error import parse_logic_error

            error_details = parse_logic_error(str(error))
            if not error_details:
                # Not a logic error, return unchanged
                return error

            # Check if this error is for our app
            should_transform = False

            if self._app_id == 0:
                # For new apps (app_id == 0), we can't use app ID filtering
                # Instead check the programs to identify if this is the correct app
                should_transform = self._is_new_app_error_for_this_app(error)
            else:
                # Only handle errors for this specific app
                app_id_string = f"app={self._app_id}"
                should_transform = app_id_string in str(error)

            if not should_transform:
                # Error is not for this app, return unchanged
                return error

            # This is a logic error for our app, transform it
            return self._expose_logic_error(e=error)

        except Exception:
            # If transformation fails, return the original error
            return error

    def _get_sender(self, sender: str | None) -> str:
        if not sender and not self._default_sender:
            raise Exception(
                f"No sender provided and no default sender present in app client for call to app {self.app_name}"
            )
        return sender or self._default_sender  # type: ignore[return-value]

    def _get_signer(
        self, sender: str | None, signer: TransactionSigner | AddressWithTransactionSigner | None
    ) -> TransactionSigner | AddressWithTransactionSigner | None:
        return signer or (self._default_signer if not sender or sender == self._default_sender else None)

    def _get_bare_params(self, params: dict[str, Any], on_complete: OnApplicationComplete) -> dict[str, Any]:
        sender = self._get_sender(params.get("sender"))
        return {
            **params,
            "app_id": self._app_id,
            "sender": sender,
            "signer": self._get_signer(params.get("sender"), params.get("signer")),
            "on_complete": on_complete,
        }

    def _get_abi_args_with_default_values(
        self,
        *,
        method_name_or_signature: str,
        args: Sequence[ABIValue | ABIStruct | AppMethodCallTransactionArgument | None] | None,
        sender: str,
    ) -> list[Any]:
        method = self._app_spec.get_abi_method(method_name_or_signature)
        result = list[ABIValue | ABIStruct | AppMethodCallTransactionArgument | None]()

        if args and len(method.args) < len(args):
            raise ValueError(
                f"Unexpected arg at position {len(method.args)}. {method.name} only expects {len(method.args)} args"
            )

        for i, method_arg in enumerate(method.args):
            arg_value = args[i] if args and i < len(args) else None

            if arg_value is not None:
                result.append(arg_value)
                continue

            default_value = method_arg.default_value
            arg_type = method_arg.type
            arg_name = method_arg.name or f"arg{i + 1}"
            if isinstance(arg_type, arc56.TransactionType):
                result.append(None)
            elif default_value:
                assert isinstance(arg_type, arc56.ReferenceType | abi.ABIType)
                result.append(self._get_abi_arg_default_value(arg_name, arg_type, default_value, sender))
            else:
                raise ValueError(f"No value provided for required argument {arg_name} in call to method {method.name}")

        return result

    def _get_abi_arg_default_value(
        self,
        arg_name: str,
        arg_type: abi.ABIType | arc56.ReferenceType,
        default_value: arc56.DefaultValue,
        sender: str,
    ) -> ABIValue:
        match default_value.source:
            case "literal":
                value_raw = base64.b64decode(default_value.data)
                value_type = default_value.type or arg_type
                return get_abi_decoded_value(value_raw, value_type)

            case "method":
                default_method = self._app_spec.get_abi_method(default_value.data)
                empty_args = [None] * len(default_method.args)
                call_result = self.send.call(
                    AppClientMethodCallParams(
                        method=default_value.data,
                        args=empty_args,
                        sender=sender,
                    )
                )

                if call_result.abi_return is None:
                    raise ValueError("Default value method call did not return a value")
                assert isinstance(default_method.returns.type, abi.ABIType)
                return call_result.abi_return

            case "local" | "global" | "box":
                key = base64.b64decode(default_value.data)
                try:
                    value, storage_key = self._get_storage_value(default_value.source, key, sender)
                except KeyError:
                    raise ValueError(
                        f"Key '{default_value.data}' not found in {default_value.source} "
                        f"storage for argument {arg_name}"
                    ) from None

                decoded_value: ABIValue
                if isinstance(value, bytes):
                    # special case to convert raw AVM bytes to a native string type suitable for encoding
                    if storage_key.value_type == arc56.AVMType.BYTES and isinstance(arg_type, abi.StringType):
                        decoded_value = value.decode("utf-8")
                    else:
                        decoded_value = get_abi_decoded_value(value, storage_key.value_type)
                else:
                    decoded_value = value
                return decoded_value
            case _:
                assert_never(default_value.source)

    def _get_storage_value(
        self, source: Literal["local", "global", "box"], key: bytes, sender: str
    ) -> tuple[bytes | int | str, arc56.StorageKey]:
        state_keys = self.app_spec.state.keys
        if source == "global":
            state = {s.key_raw: s for s in self.get_global_state().values()}[key]
            value = state.value_raw if state.value_raw is not None else state.value
            storage_keys = state_keys.global_state
        elif source == "local":
            state = {s.key_raw: s for s in self.get_local_state(sender).values()}[key]
            value = state.value_raw if state.value_raw is not None else state.value
            storage_keys = state_keys.local_state
        elif source == "box":
            value = self.get_box_value(key)
            storage_keys = state_keys.box
        else:
            assert_never(source)

        key_base64 = base64.b64encode(key).decode("ascii")
        storage_key = {sk.key: sk for sk in storage_keys.values()}[key_base64]
        return value, storage_key

    def _get_abi_params(self, params: dict[str, Any], on_complete: OnApplicationComplete) -> dict[str, Any]:
        sender = self._get_sender(params.get("sender"))
        method = self._app_spec.get_abi_method(params["method"])
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
        method: arc56.Method,
    ) -> SendAppUpdateTransactionResult[Arc56ReturnValueType] | SendAppTransactionResult[Arc56ReturnValueType]:
        _ = method  # kept for compatibility
        result_value = result()
        abi_return_value: Arc56ReturnValueType
        if isinstance(result_value.abi_return, ABIReturn):
            if result_value.abi_return.decode_error:
                raise ValueError(result_value.abi_return.decode_error)
            abi_return_value = result_value.abi_return.value
        else:
            abi_return_value = None

        if isinstance(result_value, SendAppUpdateTransactionResult):
            return SendAppUpdateTransactionResult[Arc56ReturnValueType](
                **{**result_value.__dict__, "abi_return": abi_return_value}
            )
        return SendAppTransactionResult[Arc56ReturnValueType](
            **{**result_value.__dict__, "abi_return": abi_return_value}
        )
