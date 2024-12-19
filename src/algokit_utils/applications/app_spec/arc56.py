import json
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Literal, TypeAlias

import algosdk

__all__ = [
    "Arc56Contract",
    "Arc56ContractState",
    "Arc56Method",
    "Arc56MethodArg",
    "Arc56MethodReturnType",
    "BoxRecommendation",
    "DefaultValue",
    "DefaultValueSource",
    "Method",
    "MethodActions",
    "MethodArg",
    "MethodReturns",
    "Recommendations",
]


# ===== ARCs =====

# Define type aliases
ABITypeAlias: TypeAlias = str
ABIArgumentType: TypeAlias = algosdk.abi.ABIType | algosdk.abi.ABITransactionType | algosdk.abi.ABIReferenceType
StructName: TypeAlias = str
AVMBytes = Literal["AVMBytes"]
AVMString = Literal["AVMString"]
AVMUint64 = Literal["AVMUint64"]
AVMType = AVMBytes | AVMString | AVMUint64
OnCompleteAction = Literal["NoOp", "OptIn", "CloseOut", "ClearState", "UpdateApplication", "DeleteApplication"]
DefaultValueSource = Literal["box", "global", "local", "literal", "method"]


def _convert_key_to_snake_case(name: str) -> str:
    import re

    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _convert_keys_to_snake_case(obj: Any) -> Any:  # noqa: ANN401
    if isinstance(obj, dict):
        return {_convert_key_to_snake_case(k): _convert_keys_to_snake_case(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_keys_to_snake_case(item) for item in obj]
    return obj


class _SerializableBaseClass:
    """
    A base class that provides a generic `dictify` method to convert dataclass instances
    into dictionaries recursively.
    """

    def to_dict(self) -> dict[str, Any]:
        def serialize(obj: Any) -> dict[str, Any] | list[Any] | Any:  # noqa: ANN401
            if is_dataclass(obj) and not isinstance(obj, type):
                return {k: serialize(v) for k, v in asdict(obj).items()}
            elif isinstance(obj, algosdk.abi.ABIType):
                return str(obj)
            elif isinstance(obj, list):
                return [serialize(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            else:
                return obj

        result = serialize(self)
        if not isinstance(result, dict):
            raise TypeError("Serialized object is not a dictionary.")
        return result


@dataclass(kw_only=True)
class StructField:
    name: str
    type: ABITypeAlias | StructName | list["StructField"]


@dataclass(kw_only=True)
class StorageKey:
    desc: str | None
    key_type: ABITypeAlias | AVMType | StructName
    value_type: ABITypeAlias | AVMType | StructName
    key: str  # base64 encoded bytes


@dataclass(kw_only=True)
class StorageMap:
    desc: str | None
    key_type: ABITypeAlias | AVMType | StructName
    value_type: ABITypeAlias | AVMType | StructName
    prefix: str | None  # base64-encoded prefix


@dataclass(kw_only=True)
class DefaultValue:
    data: str
    type: ABITypeAlias | AVMType | None = None
    source: DefaultValueSource


@dataclass(kw_only=True)
class MethodArg:
    type: ABITypeAlias
    struct: StructName | None = None
    name: str | None = None
    desc: str | None = None
    default_value: DefaultValue | None = None


@dataclass
class MethodReturns:
    type: ABITypeAlias
    struct: StructName | None = None
    desc: str | None = None


@dataclass(kw_only=True)
class MethodActions:
    create: list[Literal["NoOp", "OptIn", "DeleteApplication"]]
    call: list[Literal["NoOp", "OptIn", "CloseOut", "ClearState", "UpdateApplication", "DeleteApplication"]]


@dataclass(kw_only=True)
class BoxRecommendation:
    app: int | None = None
    key: str = ""
    read_bytes: int = 0
    write_bytes: int = 0


@dataclass(kw_only=True)
class Recommendations:
    inner_transaction_count: int | None = None
    boxes: list[BoxRecommendation] | None = None
    accounts: list[str] | None = None
    apps: list[int] | None = None
    assets: list[int] | None = None


@dataclass(kw_only=True)
class Method(_SerializableBaseClass):
    name: str
    desc: str | None = None
    args: list[MethodArg] = field(default_factory=list)
    returns: MethodReturns = field(default_factory=lambda: MethodReturns(type="void"))
    actions: MethodActions = field(default_factory=lambda: MethodActions(create=[], call=[]))
    readonly: bool | None = False
    events: list["Event"] | None = None
    recommendations: Recommendations | None = None


@dataclass(kw_only=True)
class EventArg:
    type: ABITypeAlias
    name: str | None = None
    desc: str | None = None
    struct: StructName | None = None


@dataclass(kw_only=True)
class Event:
    name: str
    desc: str | None = None
    args: list[EventArg] = field(default_factory=list)


@dataclass(kw_only=True)
class CompilerVersion:
    major: int
    minor: int
    patch: int
    commit_hash: str | None = None


@dataclass(kw_only=True)
class CompilerInfo:
    compiler: Literal["algod", "puya"]
    compiler_version: CompilerVersion


@dataclass
class SourceInfoDetail:
    pc: list[int]
    error_message: str | None = None
    teal: int | None = None
    source: str | None = None


@dataclass(kw_only=True)
class ProgramSourceInfo:
    source_info: list[SourceInfoDetail]
    pc_offset_method: Literal["none", "cblocks"]

    @staticmethod
    def from_json(source_info: str | dict) -> "ProgramSourceInfo":
        if "source_info" not in source_info:
            raise ValueError("source_info is required")
        source_dict: dict = json.loads(source_info) if isinstance(source_info, str) else source_info
        parsed_source_dict = [SourceInfoDetail(**detail) for detail in source_dict["source_info"]]
        return ProgramSourceInfo(source_info=parsed_source_dict, pc_offset_method=source_dict["pc_offset_method"])


@dataclass(kw_only=True)
class Arc56ContractState:
    keys: dict[str, dict[str, StorageKey]]
    maps: dict[str, dict[str, StorageMap]]
    schemas: dict[str, dict[str, int]]


@dataclass(kw_only=True)
class Arc56MethodArg:
    """Represents an ARC-56 method argument with ABI type conversion."""

    name: str | None = None
    desc: str | None = None
    struct: StructName | None = None
    default_value: DefaultValue | None = None
    type: ABIArgumentType

    @classmethod
    def from_method_arg(cls, arg: MethodArg, converted_type: ABIArgumentType) -> "Arc56MethodArg":
        """Create an Arc56MethodArg from a MethodArg with converted type."""
        return cls(
            name=arg.name,
            desc=arg.desc,
            struct=arg.struct,
            default_value=arg.default_value,
            type=converted_type,
        )


@dataclass(kw_only=True)
class Arc56MethodReturnType:
    """Represents an ARC-56 method return type with ABI type conversion."""

    type: algosdk.abi.ABIType | Literal["void"]  # Can be 'void' or ABIType
    struct: StructName | None = None
    desc: str | None = None


class Arc56Method(_SerializableBaseClass, algosdk.abi.Method):
    def __init__(self, method: Method) -> None:
        # First, create the parent class with original arguments
        super().__init__(
            name=method.name,
            args=method.args,  # type: ignore[arg-type]
            returns=algosdk.abi.Returns(arg_type=method.returns.type, desc=method.returns.desc),
            desc=method.desc,
        )
        self.method = method

        # Store our custom Arc56MethodArg list separately

        self._arc56_args = [
            Arc56MethodArg.from_method_arg(
                arg,
                algosdk.abi.ABIType.from_string(arg.type)
                if not self._is_transaction_or_reference_type(arg.type) and isinstance(arg.type, str)
                else arg.type,  # type: ignore[arg-type]
            )
            for arg in method.args
        ]

        # Convert returns similar to TypeScript implementation, including struct support
        converted_return_type: Literal["void"] | algosdk.abi.ABIType
        if method.returns.type == "void":
            converted_return_type = "void"
        else:
            converted_return_type = algosdk.abi.ABIType.from_string(str(method.returns.type))

        self._arc56_returns = Arc56MethodReturnType(
            type=converted_return_type,
            struct=method.returns.struct,
            desc=method.returns.desc,
        )

    def _is_transaction_or_reference_type(self, type_str: str) -> bool:
        return type_str in [
            algosdk.constants.ASSETCONFIG_TXN,
            algosdk.constants.PAYMENT_TXN,
            algosdk.constants.KEYREG_TXN,
            algosdk.constants.ASSETFREEZE_TXN,
            algosdk.constants.ASSETTRANSFER_TXN,
            algosdk.constants.APPCALL_TXN,
            algosdk.constants.STATEPROOF_TXN,
            algosdk.abi.ABIReferenceType.APPLICATION,
            algosdk.abi.ABIReferenceType.ASSET,
            algosdk.abi.ABIReferenceType.ACCOUNT,
        ]

    @property
    def arc56_args(self) -> list[Arc56MethodArg]:
        """Get the ARC-56 specific argument representations."""
        return self._arc56_args

    @property
    def arc56_returns(self) -> Arc56MethodReturnType:
        """Get the ARC-56 specific returns type, including struct information."""
        return self._arc56_returns


@dataclass(kw_only=True)
class Arc56Contract(_SerializableBaseClass):
    arcs: list[int]
    name: str
    desc: str | None = None
    networks: dict[str, dict[str, int]] | None = None
    structs: dict[StructName, list[StructField]] = field(default_factory=dict)
    methods: list[Method] = field(default_factory=list)
    state: Arc56ContractState
    bare_actions: dict[str, list[OnCompleteAction]] = field(default_factory=dict)
    source_info: dict[str, ProgramSourceInfo] | None = None
    source: dict[str, str] | None = None
    byte_code: dict[str, str] | None = None
    compiler_info: CompilerInfo | None = None
    events: list[Event] | None = None
    template_variables: dict[str, dict[str, ABITypeAlias | AVMType | StructName | str]] | None = None
    scratch_variables: dict[str, dict[str, int | ABITypeAlias | AVMType | StructName]] | None = None

    @staticmethod
    def from_json(application_spec: str | dict) -> "Arc56Contract":
        """Convert a JSON dictionary into an Arc56Contract instance.

        Args:
            json_data (dict): The JSON data representing an Arc56Contract

        Returns:
            Arc56Contract: The constructed Arc56Contract instance
        """
        # Convert networks if present
        json_data = json.loads(application_spec) if isinstance(application_spec, str) else application_spec
        json_data = _convert_keys_to_snake_case(json_data)
        networks = json_data.get("networks")

        # Convert structs
        structs = {
            name: [StructField(**field) if isinstance(field, dict) else field for field in struct_fields]
            for name, struct_fields in json_data.get("structs", {}).items()
        }

        # Convert methods
        methods = []
        for method_data in json_data.get("methods", []):
            # Convert method args
            args = [MethodArg(**arg) for arg in method_data.get("args", [])]

            # Convert method returns
            returns_data = method_data.get("returns", {"type": "void"})
            returns = MethodReturns(**returns_data)

            # Convert method actions
            actions_data = method_data.get("actions", {"create": [], "call": []})
            actions = MethodActions(**actions_data)

            # Convert events if present
            events = None
            if "events" in method_data:
                events = [Event(**event) for event in method_data["events"]]

            # Convert recommendations if present
            recommendations = None
            if "recommendations" in method_data:
                recommendations = Recommendations(**method_data["recommendations"])

            methods.append(
                Method(
                    name=method_data["name"],
                    desc=method_data.get("desc"),
                    args=args,
                    returns=returns,
                    actions=actions,
                    readonly=method_data.get("readonly", False),
                    events=events,
                    recommendations=recommendations,
                )
            )

        # Convert state
        state_data = json_data["state"]
        state = Arc56ContractState(
            keys={
                category: {name: StorageKey(**key_data) for name, key_data in keys.items()}
                for category, keys in state_data.get("keys", {}).items()
            },
            maps={
                category: {name: StorageMap(**map_data) for name, map_data in maps.items()}
                for category, maps in state_data.get("maps", {}).items()
            },
            schemas=state_data.get("schema", {}),
        )

        # Convert compiler info if present
        compiler_info = None
        if "compiler_info" in json_data:
            compiler_version = CompilerVersion(**json_data["compiler_info"]["compiler_version"])
            compiler_info = CompilerInfo(
                compiler=json_data["compiler_info"]["compiler"], compiler_version=compiler_version
            )

        # Convert events if present
        events = None
        if "events" in json_data:
            events = [Event(**event) for event in json_data["events"]]

        source_info = {}
        if "source_info" in json_data:
            source_info = {key: ProgramSourceInfo.from_json(val) for key, val in json_data["source_info"].items()}

        return Arc56Contract(
            arcs=json_data.get("arcs", []),
            name=json_data["name"],
            desc=json_data.get("desc"),
            networks=networks,
            structs=structs,
            methods=methods,
            state=state,
            bare_actions=json_data.get("bare_actions", {}),
            source_info=source_info,
            source=json_data.get("source"),
            byte_code=json_data.get("byte_code"),
            compiler_info=compiler_info,
            events=events,
            template_variables=json_data.get("template_variables"),
            scratch_variables=json_data.get("scratch_variables"),
        )
