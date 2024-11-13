import base64
from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, TypeAlias

import algosdk
import algosdk.atomic_transaction_composer
import algosdk.box_reference
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.logic import get_application_address
from algosdk.v2client import algod

from algokit_utils.models.abi import ABIValue
from algokit_utils.models.application import DELETABLE_TEMPLATE_NAME, UPDATABLE_TEMPLATE_NAME


@dataclass(frozen=True)
class BoxName:
    name: str
    name_raw: bytes
    name_base64: str


@dataclass(frozen=True)
class AppState:
    key_raw: bytes
    key_base64: str
    value_raw: bytes | None
    value_base64: str | None
    value: str | int


class DataTypeFlag(IntEnum):
    BYTES = 1
    UINT = 2


TealTemplateParams: TypeAlias = Mapping[str, str | int | bytes] | dict[str, str | int | bytes]


@dataclass(frozen=True)
class AppInformation:
    app_id: int
    app_address: str
    approval_program: bytes
    clear_state_program: bytes
    creator: str
    global_state: dict[str, AppState]
    local_ints: int
    local_byte_slices: int
    global_ints: int
    global_byte_slices: int
    extra_program_pages: int | None


@dataclass(frozen=True)
class CompiledTeal:
    teal: str
    compiled: bytes
    compiled_hash: str
    compiled_base64_to_bytes: bytes
    source_map: algosdk.source_map.SourceMap | None


class AppCompilationResult:
    compiled_approval: CompiledTeal
    compiled_clear: CompiledTeal


BoxIdentifier = str | bytes | AccountTransactionSigner


def _is_valid_token_character(char: str) -> bool:
    return char.isalnum() or char == "_"


def _last_token_base64(line: str, idx: int) -> bool:
    try:
        *_, last = line[:idx].split()
    except ValueError:
        return False
    return last in ("base64", "b64")


def _find_template_token(line: str, token: str, start: int = 0, end: int = -1) -> int | None:
    """Find the first template token within a line of TEAL. Only matches outside of quotes are returned.
    Only full token matches are returned, i.e. TMPL_STR will not match against TMPL_STRING
    Returns None if not found"""
    if end < 0:
        end = len(line)

    idx = start
    while idx < end:
        token_idx = _find_unquoted_string(line, token, idx, end)
        if token_idx is None:
            break
        trailing_idx = token_idx + len(token)
        if (token_idx == 0 or not _is_valid_token_character(line[token_idx - 1])) and (  # word boundary at start
            trailing_idx >= len(line) or not _is_valid_token_character(line[trailing_idx])  # word boundary at end
        ):
            return token_idx
        idx = trailing_idx
    return None


def _find_unquoted_string(line: str, token: str, start: int = 0, end: int = -1) -> int | None:
    """Find the first string within a line of TEAL. Only matches outside of quotes and base64 are returned.
    Returns None if not found"""

    if end < 0:
        end = len(line)
    idx = start
    in_quotes = in_base64 = False
    while idx < end:
        current_char = line[idx]
        match current_char:
            # enter base64
            case " " | "(" if not in_quotes and _last_token_base64(line, idx):
                in_base64 = True
            # exit base64
            case " " | ")" if not in_quotes and in_base64:
                in_base64 = False
            # escaped char
            case "\\" if in_quotes:
                # skip next character
                idx += 1
            # quote boundary
            case '"':
                in_quotes = not in_quotes
            # can test for match
            case _ if not in_quotes and not in_base64 and line.startswith(token, idx):
                # only match if not in quotes and string matches
                return idx
        idx += 1
    return None


def _replace_template_variable(program_lines: list[str], template_variable: str, value: str) -> tuple[list[str], int]:
    result: list[str] = []
    match_count = 0
    token = f"TMPL_{template_variable}"
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
    def __init__(self, algod_client: algod.AlgodClient):
        self._algod = algod_client
        self._compilation_results: dict[str, CompiledTeal] = {}

    def compile_teal(self, teal_code: str) -> CompiledTeal:
        if teal_code in self._compilation_results:
            return self._compilation_results[teal_code]

        compiled = self._algod.compile(teal_code, source_map=True)
        result = CompiledTeal(
            teal=teal_code,
            compiled=compiled["result"],
            compiled_hash=compiled["hash"],
            compiled_base64_to_bytes=base64.b64decode(compiled["result"]),
            source_map=compiled.get("sourcemap"),
        )
        self._compilation_results[teal_code] = result
        return result

    def compile_teal_template(
        self,
        teal_template_code: str,
        template_params: TealTemplateParams | None = None,
        deployment_metadata: dict[str, bool] | None = None,
    ) -> CompiledTeal:
        teal_code = AppManager.strip_teal_comments(teal_template_code)
        teal_code = AppManager.replace_template_variables(teal_code, template_params or {})

        if deployment_metadata:
            teal_code = AppManager.replace_teal_template_deploy_time_control_params(teal_code, deployment_metadata)

        return self.compile_teal(teal_code)

    def get_compilation_result(self, teal_code: str) -> CompiledTeal | None:
        return self._compilation_results.get(teal_code)

    def get_by_id(self, app_id: int) -> AppInformation:
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
        return self.get_by_id(app_id).global_state

    def get_local_state(self, app_id: int, address: str) -> dict[str, AppState]:
        app_info = self._algod.account_application_info(address, app_id)
        assert isinstance(app_info, dict)
        if not app_info.get("app-local-state", {}).get("key-value"):
            raise ValueError("Couldn't find local state")
        return self.decode_app_state(app_info["app-local-state"]["key-value"])

    def get_box_names(self, app_id: int) -> list[BoxName]:
        box_result = self._algod.application_boxes(app_id)
        assert isinstance(box_result, dict)
        return [
            BoxName(
                name_raw=base64.b64decode(b["name"]),
                name_base64=b["name"],
                name=base64.b64decode(b["name"]).decode("utf-8"),
            )
            for b in box_result["boxes"]
        ]

    def get_box_value(self, app_id: int, box_name: BoxIdentifier) -> bytes:
        name = b""
        if isinstance(box_name, str):
            name = box_name.encode("utf-8")
        elif isinstance(box_name, bytes):
            name = box_name
        elif isinstance(box_name, AccountTransactionSigner):
            name = algosdk.encoding.decode_address(algosdk.account.address_from_private_key(box_name.private_key))
        else:
            raise ValueError(f"Invalid box identifier type: {type(box_name)}")

        box_result = self._algod.application_box_by_name(app_id, name)
        assert isinstance(box_result, dict)
        return base64.b64decode(box_result["value"])

    def get_box_values(self, app_id: int, box_names: list[BoxIdentifier]) -> list[bytes]:
        return [self.get_box_value(app_id, box_name) for box_name in box_names]

    def get_box_value_from_abi_type(
        self, app_id: int, box_name: BoxIdentifier, abi_type: algosdk.abi.ABIType
    ) -> ABIValue:
        value = self.get_box_value(app_id, box_name)
        try:
            return abi_type.decode(value)  # type: ignore[no-any-return]
        except Exception as e:
            raise ValueError(f"Failed to decode box value {value.decode('utf-8')} with ABI type {abi_type}") from e

    def get_box_values_from_abi_type(
        self, app_id: int, box_names: list[BoxIdentifier], abi_type: algosdk.abi.ABIType
    ) -> list[ABIValue]:
        return [self.get_box_value_from_abi_type(app_id, box_name, abi_type) for box_name in box_names]

    @staticmethod
    def get_abi_return(
        confirmation: algosdk.v2client.algod.AlgodResponseType, method: algosdk.abi.Method | None = None
    ) -> ABIValue | None:
        """Get the ABI return value from a transaction confirmation."""
        if not method:
            return None

        # Use the SDK's built-in ABI result parsing
        atc = algosdk.atomic_transaction_composer.AtomicTransactionComposer()
        abi_result = atc.parse_result(
            method,  # Map of transaction index to ABI method
            "dummy_txn",  # List of transaction info
            confirmation,  # type: ignore[arg-type]
        )

        if not abi_result:
            return None

        return abi_result.return_value  # type: ignore[no-any-return]

    @staticmethod
    def decode_app_state(state: list[dict[str, Any]]) -> dict[str, AppState]:
        state_values: dict[str, AppState] = {}

        for state_val in state:
            key_base64 = state_val["key"]
            key_raw = base64.b64decode(key_base64)
            key = key_raw.decode("utf-8")
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
                    value=value_raw.decode("utf-8"),
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
    def replace_teal_template_deploy_time_control_params(teal_template_code: str, params: dict[str, bool]) -> str:
        if params.get("updatable") is not None:
            if UPDATABLE_TEMPLATE_NAME not in teal_template_code:
                raise ValueError(
                    f"Deploy-time updatability control requested for app deployment, but {UPDATABLE_TEMPLATE_NAME} "
                    "not present in TEAL code"
                )
            teal_template_code = teal_template_code.replace(UPDATABLE_TEMPLATE_NAME, str(int(params["updatable"])))

        if params.get("deletable") is not None:
            if DELETABLE_TEMPLATE_NAME not in teal_template_code:
                raise ValueError(
                    f"Deploy-time deletability control requested for app deployment, but {DELETABLE_TEMPLATE_NAME} "
                    "not present in TEAL code"
                )
            teal_template_code = teal_template_code.replace(DELETABLE_TEMPLATE_NAME, str(int(params["deletable"])))

        return teal_template_code

    @staticmethod
    def strip_teal_comments(teal_code: str) -> str:
        def _strip_comment(line: str) -> str:
            comment_idx = _find_unquoted_string(line, "//")
            if comment_idx is None:
                return line
            return line[:comment_idx].rstrip()

        return "\n".join(_strip_comment(line) for line in teal_code.splitlines())
