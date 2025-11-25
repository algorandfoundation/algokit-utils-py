import base64
import dataclasses
import json
from enum import IntFlag
from pathlib import Path
from typing import Any, Literal, TypeAlias, TypedDict

from typing_extensions import deprecated

from algokit_transact.models.common import StateSchema

__all__ = [
    "AppSpecStateDict",
    "Arc32Contract",
    "CallConfig",
    "DefaultArgumentDict",
    "DefaultArgumentType",
    "MethodConfigDict",
    "MethodHints",
    "OnCompleteActionName",
    "StateDict",
    "StructArgDict",
]

from algokit_abi import arc56

AppSpecStateDict: TypeAlias = dict[str, dict[str, dict]]
"""Type defining Application Specification state entries"""


class CallConfig(IntFlag):
    """Describes the type of calls a method can be used for based
    on {py:class}`algosdk.transaction.OnApplicationComplete` type"""

    NEVER = 0
    """Never handle the specified on completion type"""
    CALL = 1
    """Only handle the specified on completion type for application calls"""
    CREATE = 2
    """Only handle the specified on completion type for application create calls"""
    ALL = 3
    """Handle the specified on completion type for both create and normal application calls"""


class StructArgDict(TypedDict):
    name: str
    elements: list[list[str]]


OnCompleteActionName: TypeAlias = Literal[
    "no_op", "opt_in", "close_out", "clear_state", "update_application", "delete_application"
]
"""String literals representing on completion transaction types"""
MethodConfigDict: TypeAlias = dict[OnCompleteActionName, CallConfig]
"""Dictionary of `dict[OnCompletionActionName, CallConfig]` representing allowed actions for each on completion type"""
DefaultArgumentType: TypeAlias = Literal["abi-method", "local-state", "global-state", "constant"]
"""Literal values describing the types of default argument sources"""


class DefaultArgumentDict(TypedDict):
    """
    DefaultArgument is a container for any arguments that may
    be resolved prior to calling some target method
    """

    source: DefaultArgumentType
    data: int | str | bytes | dict


StateDict = TypedDict(  # need to use function-form of TypedDict here since "global" is a reserved keyword
    "StateDict", {"global": AppSpecStateDict, "local": AppSpecStateDict}
)


@dataclasses.dataclass(kw_only=True)
class MethodHints:
    """MethodHints provides hints to the caller about how to call the method"""

    #: hint to indicate this method can be called through Dryrun
    read_only: bool = False
    #: hint to provide names for tuple argument indices
    #: method_name=>param_name=>{name:str, elements:[str,str]}
    structs: dict[str, StructArgDict] = dataclasses.field(default_factory=dict)
    #: defaults
    default_arguments: dict[str, DefaultArgumentDict] = dataclasses.field(default_factory=dict)
    call_config: MethodConfigDict = dataclasses.field(default_factory=dict)

    def empty(self) -> bool:
        return not self.dictify()

    def dictify(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.read_only:
            d["read_only"] = True
        if self.default_arguments:
            d["default_arguments"] = self.default_arguments
        if self.structs:
            d["structs"] = self.structs
        if any(v for v in self.call_config.values() if v != CallConfig.NEVER):
            d["call_config"] = _encode_method_config(self.call_config)
        return d

    @staticmethod
    def undictify(data: dict[str, Any]) -> "MethodHints":
        return MethodHints(
            read_only=data.get("read_only", False),
            default_arguments=data.get("default_arguments", {}),
            structs=data.get("structs", {}),
            call_config=_decode_method_config(data.get("call_config", {})),
        )


def _encode_method_config(mc: MethodConfigDict) -> dict[str, str | None]:
    return {k: mc[k].name for k in sorted(mc) if mc[k] != CallConfig.NEVER}


def _decode_method_config(data: dict[OnCompleteActionName, Any]) -> MethodConfigDict:
    return {k: CallConfig[v] for k, v in data.items()}


def _encode_source(teal_text: str) -> str:
    return base64.b64encode(teal_text.encode()).decode("utf-8")


def _decode_source(b64_text: str) -> str:
    return base64.b64decode(b64_text).decode("utf-8")


def _encode_state_schema(schema: StateSchema) -> dict[str, int]:
    return {
        "num_byte_slices": schema.num_byte_slices,
        "num_uints": schema.num_uints,
    }  # type: ignore[unused-ignore]


def _decode_state_schema(data: dict[str, int]) -> StateSchema:
    return StateSchema(
        num_byte_slices=data.get("num_byte_slices", 0),
        num_uints=data.get("num_uints", 0),
    )


@deprecated("Arc32Contract is deprecated and will be removed in a future release; migrate to Arc56Contract.")
@dataclasses.dataclass(kw_only=True)
class Arc32Contract:
    """ARC-0032 application specification

    See <https://github.com/algorandfoundation/ARCs/pull/150>"""

    approval_program: str
    clear_program: str
    contract: arc56.Arc56Contract  # only contains ARC-4 subset of ARC-56
    hints: dict[str, MethodHints]
    schema: StateDict
    global_state_schema: StateSchema
    local_state_schema: StateSchema
    bare_call_config: MethodConfigDict

    def dictify(self) -> dict:
        return {
            "hints": {k: v.dictify() for k, v in self.hints.items() if not v.empty()},
            "source": {
                "approval": _encode_source(self.approval_program),
                "clear": _encode_source(self.clear_program),
            },
            "state": {
                "global": _encode_state_schema(self.global_state_schema),
                "local": _encode_state_schema(self.local_state_schema),
            },
            "schema": self.schema,
            "contract": self.contract.dictify(),
            "bare_call_config": _encode_method_config(self.bare_call_config),
        }

    def to_json(self, indent: int | None = None) -> str:
        return json.dumps(self.dictify(), indent=indent)

    @staticmethod
    def from_json(application_spec: str) -> "Arc32Contract":
        json_spec = json.loads(application_spec)
        return Arc32Contract(
            approval_program=_decode_source(json_spec["source"]["approval"]),
            clear_program=_decode_source(json_spec["source"]["clear"]),
            schema=json_spec["schema"],
            global_state_schema=_decode_state_schema(json_spec["state"]["global"]),
            local_state_schema=_decode_state_schema(json_spec["state"]["local"]),
            contract=arc56.Arc56Contract.from_dict(json_spec["contract"]),
            hints={k: MethodHints.undictify(v) for k, v in json_spec["hints"].items()},
            bare_call_config=_decode_method_config(json_spec.get("bare_call_config", {})),
        )

    def export(self, directory: Path | str | None = None) -> None:
        """Write out the artifacts generated by the application to disk.

        Writes the approval program, clear program, contract specification and application specification
        to files in the specified directory.

        :param directory: Path to the directory where the artifacts should be written. If not specified,
                        uses the current working directory
        """
        if directory is None:
            output_dir = Path.cwd()
        else:
            output_dir = Path(directory)
            output_dir.mkdir(exist_ok=True, parents=True)

        (output_dir / "approval.teal").write_text(self.approval_program)
        (output_dir / "clear.teal").write_text(self.clear_program)
        (output_dir / "contract.json").write_text(json.dumps(self.contract.dictify(), indent=4))
        (output_dir / "application.json").write_text(self.to_json())
