from typing import Literal, TypedDict

import algosdk

UPDATABLE_TEMPLATE_NAME = "TMPL_UPDATABLE"
"""The name of the TEAL template variable for deploy-time immutability control."""

DELETABLE_TEMPLATE_NAME = "TMPL_DELETABLE"
"""The name of the TEAL template variable for deploy-time permanence control."""


# ===== ARCs =====


# Type definitions
class StorageKey(TypedDict):
    key: str  # base64 encoded
    keyType: Literal["AVMString"]
    valueType: Literal["AVMUint64", "AVMBytes"]
    desc: str | None


class SchemaSpec(TypedDict):
    num_uints: int
    num_byte_slices: int


class Arc56State(TypedDict):
    schema: dict[Literal["global", "local"], dict[Literal["ints", "bytes"], int]]
    keys: dict[Literal["global", "local", "box"], dict[str, StorageKey]]
    maps: dict[Literal["global", "local", "box"], dict]


class Arc56MethodArg(TypedDict):
    name: str | None
    type: str | algosdk.abi.ABIType
    desc: str | None
    struct: str | None
    defaultValue: dict[str, str | int] | None


class Arc56MethodReturn(TypedDict):
    type: str | algosdk.abi.ABIType
    desc: str | None
    struct: str | None


class Arc56Method(TypedDict):
    name: str | None
    desc: str | None
    args: list[Arc56MethodArg]
    returns: Arc56MethodReturn
    events: list[str]  # Empty for now as per original
    readonly: bool | None
    actions: dict[Literal["create", "call"], list[str]]


class Arc56Contract(TypedDict):
    arcs: list[str]  # Empty as per original
    name: str
    desc: str | None
    structs: dict[str, list[dict[str, str]]]
    methods: list[Arc56Method]
    state: Arc56State
    source: dict[str, str]
    bareActions: dict[Literal["create", "call"], list[str]]
    # Following fields are undefined as per original
    byteCode: None
    compilerInfo: None
    events: None
    networks: None
    scratchVariables: None
    sourceInfo: None
    templateVariables: None
