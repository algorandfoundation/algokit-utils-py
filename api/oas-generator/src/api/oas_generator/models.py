from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


RawSchema = dict[str, Any]


@dataclass(slots=True)
class ParsedSpec:
    title: str
    version: str
    description: str | None
    paths: dict[str, Any]
    components: dict[str, Any]

    @property
    def schemas(self) -> dict[str, RawSchema]:
        return self.components.get("schemas", {}) or {}


@dataclass(slots=True)
class ModelField:
    name: str
    wire_name: str
    type_hint: str
    required: bool
    description: str | None
    metadata: str
    default_factory: str | None = None
    default_value: str | None = None


@dataclass(slots=True)
class ModelDescriptor:
    name: str
    description: str | None
    fields: list[ModelField]
    imports: list[str] = field(default_factory=list)
    requires_datetime: bool = False
    requires_enum: bool = False


@dataclass(slots=True)
class EnumValue:
    member_name: str
    value: str | int
    description: str | None = None


@dataclass(slots=True)
class EnumDescriptor:
    name: str
    values: list[EnumValue]
    description: str | None = None


@dataclass(slots=True)
class TypeAliasDescriptor:
    name: str
    target: str


@dataclass(slots=True)
class ParameterDescriptor:
    name: str
    wire_name: str
    location: str
    required: bool
    type_hint: str
    description: str | None
    default_value: str | None = None


@dataclass(slots=True)
class RequestBodyDescriptor:
    type_hint: str
    media_types: list[str]
    required: bool
    description: str | None
    is_binary: bool = False
    model: str | None = None
    list_model: str | None = None
    enum: str | None = None
    list_enum: str | None = None


@dataclass(slots=True)
class ResponseDescriptor:
    type_hint: str
    media_types: list[str]
    description: str | None
    is_binary: bool = False
    model: str | None = None
    list_model: str | None = None
    enum: str | None = None
    list_enum: str | None = None


@dataclass(slots=True)
class OperationDescriptor:
    name: str
    http_method: str
    path: str
    summary: str | None
    description: str | None
    tag: str
    parameters: list[ParameterDescriptor]
    path_parameters: list[ParameterDescriptor]
    query_parameters: list[ParameterDescriptor]
    header_parameters: list[ParameterDescriptor]
    request_body: RequestBodyDescriptor | None
    response: ResponseDescriptor | None
    operation_id: str
    prefer_msgpack_flag: bool = False
    force_msgpack_query: bool = False


@dataclass(slots=True)
class OperationGroup:
    tag: str
    operations: list[OperationDescriptor]


@dataclass(slots=True)
class ClientDescriptor:
    package_name: str
    class_name: str
    version: str
    description: str | None
    groups: list[OperationGroup]
    models: list[ModelDescriptor]
    enums: list[EnumDescriptor]
    aliases: list[TypeAliasDescriptor]
    default_base_url: str
    token_header: str
    uses_signed_transaction: bool = False
    uses_msgpack: bool = False
    include_block_models: bool = False
