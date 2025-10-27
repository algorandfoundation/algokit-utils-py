from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from api.oas_generator import models as ctx
from api.oas_generator.naming import IdentifierSanitizer


@dataclass(slots=True)
class SchemaEntry:
    name: str
    schema: ctx.RawSchema
    python_name: str
    description: str | None
    kind: str
    synthetic: bool = False


@dataclass(slots=True)
class TypeInfo:
    annotation: str
    model: str | None = None
    enum: str | None = None
    is_list: bool = False
    list_inner_model: str | None = None
    list_inner_enum: str | None = None
    is_bytes: bool = False
    is_signed_transaction: bool = False
    needs_datetime: bool = False
    imports: set[str] = field(default_factory=set)


class SchemaRegistry:
    def __init__(self, spec: ctx.ParsedSpec, sanitizer: IdentifierSanitizer) -> None:
        self.spec = spec
        self.sanitizer = sanitizer
        self.entries: dict[str, SchemaEntry] = {}
        self._name_collisions: set[str] = set()
        self._synthetic_index = 0
        self._register_components()

    def _register_components(self) -> None:
        for name in sorted(self.spec.schemas):
            schema = self.spec.schemas[name]
            self._register_entry(name, schema, synthetic=False)

    def _register_entry(self, name: str, schema: ctx.RawSchema, *, synthetic: bool) -> SchemaEntry:
        python_name = self._unique_python_name(schema.get("title") or name)
        entry = SchemaEntry(
            name=name,
            schema=schema,
            python_name=python_name,
            description=schema.get("description"),
            kind=self._classify(schema),
            synthetic=synthetic,
        )
        self.entries[name] = entry
        return entry

    def _unique_python_name(self, raw: str) -> str:
        candidate = self.sanitizer.pascal(raw)
        base = candidate
        index = 1
        while candidate in self._name_collisions:
            index += 1
            candidate = f"{base}{index}"
        self._name_collisions.add(candidate)
        return candidate

    def register_inline(self, hint: str, schema: ctx.RawSchema) -> SchemaEntry:
        self._synthetic_index += 1
        synthetic_name = f"__inline_{self._synthetic_index}__"
        return self._register_entry(f"{synthetic_name}_{hint}", schema, synthetic=True)

    def _classify(self, schema: ctx.RawSchema) -> str:
        if schema.get("enum"):
            return "enum"
        if schema.get("x-algokit-signed-txn"):
            return "signed"
        if schema.get("type") == "object" or schema.get("properties"):
            return "model"
        return "alias"


class TypeResolver:
    def __init__(self, registry: SchemaRegistry) -> None:
        self.registry = registry

    def resolve(self, schema: ctx.RawSchema, *, hint: str = "Inline") -> TypeInfo:
        schema = schema or {}
        schema_type = schema.get("type")
        nullable = bool(schema.get("nullable"))
        if isinstance(schema_type, list):
            if "null" in schema_type:
                nullable = True
                schema_type = [t for t in schema_type if t != "null"]
            schema_type = schema_type[0] if len(schema_type) == 1 else None
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            entry = self.registry.entries[ref_name]
            info = self._type_from_entry(entry, hint=entry.python_name)
            return self._maybe_optional(info, nullable)
        if schema.get("x-algokit-signed-txn"):
            info = TypeInfo(annotation="SignedTransaction", model="SignedTransaction", is_signed_transaction=True)
            return self._maybe_optional(info, nullable)
        if schema_type == "array":
            info = self._resolve_array(schema, hint=hint)
            return self._maybe_optional(info, nullable)
        if schema_type == "object" and schema.get("properties"):
            entry = self.registry.register_inline(f"{hint}Model", schema)
            info = TypeInfo(annotation=entry.python_name, model=entry.python_name)
            return self._maybe_optional(info, nullable)
        if schema_type == "string":
            fmt = schema.get("format")
            if fmt in {"byte", "binary"} or schema.get("x-algokit-bytes-base64"):
                info = TypeInfo(annotation="bytes", is_bytes=True)
            elif fmt == "date-time":
                info = TypeInfo(
                    annotation="datetime",
                    needs_datetime=True,
                    imports={"from datetime import datetime"},
                )
            else:
                info = TypeInfo(annotation="str")
            return self._maybe_optional(info, nullable)
        if schema_type == "integer":
            return self._maybe_optional(TypeInfo(annotation="int"), nullable)
        if schema_type == "number":
            return self._maybe_optional(TypeInfo(annotation="float"), nullable)
        if schema_type == "boolean":
            return self._maybe_optional(TypeInfo(annotation="bool"), nullable)
        if schema.get("enum"):
            entry = self.registry.register_inline(f"{hint}Enum", schema)
            info = TypeInfo(annotation=entry.python_name, enum=entry.python_name)
            return self._maybe_optional(info, nullable)
        if schema_type == "object":
            return self._maybe_optional(TypeInfo(annotation="dict[str, object]"), nullable)
        return self._maybe_optional(TypeInfo(annotation="object"), nullable)

    def _type_from_entry(self, entry: SchemaEntry, *, hint: str) -> TypeInfo:
        if entry.kind == "model":
            return TypeInfo(annotation=entry.python_name, model=entry.python_name)
        if entry.kind == "enum":
            return TypeInfo(annotation=entry.python_name, enum=entry.python_name)
        if entry.kind == "signed":
            return TypeInfo(annotation="SignedTransaction", model="SignedTransaction", is_signed_transaction=True)
        return self.resolve(entry.schema, hint=hint)

    def _resolve_array(self, schema: ctx.RawSchema, *, hint: str) -> TypeInfo:
        items = schema.get("items") or {"type": "object"}
        inner = self.resolve(items, hint=f"{hint}Item")
        annotation = f"list[{inner.annotation}]"
        type_info = TypeInfo(
            annotation=annotation,
            is_list=True,
            list_inner_model=inner.model,
            list_inner_enum=inner.enum,
            is_signed_transaction=inner.is_signed_transaction,
            needs_datetime=inner.needs_datetime,
            imports=set(inner.imports),
        )
        return type_info

    def _maybe_optional(self, info: TypeInfo, nullable: bool) -> TypeInfo:
        if nullable and "| None" not in info.annotation:
            info.annotation = f"{info.annotation} | None"
        return info


class ModelBuilder:
    def __init__(self, registry: SchemaRegistry, resolver: TypeResolver, sanitizer: IdentifierSanitizer) -> None:
        self.registry = registry
        self.resolver = resolver
        self.sanitizer = sanitizer
        self.uses_signed_transaction = False

    def build(self) -> tuple[list[ctx.ModelDescriptor], list[ctx.EnumDescriptor], list[ctx.TypeAliasDescriptor]]:
        models: list[ctx.ModelDescriptor] = []
        enums: list[ctx.EnumDescriptor] = []
        aliases: list[ctx.TypeAliasDescriptor] = []

        pending = sorted(self.registry.entries.keys())
        processed: set[str] = set()
        while pending:
            name = pending.pop(0)
            if name in processed:
                continue
            processed.add(name)
            entry = self.registry.entries[name]
            if entry.kind == "model":
                models.append(self._build_model(entry))
            elif entry.kind == "enum":
                enums.append(self._build_enum(entry))
            elif entry.kind == "alias":
                aliases.append(
                    ctx.TypeAliasDescriptor(name=entry.python_name, target=self.resolver.resolve(entry.schema).annotation)
                )
            for candidate in sorted(self.registry.entries.keys()):
                if candidate not in processed and candidate not in pending:
                    pending.append(candidate)
            pending.sort()
        return models, enums, aliases

    def _build_model(self, entry: SchemaEntry) -> ctx.ModelDescriptor:
        properties = entry.schema.get("properties", {}) or {}
        required = set(entry.schema.get("required", []) or [])
        fields: list[ctx.ModelField] = []
        imports: set[str] = set()

        for prop_name in sorted(properties):
            prop_schema = properties[prop_name] or {}
            wire_name = prop_schema.get("x-algokit-field-rename") or prop_name
            type_info = self.resolver.resolve(prop_schema, hint=entry.python_name + self.sanitizer.pascal(prop_name))
            if type_info.is_signed_transaction:
                self.uses_signed_transaction = True
            field = ctx.ModelField(
                name=self.sanitizer.snake(wire_name),
                wire_name=wire_name,
                type_hint=type_info.annotation,
                required=prop_name in required,
                description=prop_schema.get("description"),
                metadata=self._build_metadata(wire_name, type_info),
                default_value=None if prop_name in required else "None",
            )
            imports.update(type_info.imports)
            fields.append(field)

        fields.sort(key=lambda f: (not f.required, f.name))
        return ctx.ModelDescriptor(
            name=entry.python_name,
            description=entry.description,
            fields=fields,
            imports=sorted(imports),
            requires_datetime=any("datetime" in imp for imp in imports),
        )

    def _build_enum(self, entry: SchemaEntry) -> ctx.EnumDescriptor:
        members: list[ctx.EnumValue] = []
        for value in entry.schema.get("enum", []) or []:
            member_name = self.sanitizer.const(str(value))
            members.append(ctx.EnumValue(member_name=member_name, value=value))
        return ctx.EnumDescriptor(name=entry.python_name, values=members, description=entry.description)

    def _build_metadata(self, wire_name: str, type_info: TypeInfo) -> str:
        alias = wire_name.replace('"', '\\"')
        if type_info.model and not type_info.is_list:
            return f'nested("{alias}", lambda: {type_info.model})'
        if type_info.enum and not type_info.is_list:
            return f'enum_value("{alias}", {type_info.enum})'
        if type_info.is_list and type_info.list_inner_model:
            return (
                f'wire("{alias}", encode=encode_model_sequence, '
                f'decode=lambda raw: decode_model_sequence(lambda: {type_info.list_inner_model}, raw))'
            )
        if type_info.is_list and type_info.list_inner_enum:
            return (
                f'wire("{alias}", encode=encode_enum_sequence, '
                f'decode=lambda raw: decode_enum_sequence(lambda: {type_info.list_inner_enum}, raw))'
            )
        if type_info.is_signed_transaction:
            return f'nested("{alias}", lambda: SignedTransaction)'
        return f'wire("{alias}")'


class OperationBuilder:
    def __init__(self, spec: ctx.ParsedSpec, resolver: TypeResolver, sanitizer: IdentifierSanitizer,
                 registry: SchemaRegistry) -> None:
        self.spec = spec
        self.resolver = resolver
        self.sanitizer = sanitizer
        self.registry = registry
        self.uses_signed_transaction = False
        self.uses_msgpack = False
        self.uses_block_models = False

    def build(self) -> list[ctx.OperationGroup]:
        grouped: dict[str, list[ctx.OperationDescriptor]] = defaultdict(list)
        for path, path_item in sorted(self.spec.paths.items()):
            for method, operation in path_item.items():
                if method.lower() not in {"get", "post", "put", "delete", "patch"}:
                    continue
                descriptor = self._build_operation(path, method.upper(), operation)
                grouped[descriptor.tag].append(descriptor)
        result: list[ctx.OperationGroup] = []
        for tag, operations in grouped.items():
            operations.sort(key=lambda op: op.name)
            result.append(ctx.OperationGroup(tag=tag, operations=operations))
        return sorted(result, key=lambda group: group.tag)

    def _build_operation(self, path: str, method: str, op: dict[str, Any]) -> ctx.OperationDescriptor:
        operation_id = op.get("operationId") or self._derive_operation_id(method, path)
        tag = (op.get("tags") or ["default"])[0]
        parameters, force_msgpack = self._build_parameters(op.get("parameters", []))
        request_body = self._build_request_body(op.get("requestBody"), operation_id)
        response = self._build_response(op.get("responses", {}), operation_id)
        prefer_msgpack = False
        if response and "application/msgpack" in response.media_types and "application/json" in response.media_types:
            prefer_msgpack = True
        path_params = [p for p in parameters if p.location == "path"]
        query_params = [p for p in parameters if p.location == "query"]
        header_params = [p for p in parameters if p.location == "header"]
        return ctx.OperationDescriptor(
            name=self.sanitizer.snake(operation_id),
            http_method=method,
            path=path,
            summary=op.get("summary"),
            description=op.get("description"),
            tag=tag,
            parameters=parameters,
            path_parameters=path_params,
            query_parameters=query_params,
            header_parameters=header_params,
            request_body=request_body,
            response=response,
            operation_id=operation_id,
            prefer_msgpack_flag=prefer_msgpack,
            force_msgpack_query=force_msgpack,
        )

    def _derive_operation_id(self, method: str, path: str) -> str:
        slug = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
        raw = f"{method}_{slug}" if slug else method
        return self.sanitizer.pascal(raw)

    def _build_parameters(self, params: list[dict[str, Any]]) -> tuple[list[ctx.ParameterDescriptor], bool]:
        result: list[ctx.ParameterDescriptor] = []
        force_msgpack = False
        for param in params:
            param = self._resolve_parameter_ref(param)
            schema = param.get("schema") or {}
            name = param.get("name", "param")
            wire_name = name
            if (
                name == "format"
                and param.get("in") == "query"
                and schema.get("enum") == ["msgpack"]
            ):
                force_msgpack = True
                continue
            type_info = self.resolver.resolve(schema, hint=self.sanitizer.pascal(name))
            result.append(
                ctx.ParameterDescriptor(
                    name=self.sanitizer.snake(name),
                    wire_name=wire_name,
                    location=param.get("in", "query"),
                    required=param.get("required", False),
                    type_hint=type_info.annotation,
                    description=param.get("description"),
                    default_value="None" if not param.get("required", False) else None,
                )
            )
        return result, force_msgpack

    def _resolve_parameter_ref(self, param: dict[str, Any]) -> dict[str, Any]:
        if "$ref" not in param:
            return param
        ref_name = param["$ref"].split("/")[-1]
        parameters = self.spec.components.get("parameters", {}) or {}
        return parameters.get(ref_name, {})

    def _build_request_body(self, request_body: dict[str, Any] | None, operation_id: str) -> ctx.RequestBodyDescriptor | None:
        if not request_body:
            return None
        if "$ref" in request_body:
            request_body = self._resolve_request_body_ref(request_body)
        content = request_body.get("content") or {}
        schema = None
        media_types: list[str] = []
        for media_type in ("application/json", "application/msgpack", "application/octet-stream"):
            if media_type in content:
                schema = content[media_type].get("schema")
                media_types.append(media_type)
        if schema is None:
            return None
        type_info = self.resolver.resolve(schema, hint=f"{operation_id}Request")
        if type_info.is_signed_transaction:
            self.uses_signed_transaction = True
        if any(media == "application/msgpack" for media in media_types):
            self.uses_msgpack = True
        return ctx.RequestBodyDescriptor(
            type_hint=type_info.annotation,
            media_types=media_types,
            required=request_body.get("required", False),
            description=request_body.get("description"),
            is_binary=type_info.is_bytes,
            model=type_info.model,
            list_model=type_info.list_inner_model if type_info.is_list else None,
            enum=type_info.enum,
            list_enum=type_info.list_inner_enum if type_info.is_list else None,
        )

    def _build_response(self, responses: dict[str, Any], operation_id: str) -> ctx.ResponseDescriptor | None:
        if not responses:
            return None
        preferred_codes = [code for code in responses if code.startswith("2")]
        code = sorted(preferred_codes)[0] if preferred_codes else sorted(responses)[0]
        payload = responses[code]
        if isinstance(payload, dict) and "$ref" in payload:
            payload = self._resolve_response_ref(payload)
        content = payload.get("content") or {}
        schema = None
        media_types: list[str] = []
        for media_type in ("application/json", "application/msgpack", "application/octet-stream"):
            if media_type in content:
                schema = content[media_type].get("schema")
                media_types.append(media_type)
        if operation_id == "GetBlock" and schema is not None:
            self.uses_block_models = True
            media_types = media_types or ["application/json"]
            return ctx.ResponseDescriptor(
                type_hint="models.GetBlock",
                media_types=media_types,
                description=payload.get("description"),
                is_binary=False,
                model="GetBlock",
            )
        if schema is None:
            return None
        type_info = self.resolver.resolve(schema, hint=f"{operation_id}Response")
        if type_info.is_signed_transaction:
            self.uses_signed_transaction = True
        if any(media == "application/msgpack" for media in media_types):
            self.uses_msgpack = True
        return ctx.ResponseDescriptor(
            type_hint=type_info.annotation,
            media_types=media_types,
            description=payload.get("description"),
            is_binary=type_info.is_bytes,
            model=type_info.model,
            list_model=type_info.list_inner_model if type_info.is_list else None,
            enum=type_info.enum,
            list_enum=type_info.list_inner_enum if type_info.is_list else None,
        )

    def _resolve_response_ref(self, response: dict[str, Any]) -> dict[str, Any]:
        ref_name = response["$ref"].split("/")[-1]
        responses = self.spec.components.get("responses", {}) or {}
        return responses.get(ref_name, {})


def build_client_descriptor(spec: ctx.ParsedSpec, package_name: str, sanitizer: IdentifierSanitizer) -> ctx.ClientDescriptor:
    registry = SchemaRegistry(spec, sanitizer)
    resolver = TypeResolver(registry)
    model_builder = ModelBuilder(registry, resolver, sanitizer)
    models, enums, aliases = model_builder.build()
    operation_builder = OperationBuilder(spec, resolver, sanitizer, registry)
    groups = operation_builder.build()
    class_name = sanitizer.pascal(package_name)
    uses_signed_txn = model_builder.uses_signed_transaction or operation_builder.uses_signed_transaction
    defaults = {
        "algod_client": ("http://localhost:4001", "X-Algo-API-Token"),
        "indexer_client": ("http://localhost:8980", "X-Indexer-API-Token"),
        "kmd_client": ("http://localhost:7833", "X-KMD-API-Token"),
    }
    base_url, token_header = defaults.get(package_name, ("http://localhost", "X-Algo-API-Token"))
    return ctx.ClientDescriptor(
        package_name=package_name,
        class_name=class_name,
        version=spec.version,
        description=spec.description,
        groups=groups,
        models=models,
        enums=enums,
        aliases=aliases,
        default_base_url=base_url,
        token_header=token_header,
        uses_signed_transaction=uses_signed_txn,
        uses_msgpack=operation_builder.uses_msgpack,
        include_block_models=operation_builder.uses_block_models,
    )

    def _resolve_request_body_ref(self, body: dict[str, Any]) -> dict[str, Any]:
        ref_name = body["$ref"].split("/")[-1]
        request_bodies = self.spec.components.get("requestBodies", {}) or {}
        return request_bodies.get(ref_name, {})
