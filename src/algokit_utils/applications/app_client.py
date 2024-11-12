from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from algosdk.logic import get_application_address

from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.applications.utils import get_abi_decoded_value, get_abi_encoded_value
from algokit_utils.models.application import Arc56Contract, StorageKey, StorageMap

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
class ResolveAppClientByNetwork(_CommonAppClientParams):
    app_spec: Arc56Contract | ApplicationSpecification | str
    algorand: AlgorandClientProtocol


class AppClientStateMethodsProtocol(Protocol):
    def get_all(self) -> dict[str, Any]: ...

    def get_value(self, name: str, app_state: dict[str, AppState] | None = None) -> ABIValue | None: ...

    def get_map_value(self, map_name: str, key: bytes | Any, app_state: dict[str, AppState] | None = None) -> Any: ...  # noqa: ANN401

    def get_map(self, map_name: str) -> dict[str, ABIValue]: ...


class _AppClientStateMethods(AppClientStateMethodsProtocol):
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


class AppClientStateAccessor:
    def __init__(self, client: AppClient) -> None:
        self._client = client
        self._algorand = client._algorand  # noqa: SLF001
        self._app_id = client._app_id  # noqa: SLF001
        self._app_spec = client._app_spec  # noqa: SLF001

    def local_state(self, address: str) -> AppClientStateMethodsProtocol:
        """Methods to access local state for the current app for a given address"""
        return self._get_state_methods(
            state_getter=lambda: self._algorand.app.get_local_state(self._app_id, address),
            key_getter=lambda: self._app_spec.state.keys.get("local", {}),
            map_getter=lambda: self._app_spec.state.maps.get("local", {}),
        )

    @property
    def global_state(self) -> AppClientStateMethodsProtocol:
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
    ) -> AppClientStateMethodsProtocol:
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
        self._state_accessor = AppClientStateAccessor(self)

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
    def state(self) -> AppClientStateAccessor:
        return self._state_accessor

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

    #       public static async fromNetwork(params: ResolveAppClientByNetwork): Promise<AppClient> {
    #     const network = await params.algorand.client.network()
    #     const appSpec = AppClient.normaliseAppSpec(params.appSpec)
    #     const networkNames = [network.genesisHash]
    #     if (network.isLocalNet) networkNames.push('localnet')
    #     if (network.isTestNet) networkNames.push('testnet')
    #     if (network.isMainNet) networkNames.push('mainnet')
    #     const availableAppSpecNetworks = Object.keys(appSpec.networks ?? {})
    #     const networkIndex = availableAppSpecNetworks.findIndex((n) => networkNames.includes(n))

    #     if (networkIndex === -1) {
    #       throw new Error(`No app ID found for network ${JSON.stringify(networkNames)} in the app spec`)
    #     }

    #     const appId = BigInt(appSpec.networks![networkIndex].appID)
    #     return new AppClient({ ...params, appId, appSpec })
    #   }

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

    # public clone(params: CloneAppClientParams) {
    # return new AppClient({
    #   appId: this._appId,
    #   appSpec: this._appSpec,
    #   algorand: this._algorand,
    #   appName: this._appName,
    #   defaultSender: this._defaultSender,
    #   defaultSigner: this._defaultSigner,
    #   approvalSourceMap: this._approvalSourceMap,
    #   clearSourceMap: this._clearSourceMap,
    #   ...params,
    # })
    # }

    def get_local_state(self, address: str) -> dict[str, AppState]:
        return self._state_accessor.get_local_state(address)

    def get_global_state(self) -> dict[str, AppState]:
        return self._state_accessor.get_global_state()

    def new_group(self) -> TransactionComposer:
        return self._algorand.new_group()

    def _get_signer(
        self,
        sender: str | None,
        signer: TransactionSigner | None,
    ) -> TransactionSigner | None:
        return signer or (None if sender else self._default_signer)

    def _get_sender(self, sender: str | None = None) -> str:
        if not sender and not self._default_sender:
            raise ValueError(
                f"No sender provided and no default sender present in app client for call to app {self._app_name}"
            )
        return sender or self._default_sender  # type: ignore[return-value]

    # def _handle_call_errors(self, call: Callable[[], Any]) -> Any:
    #     try:
    #         return call()
    #     except Exception as e:
    #         raise self._expose_logic_error(e) from e

    # def _expose_logic_error(self, e: Exception) -> Exception:
    #     # Add source map info if available
    #     if hasattr(e, "program_counter") and self._approval_source_map:
    #         pc = e.program_counter  # type: ignore[attr-defined]
    #         line = self._approval_source_map.get_line_for_pc(pc)
    #         e.source_line = line  # type: ignore[attr-defined]
    #     return e

    # def get_abi_method(self, method_name: str) -> dict[str, Any]:
    #     for method in self._app_spec.contract.methods:
    #         if method["name"] == method_name:
    #             return method
    #     raise ValueError(f"Method {method_name} not found")

    # def process_method_call_return(self, result: Any, method: dict[str, Any]) -> Any:
    #     if not result or "return" not in result:
    #         return result

    #     return_type = method.get("returns", {}).get("type")
    #     if not return_type:
    #         return result

    #     return self._decode_abi_value(result["return"], return_type)
