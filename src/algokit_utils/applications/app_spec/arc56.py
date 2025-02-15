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
    """Represents a field in a struct type."""

    name: str
    """The name of the struct field"""
    type: list[StructField] | str
    """The type of the struct field, either a string or list of StructFields"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> StructField:
        if isinstance(data["type"], list):
            data["type"] = [StructField.from_dict(item) for item in data["type"]]
        return StructField(**data)


class CallEnum(str, Enum):
    """Enum representing different call types for application transactions."""

    CLEAR_STATE = "ClearState"
    CLOSE_OUT = "CloseOut"
    DELETE_APPLICATION = "DeleteApplication"
    NO_OP = "NoOp"
    OPT_IN = "OptIn"
    UPDATE_APPLICATION = "UpdateApplication"


class CreateEnum(str, Enum):
    """Enum representing different create types for application transactions."""

    DELETE_APPLICATION = "DeleteApplication"
    NO_OP = "NoOp"
    OPT_IN = "OptIn"


@dataclass
class BareActions:
    """Represents bare call and create actions for an application."""

    call: list[CallEnum]
    """The list of allowed call actions"""
    create: list[CreateEnum]
    """The list of allowed create actions"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> BareActions:
        return BareActions(**data)


@dataclass
class ByteCode:
    """Represents the approval and clear program bytecode."""

    approval: str
    """The base64 encoded approval program bytecode"""
    clear: str
    """The base64 encoded clear program bytecode"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ByteCode:
        return ByteCode(**data)


class Compiler(str, Enum):
    """Enum representing different compiler types."""

    ALGOD = "algod"
    PUYA = "puya"


@dataclass
class CompilerVersion:
    """Represents compiler version information."""

    commit_hash: str | None = None
    """The git commit hash of the compiler"""
    major: int | None = None
    """The major version number"""
    minor: int | None = None
    """The minor version number"""
    patch: int | None = None
    """The patch version number"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CompilerVersion:
        return CompilerVersion(**data)


@dataclass
class CompilerInfo:
    """Information about the compiler used."""

    compiler: Compiler
    """The type of compiler used"""
    compiler_version: CompilerVersion
    """Version information for the compiler"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CompilerInfo:
        data["compiler_version"] = CompilerVersion.from_dict(data["compiler_version"])
        return CompilerInfo(**data)


@dataclass
class Network:
    """Network-specific application information."""

    app_id: int
    """The application ID on the network"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Network:
        return Network(**data)


@dataclass
class ScratchVariables:
    """Information about scratch space variables."""

    slot: int
    """The scratch slot number"""
    type: str
    """The type of the scratch variable"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ScratchVariables:
        return ScratchVariables(**data)


@dataclass
class Source:
    """Source code for approval and clear programs."""

    approval: str
    """The base64 encoded approval program source"""
    clear: str
    """The base64 encoded clear program source"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Source:
        return Source(**data)

    def get_decoded_approval(self) -> str:
        """Get decoded approval program source.

        :return: Decoded approval program source code
        """
        return self._decode_source(self.approval)

    def get_decoded_clear(self) -> str:
        """Get decoded clear program source.

        :return: Decoded clear program source code
        """
        return self._decode_source(self.clear)

    def _decode_source(self, b64_text: str) -> str:
        return base64.b64decode(b64_text).decode("utf-8")


@dataclass
class Global:
    """Global state schema."""

    bytes: int
    """The number of byte slices in global state"""
    ints: int
    """The number of integers in global state"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Global:
        return Global(**data)


@dataclass
class Local:
    """Local state schema."""

    bytes: int
    """The number of byte slices in local state"""
    ints: int
    """The number of integers in local state"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Local:
        return Local(**data)


@dataclass
class Schema:
    """Application state schema."""

    global_state: Global  # actual schema field is "global" since it's a reserved word
    """The global state schema"""
    local_state: Local  # actual schema field is "local" for consistency with renamed "global"
    """The local state schema"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Schema:
        global_state = Global.from_dict(data["global"])
        local_state = Local.from_dict(data["local"])
        return Schema(global_state=global_state, local_state=local_state)


@dataclass
class TemplateVariables:
    """Template variable information."""

    type: str
    """The type of the template variable"""
    value: str | None = None
    """The optional value of the template variable"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> TemplateVariables:
        return TemplateVariables(**data)


@dataclass
class EventArg:
    """Event argument information."""

    type: str
    """The type of the event argument"""
    desc: str | None = None
    """The optional description of the argument"""
    name: str | None = None
    """The optional name of the argument"""
    struct: str | None = None
    """The optional struct type name"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> EventArg:
        return EventArg(**data)


@dataclass
class Event:
    """Event information."""

    args: list[EventArg]
    """The list of event arguments"""
    name: str
    """The name of the event"""
    desc: str | None = None
    """The optional description of the event"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Event:
        data["args"] = [EventArg.from_dict(item) for item in data["args"]]
        return Event(**data)


@dataclass
class Actions:
    """Method actions information."""

    call: list[CallEnum] | None = None
    """The optional list of allowed call actions"""
    create: list[CreateEnum] | None = None
    """The optional list of allowed create actions"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Actions:
        return Actions(**data)


@dataclass
class DefaultValue:
    """Default value information for method arguments."""

    data: str
    """The default value data"""
    source: Literal["box", "global", "local", "literal", "method"]
    """The source of the default value"""
    type: str | None = None
    """The optional type of the default value"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> DefaultValue:
        return DefaultValue(**data)


@dataclass
class MethodArg:
    """Method argument information."""

    type: str
    """The type of the argument"""
    default_value: DefaultValue | None = None
    """The optional default value"""
    desc: str | None = None
    """The optional description"""
    name: str | None = None
    """The optional name"""
    struct: str | None = None
    """The optional struct type name"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> MethodArg:
        if data.get("default_value"):
            data["default_value"] = DefaultValue.from_dict(data["default_value"])
        return MethodArg(**data)


@dataclass
class Boxes:
    """Box storage requirements."""

    key: str
    """The box key"""
    read_bytes: int
    """The number of bytes to read"""
    write_bytes: int
    """The number of bytes to write"""
    app: int | None = None
    """The optional application ID"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Boxes:
        return Boxes(**data)


@dataclass
class Recommendations:
    """Method execution recommendations."""

    accounts: list[str] | None = None
    """The optional list of accounts"""
    apps: list[int] | None = None
    """The optional list of applications"""
    assets: list[int] | None = None
    """The optional list of assets"""
    boxes: Boxes | None = None
    """The optional box storage requirements"""
    inner_transaction_count: int | None = None
    """The optional inner transaction count"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Recommendations:
        if data.get("boxes"):
            data["boxes"] = Boxes.from_dict(data["boxes"])
        return Recommendations(**data)


@dataclass
class Returns:
    """Method return information."""

    type: str
    """The type of the return value"""
    desc: str | None = None
    """The optional description"""
    struct: str | None = None
    """The optional struct type name"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Returns:
        return Returns(**data)


@dataclass
class Method:
    """Method information."""

    actions: Actions
    """The allowed actions"""
    args: list[MethodArg]
    """The method arguments"""
    name: str
    """The method name"""
    returns: Returns
    """The return information"""
    desc: str | None = None
    """The optional description"""
    events: list[Event] | None = None
    """The optional list of events"""
    readonly: bool | None = None
    """The optional readonly flag"""
    recommendations: Recommendations | None = None
    """The optional execution recommendations"""

    _abi_method: AlgosdkMethod | None = None

    def __post_init__(self) -> None:
        self._abi_method = AlgosdkMethod.undictify(asdict(self))

    def to_abi_method(self) -> AlgosdkMethod:
        """Convert to ABI method.

        :raises ValueError: If underlying ABI method is not initialized
        :return: ABI method
        """
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
    """PC offset method types."""

    CBLOCKS = "cblocks"
    NONE = "none"


@dataclass
class SourceInfo:
    """Source code location information."""

    pc: list[int]
    """The list of program counter values"""
    error_message: str | None = None
    """The optional error message"""
    source: str | None = None
    """The optional source code"""
    teal: int | None = None
    """The optional TEAL version"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> SourceInfo:
        return SourceInfo(**data)


@dataclass
class StorageKey:
    """Storage key information."""

    key: str
    """The storage key"""
    key_type: str
    """The type of the key"""
    value_type: str
    """The type of the value"""
    desc: str | None = None
    """The optional description"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> StorageKey:
        return StorageKey(**data)


@dataclass
class StorageMap:
    """Storage map information."""

    key_type: str
    """The type of the map keys"""
    value_type: str
    """The type of the map values"""
    desc: str | None = None
    """The optional description"""
    prefix: str | None = None
    """The optional key prefix"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> StorageMap:
        return StorageMap(**data)


@dataclass
class Keys:
    """Storage keys for different storage types."""

    box: dict[str, StorageKey]
    """The box storage keys"""
    global_state: dict[str, StorageKey]  # actual schema field is "global" since it's a reserved word
    """The global state storage keys"""
    local_state: dict[str, StorageKey]  # actual schema field is "local" for consistency with renamed "global"
    """The local state storage keys"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Keys:
        box = {key: StorageKey.from_dict(value) for key, value in data["box"].items()}
        global_state = {key: StorageKey.from_dict(value) for key, value in data["global"].items()}
        local_state = {key: StorageKey.from_dict(value) for key, value in data["local"].items()}
        return Keys(box=box, global_state=global_state, local_state=local_state)


@dataclass
class Maps:
    """Storage maps for different storage types."""

    box: dict[str, StorageMap]
    """The box storage maps"""
    global_state: dict[str, StorageMap]  # actual schema field is "global" since it's a reserved word
    """The global state storage maps"""
    local_state: dict[str, StorageMap]  # actual schema field is "local" for consistency with renamed "global"
    """The local state storage maps"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Maps:
        box = {key: StorageMap.from_dict(value) for key, value in data["box"].items()}
        global_state = {key: StorageMap.from_dict(value) for key, value in data["global"].items()}
        local_state = {key: StorageMap.from_dict(value) for key, value in data["local"].items()}
        return Maps(box=box, global_state=global_state, local_state=local_state)


@dataclass
class State:
    """Application state information."""

    keys: Keys
    """The storage keys"""
    maps: Maps
    """The storage maps"""
    schema: Schema
    """The state schema"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> State:
        data["keys"] = Keys.from_dict(data["keys"])
        data["maps"] = Maps.from_dict(data["maps"])
        data["schema"] = Schema.from_dict(data["schema"])
        return State(**data)


@dataclass
class ProgramSourceInfo:
    """Program source information."""

    pc_offset_method: PcOffsetMethod
    """The PC offset method"""
    source_info: list[SourceInfo]
    """The list of source info entries"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ProgramSourceInfo:
        data["source_info"] = [SourceInfo.from_dict(item) for item in data["source_info"]]
        return ProgramSourceInfo(**data)


@dataclass
class SourceInfoModel:
    """Source information for approval and clear programs."""

    approval: ProgramSourceInfo
    """The approval program source info"""
    clear: ProgramSourceInfo
    """The clear program source info"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> SourceInfoModel:
        data["approval"] = ProgramSourceInfo.from_dict(data["approval"])
        data["clear"] = ProgramSourceInfo.from_dict(data["clear"])
        return SourceInfoModel(**data)


# constants that define which parent keys mark a region whose inner keys should remain unchanged.
PROTECTED_TOP_DICTS = {"networks", "scratch_variables", "template_variables", "structs"}
STATE_PROTECTED_PARENTS = {"keys", "maps"}
STATE_PROTECTED_CHILDREN = {"global", "local", "box"}


def _is_protected_path(path: tuple[str, ...]) -> bool:
    """
    Return True if the current recursion path indicates that we are inside a protected dictionary,
    meaning that the keys should be left unchanged.
    """
    return (len(path) >= 2 and path[-2] in STATE_PROTECTED_PARENTS and path[-1] in STATE_PROTECTED_CHILDREN) or (  # noqa: PLR2004
        len(path) >= 1 and path[-1] in PROTECTED_TOP_DICTS
    )


def _dict_keys_to_snake_case(value: Any, path: tuple[str, ...] = ()) -> Any:  # noqa: ANN401
    """Recursively convert dictionary keys to snake_case except in protected sections.

    A dictionary is not converted if it is directly under:
      - keys/maps sections ("global", "local", "box")
      - or one of the top-level keys ("networks", "scratchVariables", "templateVariables", "structs")
    (Note that once converted the parent key names become snake_case.)
    """
    import re

    def camel_to_snake(s: str) -> str:
        # Use a regular expression to insert an underscore before capital letters (except at start).
        return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()

    if isinstance(value, dict):
        protected = _is_protected_path(path)
        new_dict = {}
        for key, val in value.items():
            new_key = key if protected else camel_to_snake(key)
            new_dict[new_key] = _dict_keys_to_snake_case(val, (*path, new_key))
        return new_dict
    elif isinstance(value, list):
        return [_dict_keys_to_snake_case(item, path) for item in value]
    else:
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
    """ARC-0056 application specification.

    See https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0056.md
    """

    arcs: list[int]
    """The list of supported ARC version numbers"""
    bare_actions: BareActions
    """The bare call and create actions"""
    methods: list[Method]
    """The list of contract methods"""
    name: str
    """The contract name"""
    state: State
    """The contract state information"""
    structs: dict[str, list[StructField]]
    """The contract struct definitions"""
    byte_code: ByteCode | None = None
    """The optional bytecode for approval and clear programs"""
    compiler_info: CompilerInfo | None = None
    """The optional compiler information"""
    desc: str | None = None
    """The optional contract description"""
    events: list[Event] | None = None
    """The optional list of contract events"""
    networks: dict[str, Network] | None = None
    """The optional network deployment information"""
    scratch_variables: dict[str, ScratchVariables] | None = None
    """The optional scratch variable information"""
    source: Source | None = None
    """The optional source code"""
    source_info: SourceInfoModel | None = None
    """The optional source code information"""
    template_variables: dict[str, TemplateVariables] | None = None
    """The optional template variable information"""

    @staticmethod
    def from_dict(application_spec: dict) -> Arc56Contract:
        """Create Arc56Contract from dictionary.

        :param application_spec: Dictionary containing contract specification
        :return: Arc56Contract instance
        """
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
