import base64
from collections.abc import Mapping
from typing import Any, cast

import algosdk
import algosdk.atomic_transaction_composer
import algosdk.box_reference
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.box_reference import BoxReference as AlgosdkBoxReference
from algosdk.logic import get_application_address
from algosdk.source_map import SourceMap
from algosdk.v2client import algod

from algokit_utils.applications.abi import ABIReturn, ABIType, ABIValue
from algokit_utils.models.application import (
    AppInformation,
    AppState,
    CompiledTeal,
)
from algokit_utils.models.state import BoxIdentifier, BoxName, BoxReference, DataTypeFlag, TealTemplateParams

__all__ = [
    "DELETABLE_TEMPLATE_NAME",
    "UPDATABLE_TEMPLATE_NAME",
    "AppManager",
]


UPDATABLE_TEMPLATE_NAME = "TMPL_UPDATABLE"
"""The name of the TEAL template variable for deploy-time immutability control."""

DELETABLE_TEMPLATE_NAME = "TMPL_DELETABLE"
"""The name of the TEAL template variable for deploy-time permanence control."""


def _is_valid_token_character(char: str) -> bool:
    return char.isalnum() or char == "_"


def _last_token_base64(line: str, idx: int) -> bool:
    try:
        *_, last = line[:idx].split()
    except ValueError:
        return False
    return last in ("base64", "b64")


def _find_template_token(line: str, token: str, start: int = 0, end: int = -1) -> int | None:
    if end < 0:
        end = len(line)

    idx = start
    while idx < end:
        token_idx = _find_unquoted_string(line, token, idx, end)
        if token_idx is None:
            break
        trailing_idx = token_idx + len(token)
        if (token_idx == 0 or not _is_valid_token_character(line[token_idx - 1])) and (
            trailing_idx >= len(line) or not _is_valid_token_character(line[trailing_idx])
        ):
            return token_idx
        idx = trailing_idx
    return None


def _find_unquoted_string(line: str, token: str, start: int = 0, end: int = -1) -> int | None:
    if end < 0:
        end = len(line)
    idx = start
    in_quotes = in_base64 = False
    while idx < end:
        current_char = line[idx]
        match current_char:
            case " " | "(" if not in_quotes and _last_token_base64(line, idx):
                in_base64 = True
            case " " | ")" if not in_quotes and in_base64:
                in_base64 = False
            case "\\" if in_quotes:
                idx += 1
            case '"':
                in_quotes = not in_quotes
            case _ if not in_quotes and not in_base64 and line.startswith(token, idx):
                return idx
        idx += 1
    return None


def _replace_template_variable(program_lines: list[str], template_variable: str, value: str) -> tuple[list[str], int]:
    result: list[str] = []
    match_count = 0
    token = f"TMPL_{template_variable}" if not template_variable.startswith("TMPL_") else template_variable
    token_idx_offset = len(value) - len(token)
    for line in program_lines:
        comment_idx = _find_unquoted_string(line, "//")
        if comment_idx is None:
            comment_idx = len(line)
        code = line[:comment_idx]
        comment = line[comment_idx:]
        trailing_idx = 0
        while True:
            token_idx = _find_template_token(code, token, trailing_idx)
            if token_idx is None:
                break

            trailing_idx = token_idx + len(token)
            prefix = code[:token_idx]
            suffix = code[trailing_idx:]
            code = f"{prefix}{value}{suffix}"
            match_count += 1
            trailing_idx += token_idx_offset
        result.append(code + comment)
    return result, match_count


class AppManager:
    """A manager class for interacting with Algorand applications.

    Provides functionality for compiling TEAL code, managing application state,
    and interacting with application boxes.

    :param algod_client: The Algorand client instance to use for interacting with the network

    :example:
        >>> app_manager = AppManager(algod_client)
    """

    def __init__(self, algod_client: algod.AlgodClient):
        self._algod = algod_client
        self._compilation_results: dict[str, CompiledTeal] = {}

    def compile_teal(self, teal_code: str) -> CompiledTeal:
        """Compile TEAL source code.

        :param teal_code: The TEAL source code to compile
        :return: The compiled TEAL code and associated metadata
        """

        if teal_code in self._compilation_results:
            return self._compilation_results[teal_code]

        compiled = self._algod.compile(teal_code, source_map=True)
        result = CompiledTeal(
            teal=teal_code,
            compiled=compiled["result"],
            compiled_hash=compiled["hash"],
            compiled_base64_to_bytes=base64.b64decode(compiled["result"]),
            source_map=SourceMap(compiled.get("sourcemap", {})),
        )
        self._compilation_results[teal_code] = result
        return result

    def compile_teal_template(
        self,
        teal_template_code: str,
        template_params: TealTemplateParams | None = None,
        deployment_metadata: Mapping[str, bool | None] | None = None,
    ) -> CompiledTeal:
        """Compile a TEAL template with parameters.

        :param teal_template_code: The TEAL template code to compile
        :param template_params: Parameters to substitute in the template
        :param deployment_metadata: Deployment control parameters
        :return: The compiled TEAL code and associated metadata

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> teal_template_code =
            ...     # This is a TEAL template
            ...     # It can contain template variables like {TMPL_UPDATABLE} and {TMPL_DELETABLE}
            ...
            >>> compiled_teal = app_manager.compile_teal_template(teal_template_code)
        """

        teal_code = AppManager.strip_teal_comments(teal_template_code)
        teal_code = AppManager.replace_template_variables(teal_code, template_params or {})

        if deployment_metadata:
            teal_code = AppManager.replace_teal_template_deploy_time_control_params(teal_code, deployment_metadata)

        return self.compile_teal(teal_code)

    def get_compilation_result(self, teal_code: str) -> CompiledTeal | None:
        """Get cached compilation result for TEAL code if available.

        :param teal_code: The TEAL source code
        :return: The cached compilation result if available, None otherwise

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> teal_code = "RETURN 1"
            >>> compiled_teal = app_manager.compile_teal(teal_code)
            >>> compilation_result = app_manager.get_compilation_result(teal_code)
        """
        return self._compilation_results.get(teal_code)

    def get_by_id(self, app_id: int) -> AppInformation:
        """Get information about an application by ID.

        :param app_id: The application ID
        :return: Information about the application

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 1234567890
            >>> app_info = app_manager.get_by_id(app_id)
        """

        app = self._algod.application_info(app_id)
        assert isinstance(app, dict)
        app_params = app["params"]

        return AppInformation(
            app_id=app_id,
            app_address=get_application_address(app_id),
            approval_program=base64.b64decode(app_params["approval-program"]),
            clear_state_program=base64.b64decode(app_params["clear-state-program"]),
            creator=app_params["creator"],
            local_ints=app_params["local-state-schema"]["num-uint"],
            local_byte_slices=app_params["local-state-schema"]["num-byte-slice"],
            global_ints=app_params["global-state-schema"]["num-uint"],
            global_byte_slices=app_params["global-state-schema"]["num-byte-slice"],
            extra_program_pages=app_params.get("extra-program-pages", 0),
            global_state=self.decode_app_state(app_params.get("global-state", [])),
        )

    def get_global_state(self, app_id: int) -> dict[str, AppState]:
        """Get the global state of an application.

        :param app_id: The application ID
        :return: The application's global state

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> global_state = app_manager.get_global_state(app_id)
        """

        return self.get_by_id(app_id).global_state

    def get_local_state(self, app_id: int, address: str) -> dict[str, AppState]:
        """Get the local state for an account in an application.

        :param app_id: The application ID
        :param address: The account address
        :return: The account's local state for the application
        :raises ValueError: If local state is not found

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> address = "SENDER_ADDRESS"
            >>> local_state = app_manager.get_local_state(app_id, address)
        """

        app_info = self._algod.account_application_info(address, app_id)
        assert isinstance(app_info, dict)
        if not app_info.get("app-local-state", {}).get("key-value"):
            raise ValueError("Couldn't find local state")
        return self.decode_app_state(app_info["app-local-state"]["key-value"])

    def get_box_names(self, app_id: int) -> list[BoxName]:
        """Get names of all boxes for an application.

        If the box name can't be decoded from UTF-8, the string representation of the bytes is returned.

        :param app_id: The application ID
        :return: List of box names

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> box_names = app_manager.get_box_names(app_id)
        """

        def utf8_decode_or_string_cast(b: bytes) -> str:
            """Return the UTF-8 encoding or return the string representation of the bytes."""
            try:
                return b.decode("utf-8")
            except UnicodeDecodeError:
                return str(b)

        box_result = self._algod.application_boxes(app_id)
        assert isinstance(box_result, dict)
        return [
            BoxName(
                name_raw=base64.b64decode(b["name"]),
                name_base64=b["name"],
                name=utf8_decode_or_string_cast(base64.b64decode(b["name"])),
            )
            for b in box_result["boxes"]
        ]

    def get_box_value(self, app_id: int, box_name: BoxIdentifier) -> bytes:
        """Get the value stored in a box.

        :param app_id: The application ID
        :param box_name: The box identifier
        :return: The box value as bytes

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> box_name = "BOX_NAME"
            >>> box_value = app_manager.get_box_value(app_id, box_name)
        """

        name = AppManager.get_box_reference(box_name)[1]
        box_result = self._algod.application_box_by_name(app_id, name)
        assert isinstance(box_result, dict)
        return base64.b64decode(box_result["value"])

    def get_box_values(self, app_id: int, box_names: list[BoxIdentifier]) -> list[bytes]:
        """Get values for multiple boxes.

        :param app_id: The application ID
        :param box_names: List of box identifiers
        :return: List of box values as bytes

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> box_names = ["BOX_NAME_1", "BOX_NAME_2"]
            >>> box_values = app_manager.get_box_values(app_id, box_names)
        """

        return [self.get_box_value(app_id, box_name) for box_name in box_names]

    def get_box_value_from_abi_type(self, app_id: int, box_name: BoxIdentifier, abi_type: ABIType) -> ABIValue:
        """Get and decode a box value using an ABI type.

        :param app_id: The application ID
        :param box_name: The box identifier
        :param abi_type: The ABI type to decode with
        :return: The decoded box value
        :raises ValueError: If decoding fails

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> box_name = "BOX_NAME"
            >>> abi_type = ABIType.UINT
            >>> box_value = app_manager.get_box_value_from_abi_type(app_id, box_name, abi_type)
        """

        value = self.get_box_value(app_id, box_name)
        try:
            parse_to_tuple = isinstance(abi_type, algosdk.abi.TupleType)
            decoded_value = abi_type.decode(value)
            return tuple(decoded_value) if parse_to_tuple else decoded_value
        except Exception as e:
            raise ValueError(f"Failed to decode box value {value.decode('utf-8')} with ABI type {abi_type}") from e

    def get_box_values_from_abi_type(
        self, app_id: int, box_names: list[BoxIdentifier], abi_type: ABIType
    ) -> list[ABIValue]:
        """Get and decode multiple box values using an ABI type.

        :param app_id: The application ID
        :param box_names: List of box identifiers
        :param abi_type: The ABI type to decode with
        :return: List of decoded box values

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> box_names = ["BOX_NAME_1", "BOX_NAME_2"]
            >>> abi_type = ABIType.UINT
            >>> box_values = app_manager.get_box_values_from_abi_type(app_id, box_names, abi_type)
        """

        return [self.get_box_value_from_abi_type(app_id, box_name, abi_type) for box_name in box_names]

    @staticmethod
    def get_box_reference(box_id: BoxIdentifier | BoxReference) -> tuple[int, bytes]:
        """Get standardized box reference from various identifier types.

        :param box_id: The box identifier
        :return: Tuple of (app_id, box_name_bytes)
        :raises ValueError: If box identifier type is invalid

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> box_name = "BOX_NAME"
            >>> box_reference = app_manager.get_box_reference(box_name)
        """

        if isinstance(box_id, (BoxReference | AlgosdkBoxReference)):
            return box_id.app_index, box_id.name

        name = b""
        if isinstance(box_id, str):
            name = box_id.encode("utf-8")
        elif isinstance(box_id, bytes):
            name = box_id
        elif isinstance(box_id, AccountTransactionSigner):
            name = cast(
                bytes, algosdk.encoding.decode_address(algosdk.account.address_from_private_key(box_id.private_key))
            )
        else:
            raise ValueError(f"Invalid box identifier type: {type(box_id)}")

        return 0, name

    @staticmethod
    def get_abi_return(
        confirmation: algosdk.v2client.algod.AlgodResponseType, method: algosdk.abi.Method | None = None
    ) -> ABIReturn | None:
        """Get the ABI return value from a transaction confirmation.

        :param confirmation: The transaction confirmation
        :param method: The ABI method
        :return: The parsed ABI return value, or None if not available

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> method = "METHOD_NAME"
            >>> confirmation = algod_client.pending_transaction_info(tx_id)
            >>> abi_return = app_manager.get_abi_return(confirmation, method)
        """
        if not method:
            return None

        atc = algosdk.atomic_transaction_composer.AtomicTransactionComposer()
        abi_result = atc.parse_result(
            method,
            "dummy_txn",
            confirmation,  # type: ignore[arg-type]
        )

        if not abi_result:
            return None

        return ABIReturn(abi_result)

    @staticmethod
    def decode_app_state(state: list[dict[str, Any]]) -> dict[str, AppState]:
        """Decode application state from raw format.

        :param state: The raw application state
        :return: Decoded application state
        :raises ValueError: If unknown state data type is encountered

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> state = app_manager.get_global_state(app_id)
            >>> decoded_state = app_manager.decode_app_state(state)
        """

        state_values: dict[str, AppState] = {}

        def decode_bytes_to_str(value: bytes) -> str:
            try:
                return value.decode("utf-8")
            except UnicodeDecodeError:
                return value.hex()

        for state_val in state:
            key_base64 = state_val["key"]
            key_raw = base64.b64decode(key_base64)
            key = decode_bytes_to_str(key_raw)
            teal_value = state_val["value"]

            data_type_flag = teal_value.get("action", teal_value.get("type"))

            if data_type_flag == DataTypeFlag.BYTES:
                value_base64 = teal_value.get("bytes", "")
                value_raw = base64.b64decode(value_base64)
                state_values[key] = AppState(
                    key_raw=key_raw,
                    key_base64=key_base64,
                    value_raw=value_raw,
                    value_base64=value_base64,
                    value=decode_bytes_to_str(value_raw),
                )
            elif data_type_flag == DataTypeFlag.UINT:
                value = teal_value.get("uint", 0)
                state_values[key] = AppState(
                    key_raw=key_raw,
                    key_base64=key_base64,
                    value_raw=None,
                    value_base64=None,
                    value=int(value),
                )
            else:
                raise ValueError(f"Received unknown state data type of {data_type_flag}")

        return state_values

    @staticmethod
    def replace_template_variables(program: str, template_values: TealTemplateParams) -> str:
        """Replace template variables in TEAL code.

        :param program: The TEAL program code
        :param template_values: Template variable values to substitute
        :return: TEAL code with substituted values
        :raises ValueError: If template value type is unexpected

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> program = "RETURN 1"
            >>> template_values = {"TMPL_UPDATABLE": True, "TMPL_DELETABLE": True}
            >>> updated_program = app_manager.replace_template_variables(program, template_values)
        """

        program_lines = program.splitlines()
        for template_variable_name, template_value in template_values.items():
            match template_value:
                case int():
                    value = str(template_value)
                case str():
                    value = "0x" + template_value.encode("utf-8").hex()
                case bytes():
                    value = "0x" + template_value.hex()
                case _:
                    raise ValueError(
                        f"Unexpected template value type {template_variable_name}: {template_value.__class__}"
                    )

            program_lines, _ = _replace_template_variable(program_lines, template_variable_name, value)

        return "\n".join(program_lines)

    @staticmethod
    def replace_teal_template_deploy_time_control_params(
        teal_template_code: str, params: Mapping[str, bool | None]
    ) -> str:
        """Replace deploy-time control parameters in TEAL template.

        :param teal_template_code: The TEAL template code
        :param params: The deploy-time control parameters
        :return: TEAL code with substituted control parameters
        :raises ValueError: If template variables not found in code

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> app_id = 123
            >>> teal_template_code = "RETURN 1"
            >>> params = {"TMPL_UPDATABLE": True, "TMPL_DELETABLE": True}
            >>> updated_teal_code = app_manager.replace_teal_template_deploy_time_control_params(
                teal_template_code, params
            )
        """

        updatable = params.get("updatable")
        if updatable is not None:
            if UPDATABLE_TEMPLATE_NAME not in teal_template_code:
                raise ValueError(
                    f"Deploy-time updatability control requested for app deployment, but {UPDATABLE_TEMPLATE_NAME} "
                    "not present in TEAL code"
                )
            teal_template_code = teal_template_code.replace(UPDATABLE_TEMPLATE_NAME, str(int(updatable)))

        deletable = params.get("deletable")
        if deletable is not None:
            if DELETABLE_TEMPLATE_NAME not in teal_template_code:
                raise ValueError(
                    f"Deploy-time deletability control requested for app deployment, but {DELETABLE_TEMPLATE_NAME} "
                    "not present in TEAL code"
                )
            teal_template_code = teal_template_code.replace(DELETABLE_TEMPLATE_NAME, str(int(deletable)))

        return teal_template_code

    @staticmethod
    def strip_teal_comments(teal_code: str) -> str:
        """Strip comments from TEAL code.

        :param teal_code: The TEAL code to strip comments from
        :return: The TEAL code with comments stripped

        :example:
            >>> app_manager = AppManager(algod_client)
            >>> teal_code = "RETURN 1"
            >>> stripped_teal_code = app_manager.strip_teal_comments(teal_code)
        """

        def _strip_comment(line: str) -> str:
            comment_idx = _find_unquoted_string(line, "//")
            if comment_idx is None:
                return line
            return line[:comment_idx].rstrip()

        return "\n".join(_strip_comment(line) for line in teal_code.splitlines())
