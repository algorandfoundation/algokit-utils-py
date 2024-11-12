from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal

UPDATABLE_TEMPLATE_NAME = "TMPL_UPDATABLE"
"""The name of the TEAL template variable for deploy-time immutability control."""

DELETABLE_TEMPLATE_NAME = "TMPL_DELETABLE"
"""The name of the TEAL template variable for deploy-time permanence control."""


# ===== ARCs =====

# Define type aliases
ABITypeAlias = str
StructName = str
AVMBytes = Literal["AVMBytes"]
AVMString = Literal["AVMString"]
AVMUint64 = Literal["AVMUint64"]
AVMType = AVMBytes | AVMString | AVMUint64
OnCompleteAction = Literal["NoOp", "OptIn", "CloseOut", "ClearState", "UpdateApplication", "DeleteApplication"]
DefaultValueSource = Literal["box", "global", "local", "literal", "method"]


@dataclass
class CallConfig:
    no_op: str | None = None
    opt_in: str | None = None
    close_out: str | None = None
    clear_state: str | None = None
    update_application: str | None = None
    delete_application: str | None = None


class ARCType(IntEnum):
    ARC56 = 56
    ARC32 = 32


@dataclass(kw_only=True)
class StructField:
    name: str
    type_: ABITypeAlias | StructName | list["StructField"]


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
    type_: ABITypeAlias | AVMType | None = None
    source: DefaultValueSource


@dataclass(kw_only=True)
class MethodArg:
    type_: ABITypeAlias
    struct: StructName | None = None
    name: str | None = None
    desc: str | None = None
    default_value: DefaultValue | None = None


@dataclass
class MethodReturns:
    type_: ABITypeAlias
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
class Method:
    name: str
    desc: str | None = None
    args: list[MethodArg] = field(default_factory=list)
    returns: MethodReturns = field(default_factory=lambda: MethodReturns(type_="void"))
    actions: MethodActions = field(default_factory=lambda: MethodActions(create=[], call=[]))
    readonly: bool | None = False
    events: list["Event"] | None = None
    recommendations: Recommendations | None = None


@dataclass(kw_only=True)
class EventArg:
    type_: ABITypeAlias
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


@dataclass(kw_only=True)
class Arc56ContractState:
    keys: dict[str, dict[str, StorageKey]]
    maps: dict[str, dict[str, StorageMap]]
    schemas: dict[str, dict[str, int]]


@dataclass(kw_only=True)
class Arc56Contract:
    arcs: list[ARCType]
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
