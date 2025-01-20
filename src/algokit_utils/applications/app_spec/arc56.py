from __future__ import annotations

import base64
import json
from base64 import b64encode
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Literal, overload

import algosdk
from algosdk.abi import Method as AlgosdkMethod

from algokit_utils.applications.app_spec.arc32 import Arc32Contract

__all__ = [
    "Actions",
    "Arc56Contract",
    "BareActions",
    "Boxes",
    "ByteCode",
    "CallEnum",
    "Compiler",
    "CompilerInfo",
    "CompilerVersion",
    "CreateEnum",
    "DefaultValue",
    "Event",
    "EventArg",
    "Global",
    "Keys",
    "Local",
    "Maps",
    "Method",
    "MethodArg",
    "Network",
    "PcOffsetMethod",
    "ProgramSourceInfo",
    "Recommendations",
    "Returns",
    "Schema",
    "ScratchVariables",
    "Source",
    "SourceInfo",
    "SourceInfoModel",
    "State",
    "StorageKey",
    "StorageMap",
    "StructField",
    "TemplateVariables",
]


class _ActionType(str, Enum):
    CALL = "CALL"
    CREATE = "CREATE"


@dataclass
class StructField:
    name: str
    type: list[StructField] | str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> StructField:
        if isinstance(data["type"], list):
            data["type"] = [StructField.from_dict(item) for item in data["type"]]
        return StructField(**data)


class CallEnum(str, Enum):
    CLEAR_STATE = "ClearState"
    CLOSE_OUT = "CloseOut"
    DELETE_APPLICATION = "DeleteApplication"
    NO_OP = "NoOp"
    OPT_IN = "OptIn"
    UPDATE_APPLICATION = "UpdateApplication"


class CreateEnum(str, Enum):
    DELETE_APPLICATION = "DeleteApplication"
    NO_OP = "NoOp"
    OPT_IN = "OptIn"


@dataclass
class BareActions:
    call: list[CallEnum]
    create: list[CreateEnum]

    @staticmethod
    def from_dict(data: dict[str, Any]) -> BareActions:
        return BareActions(**data)


@dataclass
class ByteCode:
    approval: str
    clear: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ByteCode:
        return ByteCode(**data)


class Compiler(str, Enum):
    ALGOD = "algod"
    PUYA = "puya"


@dataclass
class CompilerVersion:
    commit_hash: str | None = None
    major: int | None = None
    minor: int | None = None
    patch: int | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CompilerVersion:
        return CompilerVersion(**data)


@dataclass
class CompilerInfo:
    compiler: Compiler
    compiler_version: CompilerVersion

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CompilerInfo:
        data["compiler_version"] = CompilerVersion.from_dict(data["compiler_version"])
        return CompilerInfo(**data)


@dataclass
class Network:
    app_id: int

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Network:
        return Network(**data)


@dataclass
class ScratchVariables:
    slot: int
    type: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ScratchVariables:
        return ScratchVariables(**data)


@dataclass
class Source:
    approval: str
    clear: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Source:
        return Source(**data)

    def get_decoded_approval(self) -> str:
        return self._decode_source(self.approval)

    def get_decoded_clear(self) -> str:
        return self._decode_source(self.clear)

    def _decode_source(self, b64_text: str) -> str:
        return base64.b64decode(b64_text).decode("utf-8")


@dataclass
class Global:
    bytes: int
    ints: int

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Global:
        return Global(**data)


@dataclass
class Local:
    bytes: int
    ints: int

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Local:
        return Local(**data)


@dataclass
class Schema:
    global_state: Global  # actual schema field is "global" since it's a reserved word
    local_state: Local  # actual schema field is "local" for consistency with renamed "global"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Schema:
        global_state = Global.from_dict(data["global"])
        local_state = Local.from_dict(data["local"])
        return Schema(global_state=global_state, local_state=local_state)


@dataclass
class TemplateVariables:
    type: str
    value: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> TemplateVariables:
        return TemplateVariables(**data)


@dataclass
class EventArg:
    type: str
    desc: str | None = None
    name: str | None = None
    struct: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> EventArg:
        return EventArg(**data)


@dataclass
class Event:
    args: list[EventArg]
    name: str
    desc: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Event:
        data["args"] = [EventArg.from_dict(item) for item in data["args"]]
        return Event(**data)


@dataclass
class Actions:
    call: list[CallEnum] | None = None
    create: list[CreateEnum] | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Actions:
        return Actions(**data)


@dataclass
class DefaultValue:
    data: str
    source: Literal["box", "global", "local", "literal", "method"]
    type: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> DefaultValue:
        return DefaultValue(**data)


@dataclass
class MethodArg:
    type: str
    default_value: DefaultValue | None = None
    desc: str | None = None
    name: str | None = None
    struct: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> MethodArg:
        if data.get("default_value"):
            data["default_value"] = DefaultValue.from_dict(data["default_value"])
        return MethodArg(**data)


@dataclass
class Boxes:
    key: str
    read_bytes: int
    write_bytes: int
    app: int | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Boxes:
        return Boxes(**data)


@dataclass
class Recommendations:
    accounts: list[str] | None = None
    apps: list[int] | None = None
    assets: list[int] | None = None
    boxes: Boxes | None = None
    inner_transaction_count: int | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Recommendations:
        if data.get("boxes"):
            data["boxes"] = Boxes.from_dict(data["boxes"])
        return Recommendations(**data)


@dataclass
class Returns:
    type: str
    desc: str | None = None
    struct: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Returns:
        return Returns(**data)


@dataclass
class Method:
    actions: Actions
    args: list[MethodArg]
    name: str
    returns: Returns
    desc: str | None = None
    events: list[Event] | None = None
    readonly: bool | None = None
    recommendations: Recommendations | None = None

    _abi_method: AlgosdkMethod | None = None

    def __post_init__(self) -> None:
        self._abi_method = AlgosdkMethod.undictify(asdict(self))

    def to_abi_method(self) -> AlgosdkMethod:
        if self._abi_method is None:
            raise ValueError("Underlying core ABI method class is not initialized!")
        return self._abi_method

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Method:
        data["actions"] = Actions.from_dict(data["actions"])
        data["args"] = [MethodArg.from_dict(item) for item in data["args"]]
        data["returns"] = Returns.from_dict(data["returns"])
        if data.get("events"):
            data["events"] = [Event.from_dict(item) for item in data["events"]]
        if data.get("recommendations"):
            data["recommendations"] = Recommendations.from_dict(data["recommendations"])
        return Method(**data)


class PcOffsetMethod(str, Enum):
    CBLOCKS = "cblocks"
    NONE = "none"


@dataclass
class SourceInfo:
    pc: list[int]
    error_message: str | None = None
    source: str | None = None
    teal: int | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> SourceInfo:
        return SourceInfo(**data)


@dataclass
class StorageKey:
    key: str
    key_type: str
    value_type: str
    desc: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> StorageKey:
        return StorageKey(**data)


@dataclass
class StorageMap:
    key_type: str
    value_type: str
    desc: str | None = None
    prefix: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> StorageMap:
        return StorageMap(**data)


@dataclass
class Keys:
    box: dict[str, StorageKey]
    global_state: dict[str, StorageKey]  # actual schema field is "global" since it's a reserved word
    local_state: dict[str, StorageKey]  # actual schema field is "local" for consistency with renamed "global"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Keys:
        box = {key: StorageKey.from_dict(value) for key, value in data["box"].items()}
        global_state = {key: StorageKey.from_dict(value) for key, value in data["global"].items()}
        local_state = {key: StorageKey.from_dict(value) for key, value in data["local"].items()}
        return Keys(box=box, global_state=global_state, local_state=local_state)


@dataclass
class Maps:
    box: dict[str, StorageMap]
    global_state: dict[str, StorageMap]  # actual schema field is "global" since it's a reserved word
    local_state: dict[str, StorageMap]  # actual schema field is "local" for consistency with renamed "global"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Maps:
        box = {key: StorageMap.from_dict(value) for key, value in data["box"].items()}
        global_state = {key: StorageMap.from_dict(value) for key, value in data["global"].items()}
        local_state = {key: StorageMap.from_dict(value) for key, value in data["local"].items()}
        return Maps(box=box, global_state=global_state, local_state=local_state)


@dataclass
class State:
    keys: Keys
    maps: Maps
    schema: Schema

    @staticmethod
    def from_dict(data: dict[str, Any]) -> State:
        data["keys"] = Keys.from_dict(data["keys"])
        data["maps"] = Maps.from_dict(data["maps"])
        data["schema"] = Schema.from_dict(data["schema"])
        return State(**data)


@dataclass
class ProgramSourceInfo:
    pc_offset_method: PcOffsetMethod
    source_info: list[SourceInfo]

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ProgramSourceInfo:
        data["source_info"] = [SourceInfo.from_dict(item) for item in data["source_info"]]
        return ProgramSourceInfo(**data)


@dataclass
class SourceInfoModel:
    approval: ProgramSourceInfo
    clear: ProgramSourceInfo

    @staticmethod
    def from_dict(data: dict[str, Any]) -> SourceInfoModel:
        data["approval"] = ProgramSourceInfo.from_dict(data["approval"])
        data["clear"] = ProgramSourceInfo.from_dict(data["clear"])
        return SourceInfoModel(**data)


def _dict_keys_to_snake_case(
    value: Any,  # noqa: ANN401
) -> Any:  # noqa: ANN401
    def camel_to_snake(s: str) -> str:
        return "".join(["_" + c.lower() if c.isupper() else c for c in s]).lstrip("_")

    match value:
        case dict():
            new_dict: dict[str, Any] = {}
            for key, val in value.items():
                new_dict[camel_to_snake(str(key))] = _dict_keys_to_snake_case(val)
            return new_dict
        case list():
            return [_dict_keys_to_snake_case(item) for item in value]
        case _:
            return value


class _Arc32ToArc56Converter:
    def __init__(self, arc32_application_spec: str):
        self.arc32 = json.loads(arc32_application_spec)

    def convert(self) -> Arc56Contract:
        source_data = self.arc32.get("source")
        return Arc56Contract(
            name=self.arc32["contract"]["name"],
            desc=self.arc32["contract"].get("desc"),
            arcs=[],
            methods=self._convert_methods(self.arc32),
            structs=self._convert_structs(self.arc32),
            state=self._convert_state(self.arc32),
            source=Source(**source_data) if source_data else None,
            bare_actions=BareActions(
                call=self._convert_actions(self.arc32.get("bare_call_config"), _ActionType.CALL),
                create=self._convert_actions(self.arc32.get("bare_call_config"), _ActionType.CREATE),
            ),
        )

    def _convert_storage_keys(self, schema: dict) -> dict[str, StorageKey]:
        """Convert ARC32 schema declared fields to ARC56 storage keys."""
        return {
            name: StorageKey(
                key=b64encode(field["key"].encode()).decode(),
                key_type="AVMString",
                value_type="AVMUint64" if field["type"] == "uint64" else "AVMBytes",
                desc=field.get("descr"),
            )
            for name, field in schema.items()
        }

    def _convert_state(self, arc32: dict) -> State:
        """Convert ARC32 state and schema to ARC56 state specification."""
        state_data = arc32.get("state", {})
        return State(
            schema=Schema(
                global_state=Global(
                    ints=state_data.get("global", {}).get("num_uints", 0),
                    bytes=state_data.get("global", {}).get("num_byte_slices", 0),
                ),
                local_state=Local(
                    ints=state_data.get("local", {}).get("num_uints", 0),
                    bytes=state_data.get("local", {}).get("num_byte_slices", 0),
                ),
            ),
            keys=Keys(
                global_state=self._convert_storage_keys(arc32.get("schema", {}).get("global", {}).get("declared", {})),
                local_state=self._convert_storage_keys(arc32.get("schema", {}).get("local", {}).get("declared", {})),
                box={},
            ),
            maps=Maps(global_state={}, local_state={}, box={}),
        )

    def _convert_structs(self, arc32: dict) -> dict[str, list[StructField]]:
        """Extract and convert struct definitions from hints."""
        return {
            struct["name"]: [StructField(name=elem[0], type=elem[1]) for elem in struct["elements"]]
            for hint in arc32.get("hints", {}).values()
            for struct in hint.get("structs", {}).values()
        }

    def _convert_default_value(self, arg_type: str, default_arg: dict[str, Any] | None) -> DefaultValue | None:
        """Convert ARC32 default argument to ARC56 format."""
        if not default_arg or not default_arg.get("source"):
            return None

        source_mapping = {
            "constant": "literal",
            "global-state": "global",
            "local-state": "local",
            "abi-method": "method",
        }

        mapped_source = source_mapping.get(default_arg["source"])
        if not mapped_source:
            return None
        elif mapped_source == "method":
            return DefaultValue(
                source=mapped_source,  # type: ignore[arg-type]
                data=default_arg.get("data", {}).get("name"),
            )

        arg_data = default_arg.get("data")

        if isinstance(arg_data, int):
            arg_data = algosdk.abi.ABIType.from_string("uint64").encode(arg_data)
        elif isinstance(arg_data, str):
            arg_data = arg_data.encode()
        else:
            raise ValueError(f"Invalid default argument data type: {type(arg_data)}")

        return DefaultValue(
            source=mapped_source,  # type: ignore[arg-type]
            data=base64.b64encode(arg_data).decode("utf-8"),
            type=arg_type if arg_type != "string" else "AVMString",
        )

    @overload
    def _convert_actions(self, config: dict | None, action_type: Literal[_ActionType.CALL]) -> list[CallEnum]: ...

    @overload
    def _convert_actions(self, config: dict | None, action_type: Literal[_ActionType.CREATE]) -> list[CreateEnum]: ...

    def _convert_actions(self, config: dict | None, action_type: _ActionType) -> Sequence[CallEnum | CreateEnum]:
        """Extract supported actions from call config."""
        if not config:
            return []

        actions: list[CallEnum | CreateEnum] = []
        mappings = {
            "no_op": (CallEnum.NO_OP, CreateEnum.NO_OP),
            "opt_in": (CallEnum.OPT_IN, CreateEnum.OPT_IN),
            "close_out": (CallEnum.CLOSE_OUT, None),
            "delete_application": (CallEnum.DELETE_APPLICATION, CreateEnum.DELETE_APPLICATION),
            "update_application": (CallEnum.UPDATE_APPLICATION, None),
        }

        for action, (call_enum, create_enum) in mappings.items():
            if action in config and config[action] in ["ALL", action_type]:
                if action_type == "CALL" and call_enum:
                    actions.append(call_enum)
                elif action_type == "CREATE" and create_enum:
                    actions.append(create_enum)

        return actions

    def _convert_method_actions(self, hint: dict | None) -> Actions:
        """Convert method call config to ARC56 actions."""
        config = hint.get("call_config", {}) if hint else {}
        return Actions(
            call=self._convert_actions(config, _ActionType.CALL),
            create=self._convert_actions(config, _ActionType.CREATE),
        )

    def _convert_methods(self, arc32: dict) -> list[Method]:
        """Convert ARC32 methods to ARC56 format."""
        methods = []
        contract = arc32["contract"]
        hints = arc32.get("hints", {})

        for method in contract["methods"]:
            args_sig = ",".join(a["type"] for a in method["args"])
            signature = f"{method['name']}({args_sig}){method['returns']['type']}"
            hint = hints.get(signature, {})

            methods.append(
                Method(
                    name=method["name"],
                    desc=method.get("desc"),
                    readonly=hint.get("read_only"),
                    args=[
                        MethodArg(
                            name=arg.get("name"),
                            type=arg["type"],
                            desc=arg.get("desc"),
                            struct=hint.get("structs", {}).get(arg.get("name", ""), {}).get("name"),
                            default_value=self._convert_default_value(
                                arg["type"], hint.get("default_arguments", {}).get(arg.get("name"))
                            ),
                        )
                        for arg in method["args"]
                    ],
                    returns=Returns(
                        type=method["returns"]["type"],
                        desc=method["returns"].get("desc"),
                        struct=hint.get("structs", {}).get("output", {}).get("name"),
                    ),
                    actions=self._convert_method_actions(hint),
                    events=[],  # ARC32 doesn't specify events
                )
            )
        return methods


def _arc56_dict_factory() -> Callable[[list[tuple[str, Any]]], dict[str, Any]]:
    """Creates a dict factory that handles ARC-56 JSON field naming conventions."""

    word_map = {"global_state": "global", "local_state": "local"}
    blocklist = ["_abi_method"]

    def to_camel(key: str) -> str:
        key = word_map.get(key, key)
        words = key.split("_")
        return words[0] + "".join(word.capitalize() for word in words[1:])

    def dict_factory(entries: list[tuple[str, Any]]) -> dict[str, Any]:
        return {to_camel(k): v for k, v in entries if v is not None and k not in blocklist}

    return dict_factory


@dataclass
class Arc56Contract:
    """ARC-0056 application specification
    See https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0056.md
    """

    arcs: list[int]
    bare_actions: BareActions
    methods: list[Method]
    name: str
    state: State
    structs: dict[str, list[StructField]]
    byte_code: ByteCode | None = None
    compiler_info: CompilerInfo | None = None
    desc: str | None = None
    events: list[Event] | None = None
    networks: dict[str, Network] | None = None
    scratch_variables: dict[str, ScratchVariables] | None = None
    source: Source | None = None
    source_info: SourceInfoModel | None = None
    template_variables: dict[str, TemplateVariables] | None = None

    @staticmethod
    def from_dict(application_spec: dict) -> Arc56Contract:
        data = _dict_keys_to_snake_case(application_spec)
        data["bare_actions"] = BareActions.from_dict(data["bare_actions"])
        data["methods"] = [Method.from_dict(item) for item in data["methods"]]
        data["state"] = State.from_dict(data["state"])
        data["structs"] = {
            key: [StructField.from_dict(item) for item in value] for key, value in application_spec["structs"].items()
        }
        if data.get("byte_code"):
            data["byte_code"] = ByteCode.from_dict(data["byte_code"])
        if data.get("compiler_info"):
            data["compiler_info"] = CompilerInfo.from_dict(data["compiler_info"])
        if data.get("events"):
            data["events"] = [Event.from_dict(item) for item in data["events"]]
        if data.get("networks"):
            data["networks"] = {key: Network.from_dict(value) for key, value in data["networks"].items()}
        if data.get("scratch_variables"):
            data["scratch_variables"] = {
                key: ScratchVariables.from_dict(value) for key, value in data["scratch_variables"].items()
            }
        if data.get("source"):
            data["source"] = Source.from_dict(data["source"])
        if data.get("source_info"):
            data["source_info"] = SourceInfoModel.from_dict(data["source_info"])
        if data.get("template_variables"):
            data["template_variables"] = {
                key: TemplateVariables.from_dict(value) for key, value in data["template_variables"].items()
            }
        return Arc56Contract(**data)

    @staticmethod
    def from_json(application_spec: str) -> Arc56Contract:
        return Arc56Contract.from_dict(json.loads(application_spec))

    @staticmethod
    def from_arc32(arc32_application_spec: str | Arc32Contract) -> Arc56Contract:
        return _Arc32ToArc56Converter(
            arc32_application_spec.to_json()
            if isinstance(arc32_application_spec, Arc32Contract)
            else arc32_application_spec
        ).convert()

    @staticmethod
    def get_abi_struct_from_abi_tuple(
        decoded_tuple: Any,  # noqa: ANN401
        struct_fields: list[StructField],
        structs: dict[str, list[StructField]],
    ) -> dict[str, Any]:
        result = {}
        for i, field in enumerate(struct_fields):
            key = field.name
            field_type = field.type
            value = decoded_tuple[i]
            if isinstance(field_type, str):
                if field_type in structs:
                    value = Arc56Contract.get_abi_struct_from_abi_tuple(value, structs[field_type], structs)
            elif isinstance(field_type, list):
                value = Arc56Contract.get_abi_struct_from_abi_tuple(value, field_type, structs)
            result[key] = value
        return result

    def to_json(self, indent: int | None = None) -> str:
        return json.dumps(self.dictify(), indent=indent)

    def dictify(self) -> dict:
        return asdict(self, dict_factory=_arc56_dict_factory())

    def get_arc56_method(self, method_name_or_signature: str) -> Method:
        if "(" not in method_name_or_signature:
            # Filter by method name
            methods = [m for m in self.methods if m.name == method_name_or_signature]
            if not methods:
                raise ValueError(f"Unable to find method {method_name_or_signature} in {self.name} app.")
            if len(methods) > 1:
                signatures = [AlgosdkMethod.undictify(m.__dict__).get_signature() for m in self.methods]
                raise ValueError(
                    f"Received a call to method {method_name_or_signature} in contract {self.name}, "
                    f"but this resolved to multiple methods; please pass in an ABI signature instead: "
                    f"{', '.join(signatures)}"
                )
            method = methods[0]
        else:
            # Find by signature
            method = None
            for m in self.methods:
                abi_method = AlgosdkMethod.undictify(asdict(m))
                if abi_method.get_signature() == method_name_or_signature:
                    method = m
                    break

        if method is None:
            raise ValueError(f"Unable to find method {method_name_or_signature} in {self.name} app.")

        return method
