from __future__ import annotations

import base64
import copy
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

import algosdk
from algosdk.box_reference import BoxReference
from algosdk.logic import get_application_address
from algosdk.transaction import OnComplete, Transaction

from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.applications.app_manager import AppManager, CompiledTeal, TealTemplateParams
from algokit_utils.applications.utils import (
    get_abi_decoded_value,
    get_abi_encoded_value,
    get_abi_tuple_from_abi_struct,
    get_arc56_method,
)
from algokit_utils.models.abi import ABIStruct
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.models.application import Arc56Contract, StorageKey, StorageMap
from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCall,
    AppMethodCallTransactionArgument,
    PaymentParams,
    SenderParam,
)
from algokit_utils.transactions.transaction_sender import SendAppTransactionResult, SendSingleTransactionResult

if TYPE_CHECKING:
    from collections.abc import Callable

    from algosdk.atomic_transaction_composer import TransactionSigner
    from algosdk.source_map import SourceMap

    from algokit_utils.applications.app_manager import AppState
    from algokit_utils.models.abi import ABIValue
    from algokit_utils.protocols.application import AlgorandClientProtocol
    from algokit_utils.transactions.transaction_composer import TransactionComposer

# TEAL opcodes for constant blocks
BYTE_CBLOCK = 0x20  # bytecblock opcode
INT_CBLOCK = 0x21  # intcblock opcode


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


@dataclass
class ProgramSourceInfo:
    pc_offset_method: str | None
    source_info: list[dict[str, Any]]


@dataclass
class ExposedLogicErrorDetails:
    is_clear_state_program: bool = False
    approval_source_map: SourceMap | None = None
    clear_source_map: SourceMap | None = None
    program: bytes | None = None
    approval_source_info: ProgramSourceInfo | None = None
    clear_source_info: ProgramSourceInfo | None = None


@dataclass(kw_only=True)
class _CommonAppClientParams:
    app_name: str | None = None
    default_sender: str | None = None
    default_signer: TransactionSigner | None = None
    approval_source_map: SourceMap | None = None
    clear_source_map: SourceMap | None = None


@dataclass(kw_only=True)
class AppClientParams(_CommonAppClientParams):
    app_id: int
    app_spec: Arc56Contract | ApplicationSpecification | str
    algorand: AlgorandClientProtocol


@dataclass(kw_only=True)
class CloneAppClientParams(_CommonAppClientParams):
    app_id: int | None = None


@dataclass(kw_only=True)
class AppClientCompilationResult:
    approval_program: bytes
    clear_state_program: bytes
    compiled_approval: CompiledTeal | None = None
    compiled_clear: CompiledTeal | None = None


@dataclass(kw_only=True)
class CompileAppClientParams:
    app_spec: Arc56Contract | ApplicationSpecification | str
    algorand: AlgorandClientProtocol
    compilation: AppClientCompilationParams | None = None


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
        self._algorand = client._algorand  # noqa: SLF001
        self._app_id = client._app_id  # noqa: SLF001
        self._app_spec = client._app_spec  # noqa: SLF001

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


@dataclass(kw_only=True)
class AppClientMethodCallParams:
    method: str
    sender: str | None = None
    args: list[ABIValue | ABIStruct | AppMethodCallTransactionArgument | None]
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
    # OnComplete
    on_complete: algosdk.transaction.OnComplete | None = None
    # # SendParams
    max_rounds_to_wait: int | None = None
    suppress_log: bool | None = None
    populate_app_call_resources: bool | None = None


@dataclass(kw_only=True)
class AppClientCompilationParams:
    deploy_time_params: TealTemplateParams | None = None
    updatable: bool | None = None
    deletable: bool | None = None


@dataclass(kw_only=True)
class ResolveAppClientByNetwork(_CommonAppClientParams):
    app_spec: Arc56Contract | ApplicationSpecification | str
    algorand: AlgorandClientProtocol


class _AppClientBareParamsAccessor:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand  # noqa: SLF001
        self._app_id = client._app_id  # noqa: SLF001
        self._app_spec = client._app_spec  # noqa: SLF001


class _AppClientMethodCallParamsAccessor:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand  # noqa: SLF001
        self._app_id = client._app_id  # noqa: SLF001
        self._app_spec = client._app_spec  # noqa: SLF001
        self._bare_params_accessor = _AppClientBareParamsAccessor(client)

    @property
    def bare(self) -> _AppClientBareParamsAccessor:
        return self._bare_params_accessor

    def fund_app_account(self, params: FundAppAccountParams) -> PaymentParams:
        return PaymentParams(
            sender=self._client._get_sender(params.sender),
            signer=self._client._get_signer(params.sender, params.signer),
            receiver=self._client.app_address,
            amount=params.amount,
            rekey_to=params.rekey_to,
            note=params.note,
            lease=params.lease,
            static_fee=params.static_fee,
            extra_fee=params.extra_fee,
            max_fee=params.max_fee,
            validity_window=params.validity_window,
            first_valid_round=params.first_valid_round,
            last_valid_round=params.last_valid_round,
            close_remainder_to=params.close_remainder_to,
        )

    def call(self, params: AppClientMethodCallParams) -> AppCallMethodCall:
        input_params = self._get_abi_params(params.__dict__, on_complete=algosdk.transaction.OnComplete.NoOpOC)
        return AppCallMethodCall(**input_params)

    def _get_abi_params(self, params: dict[str, Any], on_complete: algosdk.transaction.OnComplete) -> dict[str, Any]:
        input_params = copy.deepcopy(params)

        input_params["app_id"] = self._app_id
        input_params["on_complete"] = on_complete

        input_params["sender"] = self._client._get_sender(params["sender"])  # noqa: SLF001
        input_params["signer"] = self._client._get_signer(params["sender"], params["signer"])  # noqa: SLF001

        if params.get("method"):
            input_params["method"] = get_arc56_method(params["method"], self._app_spec)
            if params.get("args"):
                input_params["args"] = self._client._get_abi_args_with_default_values(  # noqa: SLF001
                    method_name_or_signature=params["method"],
                    args=params["args"],
                    sender=self._client._get_sender(input_params["sender"]),  # noqa: SLF001
                )

        return input_params


class _AppClientTransactionCreator:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand  # noqa: SLF001
        self._app_id = client._app_id  # noqa: SLF001
        self._app_spec = client._app_spec  # noqa: SLF001

    def fund_app_account(self, params: FundAppAccountParams) -> Transaction:
        return self._algorand.create_transaction.payment(self._client.params.fund_app_account(params))

    # def update(self, params: AppClientMethodCallParams | AppClientCompilationParams) -> Transaction:
    #     return self._algorand.create_transaction.app_update_method_call()


#  update: async (params: AppClientMethodCallParams & AppClientCompilationParams) => {
#         return this._algorand.createTransaction.appUpdateMethodCall(await this.params.update(params))
#       },
#       /**
#        * Return transactions for an opt-in ABI call
#        */
#       optIn: async (params: AppClientMethodCallParams) => {
#         return this._algorand.createTransaction.appCallMethodCall(await this.params.optIn(params))
#       },
#       /**
#        * Return transactions for a delete ABI call
#        */
#       delete: async (params: AppClientMethodCallParams) => {
#         return this._algorand.createTransaction.appDeleteMethodCall(await this.params.delete(params))
#       },
#       /**
#        * Return transactions for a close out ABI call
#        */
#       closeOut: async (params: AppClientMethodCallParams) => {
#         return this._algorand.createTransaction.appCallMethodCall(await this.params.closeOut(params))
#       },
#       /**
#        * Return transactions for an ABI call (defaults to no-op)
#        */
#       call: async (params: AppClientMethodCallParams & CallOnComplete) => {
#         return this._algorand.createTransaction.appCallMethodCall(await this.params.call(params))
#       },


class _AppClientSendAccessor:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand  # noqa: SLF001
        self._app_id = client._app_id  # noqa: SLF001
        self._app_spec = client._app_spec  # noqa: SLF001

    def fund_app_account(self, params: FundAppAccountParams) -> SendSingleTransactionResult:
        return self._algorand.send.payment(self._client.params.fund_app_account(params))

    def call(self, params: AppClientMethodCallParams) -> SendAppTransactionResult:
        is_read_only_call = (
            params.on_complete == algosdk.transaction.OnComplete.NoOpOC
            or not params.on_complete
            and get_arc56_method(params.method, self._app_spec).method.readonly
        )

        if is_read_only_call:
            return (
                self._algorand.new_group()
                .add_app_call_method_call(self._client.params.call(params))
                .simulate(allow_unnamed_resources=params.populate_app_call_resources or True, skip_signature=True)
            )

        return self._algorand.send.app_call_method_call(self._client.params.call(params))

    # call: async (params: AppClientMethodCallParams & CallOnComplete & SendParams) => {
    #     // Read-only call - do it via simulate
    #     if (
    #       (params.onComplete === OnApplicationComplete.NoOpOC || !params.onComplete) &&
    #       getArc56Method(params.method, this._appSpec).method.readonly
    #     ) {
    #       const result = await this._algorand
    #         .newGroup()
    #         .addAppCallMethodCall(await this.params.call(params))
    #         .simulate({
    #           allowUnnamedResources: params.populateAppCallResources ?? true,
    #           // Simulate calls for a readonly method shouldn't invoke signing
    #           skipSignatures: true,
    #         })
    #       return this.processMethodCallReturn(
    #         {
    #           ...result,
    #           transaction: result.transactions.at(-1)!,
    #           confirmation: result.confirmations.at(-1)!,
    #           // eslint-disable-next-line @typescript-eslint/no-non-null-asserted-optional-chain
    #           return: result.returns?.length ?? 0 > 0 ? result.returns?.at(-1)! : undefined,
    #         } satisfies SendAppTransactionResult,
    #         getArc56Method(params.method, this._appSpec),
    #       )
    #     }

    #     return this.handleCallErrors(async () =>
    #       this.processMethodCallReturn(
    #         this._algorand.send.appCallMethodCall(await this.params.call(params)),
    #         getArc56Method(params.method, this._appSpec),
    #       ),
    #     )
    #   },


class AppClient:
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
        self._state_accessor = _AppClientStateAccessor(self)
        self._params_accessor = _AppClientMethodCallParamsAccessor(self)
        self._send_accessor = _AppClientSendAccessor(self)

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
    def from_network(params: ResolveAppClientByNetwork) -> AppClient:
        network = params.algorand.client.network()
        app_spec = AppClient.normalise_app_spec(params.app_spec)
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

        input_params = params.__dict__
        input_params["app_id"] = app_id
        input_params["app_spec"] = app_spec

        return AppClient(AppClientParams(**input_params))  # type:ignore[arg-type, call-arg]

    @staticmethod
    def compile(
        app_spec: Arc56Contract, app_manager: AppManager, compilation: AppClientCompilationParams | None = None
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
            {"updatable": compilation.updatable or False, "deletable": compilation.deletable or False}
            if compilation
            else None
        )
        compiled_approval = app_manager.compile_teal_template(
            approval_template,
            template_params=compilation.deploy_time_params if compilation else None,
            deployment_metadata=deployment_metadata,
        )

        clear_template: str = base64.b64decode(app_spec.source.get("clear", "")).decode("utf-8")  # type: ignore[assignment]
        compiled_clear = app_manager.compile_teal_template(
            clear_template,
            template_params=compilation.deploy_time_params if compilation else None,
        )

        # TODO: Add invocation of persisting sourcemaps

        return AppClientCompilationResult(
            approval_program=compiled_approval.compiled_base64_to_bytes,
            compiled_approval=compiled_approval,
            clear_state_program=compiled_clear.compiled_base64_to_bytes,
            compiled_clear=compiled_clear,
        )

    # NOTE: No method overloads hence slightly different name, in TS its both instance/static methods named 'compile'
    def compile_and_persist_sourcemaps(
        self, compilation: AppClientCompilationParams | None = None
    ) -> AppClientCompilationResult:
        result = AppClient.compile(self._app_spec, self._algorand.app, compilation)

        if result.compiled_approval:
            self._approval_source_map = result.compiled_approval.source_map
        if result.compiled_clear:
            self._clear_source_map = result.compiled_clear.source_map

        return result

    def clone(self, params: CloneAppClientParams) -> AppClient:
        default_params = {
            "app_id": self._app_id,
            "algorand": self._algorand,
            "app_spec": self._app_spec,
            "app_name": self._app_name,
            "default_sender": self._default_sender,
            "default_signer": self._default_signer,
            "approval_source_map": self._approval_source_map,
            "clear_source_map": self._clear_source_map,
        }

        for k, v in params.__dict__.items():
            if k and v:
                default_params[k] = v

        return AppClient(AppClientParams(**default_params))  # type: ignore[arg-type]

    def get_local_state(self, address: str) -> dict[str, AppState]:
        return self._state_accessor.get_local_state(address)

    def get_global_state(self) -> dict[str, AppState]:
        return self._state_accessor.get_global_state()

    def new_group(self) -> TransactionComposer:
        return self._algorand.new_group()

    def fund_app_account(self, params: FundAppAccountParams) -> SendSingleTransactionResult:
        return self.send.fund_app_account(params)

    def _get_sender(self, sender: str | None) -> str:
        if not sender and not self._default_sender:
            raise Exception(
                f"No sender provided and no default sender present in app client for call to app {self.app_name}"
            )
        return sender or self._default_sender  # type: ignore[return-value]

    def _get_signer(self, sender: str | None, signer: TransactionSigner | None) -> TransactionSigner | None:
        return signer or self._default_signer if sender else None

    def _get_bare_params(self, params: dict[str, Any], on_complete: algosdk.transaction.OnComplete) -> dict[str, Any]:
        return {
            **params,
            "app_id": self._app_id,
            "sender": self._get_sender(params.get("sender")),
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
