import base64
import enum
import json
import typing
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from functools import cached_property

from Cryptodome.Hash import SHA512
from typing_extensions import deprecated

from algokit_abi import _arc56_serde as serde
from algokit_abi import abi
from algokit_common import from_wire, nested, to_wire, wire

if typing.TYPE_CHECKING:
    from algokit_abi import arc32

__all__ = [
    "ENUM_ALIASES",
    "AVMType",
    "Actions",
    "Arc56Contract",
    "Argument",
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
    "Network",
    "PcOffsetMethod",
    "ProgramSourceInfo",
    "Recommendations",
    "ReferenceType",
    "Returns",
    "Schema",
    "ScratchVariables",
    "Source",
    "SourceInfo",
    "SourceInfoModel",
    "State",
    "StorageKey",
    "StorageMap",
    "TemplateVariables",
    "TransactionType",
    "Void",
    "VoidType",
]


@typing.final
@enum.unique
class AVMType(str, enum.Enum):
    """Enum representing native AVM types"""

    BYTES = "AVMBytes"
    STRING = "AVMString"
    UINT64 = "AVMUint64"

    def __str__(self) -> str:
        return self.value


@typing.final
@enum.unique
class CallEnum(str, enum.Enum):
    """Enum representing different call types for application transactions."""

    CLEAR_STATE = "ClearState"
    CLOSE_OUT = "CloseOut"
    DELETE_APPLICATION = "DeleteApplication"
    NO_OP = "NoOp"
    OPT_IN = "OptIn"
    UPDATE_APPLICATION = "UpdateApplication"

    def __str__(self) -> str:
        return self.value


@typing.final
@enum.unique
class CreateEnum(str, enum.Enum):
    """Enum representing different create types for application transactions."""

    DELETE_APPLICATION = "DeleteApplication"
    NO_OP = "NoOp"
    OPT_IN = "OptIn"

    def __str__(self) -> str:
        return self.value


@typing.final
@enum.unique
class ReferenceType(str, enum.Enum):
    ASSET = "asset"
    ACCOUNT = "account"
    APPLICATION = "application"

    def __str__(self) -> str:
        return self.value


@typing.final
@enum.unique
class TransactionType(str, enum.Enum):
    ANY = "txn"
    """Any transaction"""
    PAY = "pay"
    """Payment transaction"""
    KEYREG = "keyreg"
    "Key registration transaction"
    ACFG = "acfg"
    """Asset configuration transaction"""
    AXFER = "axfer"
    """Asset transfer transaction"""
    AFRZ = "afrz"
    """Asset freeze transaction"""
    APPL = "appl"
    """App call transaction, allows creating, deleting, and interacting with an application"""

    def __str__(self) -> str:
        return self.value


VoidType = typing.Literal["void"]
Void: VoidType = "void"

ENUM_ALIASES: Mapping[str, ReferenceType | TransactionType | VoidType | AVMType] = {
    **{r.value: r for r in ReferenceType},
    **{t.value: t for t in TransactionType},
    **{a.value: a for a in AVMType},
    Void: Void,
}


class _StorageTypePropertyDescriptor:
    def __set_name__(self, owner: type, name: str) -> None:
        self._backing_field = f"_{name}"
        self._resolved_field = f"_{name}_resolved"

    def __get__(self, instance: object, owner: type) -> abi.ABIType | AVMType:
        try:
            value = getattr(instance, self._resolved_field)
        except AttributeError:
            raise AttributeError("resolved types not available until contract is initialized") from None
        return typing.cast(abi.ABIType | AVMType, value)

    def __set__(self, instance: object, value: abi.ABIType | AVMType) -> None:
        assert isinstance(value, abi.ABIType | AVMType), "expected ABIType or AVMType"
        setattr(instance, self._resolved_field, value)


@dataclass(frozen=True)
class DefaultValue:
    """Default value information for method arguments."""

    data: str
    """The default value data"""
    source: typing.Literal["box", "global", "local", "literal", "method"]
    """The source of the default value"""
    type: AVMType | abi.ABIType | None = field(default=None, metadata=serde.abi_type("type"))
    """The optional type of the default value"""


@dataclass
class Argument:
    """
    Represents an argument for an ABI method

    Args:
        type (ABIType | ReferenceType | TransactionType | str): ABI type, reference type or transaction type
        name (string, optional): name of this argument
        desc (string, optional): description of this argument
    """

    type: abi.ABIType | ReferenceType | TransactionType = field(metadata=serde.abi_type("type"))
    default_value: DefaultValue | None = field(default=None, metadata=nested("defaultValue", DefaultValue))
    desc: str | None = None
    name: str | None = None
    struct: str | None = None

    def __str__(self) -> str:
        if isinstance(self.type, abi.ABIType):
            return self.type.name
        else:
            return self.type


@dataclass
class Returns:
    """
    Represents a return type for an ABI method

    Args:
        type (ABIType | VoidType | str): ABI type of this return argument
        desc (string, optional): description of this return argument
    """

    type: abi.ABIType | VoidType = field(metadata=serde.abi_type("type"))
    desc: str | None = None
    struct: str | None = None

    def __str__(self) -> str:
        if isinstance(self.type, abi.ABIType):
            return self.type.name
        else:
            return self.type


@dataclass
class Actions:
    """Method actions information."""

    call: Sequence[CallEnum] = field(default=(), metadata=serde.sequence("call", CallEnum, omit_empty_seq=False))
    """The optional list of allowed call actions"""
    create: Sequence[CreateEnum] = field(
        default=(), metadata=serde.sequence("create", CreateEnum, omit_empty_seq=False)
    )
    """The optional list of allowed create actions"""


@dataclass
class EventArg:
    """Event argument information."""

    type: abi.ABIType = field(metadata=serde.abi_type("type"))
    """The type of the event argument"""
    name: str | None = None
    """The optional name of the argument"""
    desc: str | None = None
    """The optional description of the argument"""
    struct: str | None = None
    """The struct name, references a struct defined on the contract"""


@dataclass
class Event:
    """Event information."""

    args: Sequence[EventArg] = field(metadata=serde.nested_sequence("args", EventArg))
    """The list of event arguments"""
    name: str
    """The name of the event"""
    desc: str | None = None
    """The optional description of the event"""


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


@dataclass(frozen=True)
class Recommendations:
    """Method execution recommendations."""

    accounts: list[str] = field(default_factory=list, metadata=serde.sequence("accounts", str))
    """The optional list of accounts"""
    apps: list[int] = field(default_factory=list, metadata=serde.sequence("apps", int))
    """The optional list of applications"""
    assets: list[int] = field(default_factory=list, metadata=serde.sequence("assets", int))
    """The optional list of assets"""
    boxes: Boxes | None = None
    """The optional box storage requirements"""
    inner_transaction_count: int | None = field(default=None, metadata=wire("innerTransactionCount"))
    """The optional inner transaction count"""


@dataclass(kw_only=True)
class Method:
    """
    Represents an ABI method description.

    Args:
        name (string): name of the method
        args (tuple): tuplet of Argument objects with type, name, and optional description
        returns (Returns): a Returns object with a type and optional description
        desc (string, optional): optional description of the method
    """

    actions: Actions = field(default_factory=Actions)
    """The allowed actions"""
    args: Sequence[Argument] = field(metadata=serde.nested_sequence("args", Argument))
    """The method arguments"""
    name: str
    """The method name"""
    returns: Returns
    """The return information"""
    desc: str | None = None
    """The optional description"""
    events: Sequence[Event] = field(default=(), metadata=serde.nested_sequence("events", Event))
    """The events the method can raise"""
    readonly: bool | None = field(default=None, metadata=wire("readonly", keep_false=True))
    """The flag indicating if method is readonly, None if unknown"""
    recommendations: Recommendations | None = field(
        default=None, metadata=nested("recommendations", Recommendations, omit_empty_seq=False)
    )
    """The execution recommendations"""

    def get_txn_calls(self) -> int:
        return sum(1 for a in self.args if isinstance(a.type, TransactionType))

    @cached_property
    def signature(self) -> str:
        args_str = ",".join(map(str, self.args))
        return f"{self.name}({args_str}){self.returns}"

    @cached_property
    def selector(self) -> bytes:
        """
        Returns the ABI method signature, which is the first four bytes of the
        SHA-512/256 hash of the method signature.

        Returns:
            bytes: first four bytes of the method signature hash
        """
        sha_512_256 = SHA512.new(truncate="256")
        sha_512_256.update(self.signature.encode("utf-8"))
        return sha_512_256.digest()[:4]

    def __str__(self) -> str:
        return self.signature

    def get_selector(self) -> bytes:
        """Compatibility helper matching algosdk ABI Method API."""

        return self.selector

    def get_signature(self) -> str:
        """Compatibility helper matching algosdk ABI Method API."""

        return self.signature

    @staticmethod
    def from_signature(s: str) -> "Method":
        name, args_str, returns_str = _parse_method_string(s)

        args = []
        for arg_str in abi.split_tuple_str(args_str):
            try:
                alias = ENUM_ALIASES[arg_str]
            except KeyError:
                arg_type: abi.ABIType | ReferenceType | TransactionType = abi.ABIType.from_string(arg_str)
            else:
                if not isinstance(alias, ReferenceType | TransactionType):
                    raise ValueError(f"invalid arg: {args_str}")
                arg_type = alias
            args.append(Argument(arg_type))

        if returns_str == Void:
            returns = Returns(Void)
        else:
            returns = Returns(abi.ABIType.from_string(returns_str))
        return Method(name=name, args=tuple(args), returns=returns, actions=Actions(call=(), create=()))


def _parse_method_string(value: str) -> tuple[str, str, str]:
    # Parses a method signature into three tokens, (name,args,returns)
    # e.g. 'a(b,c)d' -> ('a', 'b,c', 'd')
    stack = []
    for i, char in enumerate(value):
        if char == "(":
            stack.append(i)
        elif char == ")":
            if not stack:
                break
            left_index = stack.pop()
            if not stack:
                return value[:left_index], value[left_index + 1 : i], value[i + 1 :]

    raise ValueError(f"ABI method string has mismatched parentheses: {value}")


class Compiler(str, enum.Enum):
    """Enum representing different compiler types."""

    ALGOD = "algod"
    PUYA = "puya"


@dataclass
class ByteCode:
    """Represents the approval and clear program bytecode."""

    approval: bytes = field(metadata=serde.base64_encoded_bytes("approval"))
    """The approval program bytecode"""
    clear: bytes = field(metadata=serde.base64_encoded_bytes("clear"))
    """The clear program bytecode"""


@dataclass
class CompilerVersion:
    """Represents compiler version information."""

    commit_hash: str | None = field(default=None, metadata=wire("commitHash"))
    """The git commit hash of the compiler"""
    major: int | None = None
    """The major version number"""
    minor: int | None = None
    """The minor version number"""
    patch: int | None = None
    """The patch version number"""


@dataclass
class CompilerInfo:
    """Information about the compiler used."""

    # TODO: make this just a str?
    compiler: Compiler = field(metadata=wire("compiler", encode=Compiler))
    """The type of compiler used"""
    compiler_version: CompilerVersion = field(metadata=nested("compilerVersion", CompilerVersion))
    """Version information for the compiler"""


@dataclass
class Network:
    """Network-specific application information."""

    app_id: int = field(metadata=wire("appId"))
    """The application ID on the network"""


@dataclass
class ScratchVariables:
    """Information about scratch space variables."""

    slot: int
    """The scratch slot number"""
    _type: abi.ABIType | AVMType | str = field(metadata=serde.storage("type"))
    type = _StorageTypePropertyDescriptor()
    """The type of the scratch variable"""


@dataclass
class Source:
    """Source code for approval and clear programs."""

    approval: str
    """The base64 encoded approval program source"""
    clear: str
    """The base64 encoded clear program source"""

    # TODO: just make this the source properties?
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

    bytes: int = field(default=0, metadata=wire("bytes", keep_zero=True))
    """The number of byte slices in global state"""
    ints: int = field(default=0, metadata=wire("ints", keep_zero=True))
    """The number of integers in global state"""


@dataclass
class Local:
    """Local state schema."""

    bytes: int = field(default=0, metadata=wire("bytes", keep_zero=True))
    """The number of byte slices in local state"""
    ints: int = field(default=0, metadata=wire("ints", keep_zero=True))
    """The number of integers in local state"""


@dataclass
class Schema:
    """Application state schema."""

    global_state: Global = field(default_factory=Global, metadata=nested("global", Global))
    """The global state schema"""
    local_state: Local = field(default_factory=Local, metadata=nested("local", Local))
    """The local state schema"""


@dataclass
class TemplateVariables:
    """Template variable information."""

    _type: abi.ABIType | AVMType | str = field(metadata=serde.storage("type"))
    type = _StorageTypePropertyDescriptor()
    """The type of the template variable"""
    value: str | None = None
    """The optional value of the template variable"""


class PcOffsetMethod(str, enum.Enum):
    """PC offset method types."""

    CBLOCKS = "cblocks"
    NONE = "none"


@dataclass
class SourceInfo:
    """Source code location information."""

    pc: list[int] = field(metadata=serde.sequence("pc", int))
    """The list of program counter values"""
    error_message: str | None = field(default=None, metadata=wire("errorMessage"))
    """The optional error message"""
    source: str | None = None
    """The optional source code"""
    teal: int | None = None
    """The optional TEAL version"""


@dataclass
class StorageKey:
    """Storage key information."""

    key: str
    """The storage key"""
    _key_type: abi.ABIType | AVMType | str = field(metadata=serde.storage("keyType"))
    """The type of the key"""
    _value_type: abi.ABIType | AVMType | str = field(metadata=serde.storage("valueType"))
    """The type of the value"""
    desc: str | None = None
    """The optional description"""

    key_type = _StorageTypePropertyDescriptor()
    value_type = _StorageTypePropertyDescriptor()


@dataclass
class StorageMap:
    """Storage map information."""

    _key_type: abi.ABIType | AVMType | str = field(metadata=serde.storage("keyType"))
    """The type of the map keys"""
    _value_type: abi.ABIType | AVMType | str = field(metadata=serde.storage("valueType"))
    """The type of the map values"""
    desc: str | None = None
    """The optional description"""
    prefix: str | None = None
    """The optional key prefix"""
    key_type = _StorageTypePropertyDescriptor()
    value_type = _StorageTypePropertyDescriptor()


@dataclass
class Keys:
    """Storage keys for different storage types."""

    box: dict[str, StorageKey] = field(default_factory=dict, metadata=serde.mapping("box", StorageKey))
    """The box storage keys"""
    global_state: dict[str, StorageKey] = field(default_factory=dict, metadata=serde.mapping("global", StorageKey))
    """The global state storage keys"""
    local_state: dict[str, StorageKey] = field(default_factory=dict, metadata=serde.mapping("local", StorageKey))
    """The local state storage keys"""


@dataclass
class Maps:
    """Storage maps for different storage types."""

    box: dict[str, StorageMap] = field(default_factory=dict, metadata=serde.mapping("box", StorageMap))
    """The box storage maps"""
    global_state: dict[str, StorageMap] = field(default_factory=dict, metadata=serde.mapping("global", StorageMap))
    """The global state storage maps"""
    local_state: dict[str, StorageMap] = field(default_factory=dict, metadata=serde.mapping("local", StorageMap))
    """The local state storage maps"""


@dataclass
class State:
    """Application state information."""

    keys: Keys = field(default_factory=Keys)
    """The storage keys"""
    maps: Maps = field(default_factory=Maps)
    """The storage maps"""
    schema: Schema = field(default_factory=Schema)
    """The state schema"""


@dataclass
class ProgramSourceInfo:
    """Program source information."""

    pc_offset_method: PcOffsetMethod = field(metadata=wire("pcOffsetMethod"))
    """The PC offset method"""
    source_info: list[SourceInfo] = field(metadata=serde.nested_sequence("sourceInfo", SourceInfo))
    """The list of source info entries"""


@dataclass
class SourceInfoModel:
    """Source information for approval and clear programs."""

    approval: ProgramSourceInfo
    """The approval program source info"""
    clear: ProgramSourceInfo
    """The clear program source info"""


_HasStructField = Argument | Returns | EventArg


@dataclass(kw_only=True)
class Arc56Contract:
    """ARC-0056 application specification.

    See https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0056.md
    """

    arcs: list[int] = field(default_factory=list, metadata=serde.sequence("arcs", int, omit_empty_seq=False))
    """The list of supported ARC version numbers"""
    bare_actions: Actions = field(default_factory=Actions, metadata=nested("bareActions", Actions))
    """The bare call and create actions"""
    methods: list[Method] = field(metadata=serde.nested_sequence("methods", Method))
    """The list of contract methods"""
    name: str
    """The contract name"""
    state: State = field(default_factory=State)
    """The contract state information"""
    structs: dict[str, abi.StructType] = field(default_factory=dict, metadata=serde.struct_metadata)
    """The contract struct definitions"""
    byte_code: ByteCode | None = field(default=None, metadata=nested("byteCode", ByteCode))
    """The optional bytecode for approval and clear programs"""
    compiler_info: CompilerInfo | None = field(default=None, metadata=nested("compilerInfo", CompilerInfo))
    """The optional compiler information"""
    desc: str | None = None
    """The optional contract description"""
    events: list[Event] | None = field(default=None, metadata=serde.nested_sequence("events", Event))
    """The optional list of contract events"""
    networks: dict[str, Network] | None = field(default=None, metadata=serde.mapping("networks", Network))
    """The optional network deployment information"""
    scratch_variables: dict[str, ScratchVariables] | None = field(
        default=None, metadata=serde.mapping("scratchVariables", ScratchVariables)
    )
    """The optional scratch variable information"""
    source: Source | None = None
    """The optional source code"""
    source_info: SourceInfoModel | None = field(default=None, metadata=nested("sourceInfo", SourceInfoModel))
    """The optional source code information"""
    template_variables: dict[str, TemplateVariables] | None = field(
        default=None, metadata=serde.mapping("templateVariables", TemplateVariables)
    )
    """The optional template variable information"""

    def __post_init__(self) -> None:
        self._update_contract_structs()

    def apply_decode_types(self, resolve_struct_type: Callable[[abi.StructType], type]) -> "Arc56Contract":
        """
        Returns a new contract specification where each StructType's decode_type
        is updated with the result of resolve_struct_type, useful for supplying custom types used in
        struct decoding

        :param resolve_struct_type: Callback that can be used to supply custom types for any Struct types
        :return: Arc56Contract instance
        """
        return replace(
            self,
            structs={
                struct_name: _apply_struct_types(struct_type, resolve_struct_type)
                for struct_name, struct_type in self.structs.items()
            },
        )

    @classmethod
    def from_dict(
        cls, application_spec: dict, resolve_struct_type: Callable[[abi.StructType], type] | None = None
    ) -> "Arc56Contract":
        """Create Arc56Contract from dictionary.

        :param application_spec: Dictionary containing contract specification
        :param resolve_struct_type: Optional callback that can be used to supply custom types for any Struct types
        :return: Arc56Contract instance
        """
        contract = from_wire(cls, application_spec)
        if resolve_struct_type is not None:
            contract = contract.apply_decode_types(resolve_struct_type)
        return contract

    @staticmethod
    def from_json(
        application_spec: str, resolve_struct_type: Callable[[abi.StructType], type] | None = None
    ) -> "Arc56Contract":
        """
        Creates an instance from an ARC-56 application spec

        :param application_spec: Dictionary containing contract specification
        :param resolve_struct_type: Optional callback that can be used to supply custom types for any Struct types
        :return: Arc56Contract instance
        """
        return Arc56Contract.from_dict(json.loads(application_spec), resolve_struct_type)

    @staticmethod
    @deprecated("Arc32 contracts are being deprecated; prefer converting to Arc56 instead.")
    def from_arc32(arc32_application_spec: typing.Union[str, "arc32.Arc32Contract"]) -> "Arc56Contract":
        from algokit_abi import arc32_to_arc56

        return arc32_to_arc56(arc32_application_spec)

    def to_json(self, indent: int | None = None) -> str:
        return json.dumps(self.dictify(), indent=indent)

    def dictify(self) -> dict:
        return to_wire(self)

    def get_abi_method(self, method_name_or_signature: str) -> Method:
        if "(" in method_name_or_signature:
            methods = [m for m in self.methods if m.signature == method_name_or_signature]
        else:
            methods = [m for m in self.methods if m.name == method_name_or_signature]

        if not methods:
            raise ValueError(f"Unable to find method {method_name_or_signature} in {self.name} contract.")
        try:
            (method,) = methods
        except ValueError:
            signatures = [m.signature for m in methods]
            raise ValueError(
                f"Received a call to method {method_name_or_signature} in contract {self.name}, "
                f"but this resolved to multiple methods; please pass in an ABI signature instead: "
                f"{', '.join(signatures)}"
            ) from None
        return method

    def _update_contract_structs(self) -> None:
        for method in self.methods:
            for arg in method.args:
                self._maybe_update_struct(arg)
            self._maybe_update_struct(method.returns)
            for event in method.events or []:
                for event_arg in event.args:
                    self._maybe_update_struct(event_arg)
        for event in self.events or []:
            for event_arg in event.args:
                self._maybe_update_struct(event_arg)
        self._replace_state_structs()
        for template in (self.template_variables or {}).values():
            self._maybe_update_abi_struct_type(template, "type")
        for scratch in (self.scratch_variables or {}).values():
            self._maybe_update_abi_struct_type(scratch, "type")

    def _replace_state_structs(self) -> None:
        keys = self.state.keys
        maps = self.state.maps
        for storage_maps in (
            keys.box,
            keys.global_state,
            keys.local_state,
            maps.box,
            maps.global_state,
            maps.local_state,
        ):
            for storage in storage_maps.values():
                self._maybe_update_abi_struct_type(storage, "key_type", "value_type")

    def _maybe_update_struct(self, has_struct: _HasStructField) -> None:
        if has_struct.struct is not None:
            has_struct.type = self.structs[has_struct.struct]

    def _maybe_update_abi_struct_type(self, storage: object, *names: str) -> None:
        for name in names:
            backing_type = getattr(storage, f"_{name}")
            if type(backing_type) is str:  # only match str exactly, so enums are not used
                resolved_type = self.structs[backing_type]
            else:
                resolved_type = backing_type
            setattr(storage, name, resolved_type)


_TABIType = typing.TypeVar("_TABIType", bound=abi.ABIType)


def _apply_struct_types(abi_type: _TABIType, resolve_type: Callable[[abi.StructType], type]) -> _TABIType:
    if isinstance(abi_type, abi.StructType):
        return replace(
            abi_type,
            decode_type=resolve_type(abi_type),
            fields={
                field_name: _apply_struct_types(field_type, resolve_type)
                for field_name, field_type in abi_type.fields.items()
            },
        )
    elif isinstance(abi_type, abi.StaticArrayType | abi.DynamicArrayType):
        return replace(abi_type, element=_apply_struct_types(abi_type.element, resolve_type))
    elif isinstance(abi_type, abi.TupleType):
        return replace(abi_type, elements=tuple(_apply_struct_types(e, resolve_type) for e in abi_type.elements))
    return abi_type
