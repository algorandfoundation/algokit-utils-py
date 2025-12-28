import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, ClassVar

from oas_generator import models as ctx
from oas_generator.naming import IdentifierSanitizer


@dataclass(slots=True)
class SchemaEntry:
    name: str
    schema: ctx.RawSchema
    python_name: str
    module_name: str
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
    is_bytes_b64: bool = False  # True for x-algokit-bytes-base64 fields (always base64 encoded)
    list_inner_is_bytes: bool = False
    list_inner_is_bytes_b64: bool = False  # True for x-algokit-bytes-base64 list items
    is_signed_transaction: bool = False
    is_box_reference: bool = False
    is_locals_reference: bool = False
    is_holding_reference: bool = False
    needs_datetime: bool = False
    byte_length: int | None = None  # Fixed byte length from x-algokit-byte-length
    list_inner_byte_length: int | None = None  # Fixed byte length for list items
    imports: set[str] = field(default_factory=set)


LEDGER_STATE_DELTA_MODEL_NAMES: set[str] = {
    "LedgerStateDelta",
    "LedgerStateDeltaForTransactionGroup",
    "TransactionGroupLedgerStateDeltasForRound",
    "TransactionGroupLedgerStateDeltasForRoundResponseModel",
}


def _get_import_module(python_name: str, default_module: str) -> str:
    """Get the correct module name for importing a model.

    Models in LEDGER_STATE_DELTA_MODEL_NAMES are defined in the custom
    _ledger_state_delta template, not in individual module files.
    """
    if python_name in LEDGER_STATE_DELTA_MODEL_NAMES:
        return "_ledger_state_delta"
    return default_module


class SchemaRegistry:
    def __init__(self, spec: ctx.ParsedSpec, sanitizer: IdentifierSanitizer) -> None:
        self.spec = spec
        self.sanitizer = sanitizer
        self.entries: dict[str, SchemaEntry] = {}
        self.entries_by_python_name: dict[str, SchemaEntry] = {}
        self._name_collisions: set[str] = set()
        self._synthetic_index = 0
        self._register_components()

    def _register_components(self) -> None:
        for name in sorted(self.spec.schemas):
            schema = self.spec.schemas[name]
            self._register_entry(name, schema, synthetic=False)

    def _register_entry(
        self,
        name: str,
        schema: ctx.RawSchema,
        *,
        synthetic: bool,
        preferred_python_name: str | None = None,
    ) -> SchemaEntry:
        raw_name = preferred_python_name or schema.get("title") or name
        python_name = self._unique_python_name(raw_name)
        module_name = self.sanitizer.module(python_name)
        entry = SchemaEntry(
            name=name,
            schema=schema,
            python_name=python_name,
            module_name=module_name,
            description=schema.get("description"),
            kind=self._classify(schema),
            synthetic=synthetic,
        )
        self.entries[name] = entry
        self.entries_by_python_name[python_name] = entry
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
        synthetic_key = f"inline_{self._synthetic_index}_{hint}"
        return self._register_entry(
            synthetic_key,
            schema,
            synthetic=True,
            preferred_python_name=hint,
        )

    def _classify(self, schema: ctx.RawSchema) -> str:
        if schema.get("enum"):
            return "enum"
        if schema.get("x-algokit-signed-txn"):
            return "signed"
        if schema.get("x-algokit-box-reference"):
            return "box_reference"
        if schema.get("x-algokit-locals-reference"):
            return "locals_reference"
        if schema.get("x-algokit-holding-reference"):
            return "holding_reference"
        if schema.get("type") == "object" or schema.get("properties"):
            return "model"
        return "alias"


class TypeResolver:
    def __init__(self, registry: SchemaRegistry) -> None:
        self.registry = registry

    def _is_array_of_uint8(self, schema: ctx.RawSchema) -> bool:
        """Check if a schema represents an array of uint8 integers (should be bytes).

        This detects schemas like:
        {
            "type": "array",
            "items": {
                "type": "integer",
                "format": "uint8"
            }
        }
        """
        if not isinstance(schema, dict):
            return False

        # Check if this is a $ref to another schema
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            if ref_name in self.registry.entries:
                ref_schema = self.registry.entries[ref_name].schema
                return self._is_array_of_uint8(ref_schema)

        if schema.get("type") != "array":
            return False

        items = schema.get("items")
        if not isinstance(items, dict):
            return False

        # Check if items are integers with uint8 format
        return items.get("type") == "integer" and items.get("format") == "uint8"

    def resolve(self, schema: ctx.RawSchema, *, hint: str = "Inline") -> TypeInfo:  # noqa: C901, PLR0911, PLR0912
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
            return self._maybe_optional(info, nullable=nullable)
        if schema.get("x-algokit-signed-txn"):
            info = TypeInfo(annotation="SignedTransaction", model="SignedTransaction", is_signed_transaction=True)
            return self._maybe_optional(info, nullable=nullable)
        if schema.get("x-algokit-box-reference"):
            info = TypeInfo(annotation="BoxReference", model="BoxReference", is_box_reference=True)
            return self._maybe_optional(info, nullable=nullable)
        if schema.get("x-algokit-locals-reference"):
            info = TypeInfo(annotation="LocalsReference", model="LocalsReference", is_locals_reference=True)
            return self._maybe_optional(info, nullable=nullable)
        if schema.get("x-algokit-holding-reference"):
            info = TypeInfo(annotation="HoldingReference", model="HoldingReference", is_holding_reference=True)
            return self._maybe_optional(info, nullable=nullable)
        if schema_type == "array":
            info = self._resolve_array(schema, hint=hint)
            return self._maybe_optional(info, nullable=nullable)
        if schema_type == "object" and schema.get("properties"):
            entry = self.registry.register_inline(f"{hint}Model", schema)
            info = TypeInfo(annotation=entry.python_name, model=entry.python_name)
            return self._maybe_optional(info, nullable=nullable)
        if schema_type == "string":
            fmt = schema.get("format")
            is_bytes_b64 = bool(schema.get("x-algokit-bytes-base64"))
            if fmt in {"byte", "binary"} or is_bytes_b64:
                # Extract fixed byte length if present
                byte_length_val = schema.get("x-algokit-byte-length")
                byte_length = int(byte_length_val) if byte_length_val is not None else None
                info = TypeInfo(annotation="bytes", is_bytes=True, is_bytes_b64=is_bytes_b64, byte_length=byte_length)
            elif fmt == "date-time":
                info = TypeInfo(
                    annotation="datetime",
                    needs_datetime=True,
                    imports={"from datetime import datetime"},
                )
            else:
                info = TypeInfo(annotation="str")
            return self._maybe_optional(info, nullable=nullable)
        if schema_type == "integer":
            return self._maybe_optional(TypeInfo(annotation="int"), nullable=nullable)
        if schema_type == "number":
            return self._maybe_optional(TypeInfo(annotation="float"), nullable=nullable)
        if schema_type == "boolean":
            return self._maybe_optional(TypeInfo(annotation="bool"), nullable=nullable)
        if schema.get("enum"):
            entry = self.registry.register_inline(f"{hint}Enum", schema)
            info = TypeInfo(annotation=entry.python_name, enum=entry.python_name)
            return self._maybe_optional(info, nullable=nullable)
        if schema_type == "object":
            return self._maybe_optional(TypeInfo(annotation="dict[str, object]"), nullable=nullable)
        return self._maybe_optional(TypeInfo(annotation="object"), nullable=nullable)

    def _type_from_entry(self, entry: SchemaEntry, *, hint: str) -> TypeInfo:
        if entry.kind == "model":
            return TypeInfo(annotation=entry.python_name, model=entry.python_name)
        if entry.kind == "enum":
            return TypeInfo(annotation=entry.python_name, enum=entry.python_name)
        if entry.kind == "signed":
            return TypeInfo(annotation="SignedTransaction", model="SignedTransaction", is_signed_transaction=True)
        if entry.kind == "box_reference":
            return TypeInfo(annotation="BoxReference", model="BoxReference", is_box_reference=True)
        if entry.kind == "locals_reference":
            return TypeInfo(annotation="LocalsReference", model="LocalsReference", is_locals_reference=True)
        if entry.kind == "holding_reference":
            return TypeInfo(annotation="HoldingReference", model="HoldingReference", is_holding_reference=True)
        return self.resolve(entry.schema, hint=hint)

    def _resolve_array(self, schema: ctx.RawSchema, *, hint: str) -> TypeInfo:
        items = schema.get("items") or {"type": "object"}

        # Check if this is an array of uint8 integers (should be bytes)
        if self._is_array_of_uint8(schema):
            return TypeInfo(annotation="bytes", is_bytes=True)

        inner = self.resolve(items, hint=f"{hint}Item")
        annotation = f"list[{inner.annotation}]"
        return TypeInfo(
            annotation=annotation,
            is_list=True,
            list_inner_model=inner.model,
            list_inner_enum=inner.enum,
            list_inner_is_bytes=inner.is_bytes,
            list_inner_is_bytes_b64=inner.is_bytes_b64,
            list_inner_byte_length=inner.byte_length,
            is_signed_transaction=inner.is_signed_transaction,
            is_box_reference=inner.is_box_reference,
            is_locals_reference=inner.is_locals_reference,
            is_holding_reference=inner.is_holding_reference,
            needs_datetime=inner.needs_datetime,
            imports=set(inner.imports),
        )

    def _maybe_optional(self, info: TypeInfo, *, nullable: bool) -> TypeInfo:
        if nullable and "| None" not in info.annotation:
            info.annotation = f"{info.annotation} | None"
        return info


class ModelBuilder:
    def __init__(self, registry: SchemaRegistry, resolver: TypeResolver, sanitizer: IdentifierSanitizer) -> None:
        self.registry = registry
        self.resolver = resolver
        self.sanitizer = sanitizer
        self.uses_signed_transaction = False
        self.uses_box_reference = False
        self.uses_locals_reference = False
        self.uses_holding_reference = False

    def _compute_default_value(self, type_info: TypeInfo, prop_schema: ctx.RawSchema) -> str | None:
        """Compute default value for a required field based on its type.

        This mirrors the TypeScript codec approach where each codec has a defaultValue():
        - string → ""
        - int → 0
        - bool → False
        - bytes → b""
        - list → [] (uses default_factory)
        - address (x-algorand-format: Address) → ZERO_ADDRESS
        - nested models → None (will use default_factory)

        Returns:
            A string representation of the default value, or None if default_factory should be used.
        """
        # Check for address format (algorand addresses get ZERO_ADDRESS)
        algorand_format = prop_schema.get("x-algorand-format")
        if algorand_format == "Address":
            return "ZERO_ADDRESS"

        # Handle primitive types based on annotation
        annotation = type_info.annotation

        # Strip Optional wrapper if present (shouldn't be for required fields, but be safe)
        base_type = annotation.replace(" | None", "").strip()

        if base_type == "str":
            return '""'
        if base_type == "int":
            return "0"
        if base_type == "float":
            return "0.0"
        if base_type == "bool":
            return "False"
        if base_type == "bytes":
            return 'b""'

        # Lists need default_factory - return None to signal this
        if type_info.is_list or base_type.startswith("list["):
            return None  # Will use default_factory=list

        # Nested models - return None (they'll remain without default)
        if type_info.model:
            return None

        # Enums - return None (no sensible default)
        if type_info.enum:
            return None

        # datetime - return None
        if type_info.needs_datetime:
            return None

        # dict types - return None (will use default_factory)
        if base_type.startswith("dict[") or base_type == "dict[str, object]":
            return None

        # object type - no sensible default
        if base_type == "object":
            return None

        return None

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
            elif entry.kind in ("signed", "box_reference", "locals_reference", "holding_reference"):
                # These are imported from algokit_transact, not generated
                pass
            elif entry.kind == "alias":
                alias_type = self.resolver.resolve(entry.schema).annotation
                alias_imports = self._collect_alias_imports(alias_type, entry)
                aliases.append(
                    ctx.TypeAliasDescriptor(
                        name=entry.python_name,
                        module_name=entry.module_name,
                        target=alias_type,
                        imports=alias_imports,
                    )
                )
            for candidate in sorted(self.registry.entries.keys()):
                if candidate not in processed and candidate not in pending:
                    pending.append(candidate)
            pending.sort()
        return models, enums, aliases

    def _build_model(self, entry: SchemaEntry) -> ctx.ModelDescriptor:  # noqa: C901, PLR0912, PLR0915
        properties = entry.schema.get("properties", {}) or {}
        required = set(entry.schema.get("required", []) or [])
        fields: list[ctx.ModelField] = []
        imports: set[str] = set()
        uses_nested = False
        uses_flatten = False
        uses_enum_value = False
        needs_any = False

        for prop_name in sorted(properties):
            prop_schema = properties[prop_name] or {}
            wire_name = prop_name
            python_name_hint = prop_schema.get("x-algokit-field-rename") or prop_name
            type_info = self.resolver.resolve(prop_schema, hint=entry.python_name + self.sanitizer.pascal(prop_name))
            if type_info.is_signed_transaction:
                self.uses_signed_transaction = True
                imports.add("from algokit_transact.models.signed_transaction import SignedTransaction")
            if type_info.is_box_reference:
                self.uses_box_reference = True
                imports.add("from algokit_transact.models.app_call import BoxReference")
            if type_info.is_locals_reference:
                self.uses_locals_reference = True
                imports.add("from algokit_transact.models.app_call import LocalsReference")
            if type_info.is_holding_reference:
                self.uses_holding_reference = True
                imports.add("from algokit_transact.models.app_call import HoldingReference")
            annotation = type_info.annotation
            if prop_name not in required and "| None" not in annotation:
                annotation = f"{annotation} | None"
            annotation = self._apply_forward_reference_annotation(annotation, entry, type_info)

            # Compute default value and factory
            default_value: str | None = None
            default_factory: str | None = None

            # Check for schema-level default value
            schema_default = prop_schema.get("default")

            if prop_name in required:
                # Required fields get type-appropriate defaults to handle canonical msgpack encoding
                computed_default = self._compute_default_value(type_info, prop_schema)
                if computed_default is not None:
                    default_value = computed_default
                    # Add ZERO_ADDRESS import if needed
                    if computed_default == "ZERO_ADDRESS":
                        imports.add("from algokit_common.constants import ZERO_ADDRESS")
                elif type_info.is_list:
                    # Lists use default_factory=list
                    default_factory = "list"
            # Optional fields: use schema default if provided, otherwise None
            elif schema_default is not None:
                # Format the default value based on type
                if isinstance(schema_default, str):
                    default_value = f'"{schema_default}"'
                elif isinstance(schema_default, bool | (int | float)):
                    default_value = str(schema_default)
                else:
                    default_value = "None"
            else:
                default_value = "None"

            field = ctx.ModelField(
                name=self.sanitizer.snake(python_name_hint),
                wire_name=wire_name,
                type_hint=annotation,
                required=prop_name in required,
                description=prop_schema.get("description"),
                metadata=self._build_metadata(wire_name, type_info, required=prop_name in required),
                default_value=default_value,
                default_factory=default_factory,
            )
            imports.update(type_info.imports)
            if type_info.model and type_info.model != entry.python_name:
                dep_entry = self.registry.entries_by_python_name.get(type_info.model)
                if dep_entry:
                    dep_module = _get_import_module(dep_entry.python_name, dep_entry.module_name)
                    if dep_module != entry.module_name:
                        imports.add(f"from .{dep_module} import {dep_entry.python_name}")
            if type_info.list_inner_model:
                # Handle special external types first
                if type_info.list_inner_model == "SignedTransaction":
                    imports.add("from algokit_transact.models.signed_transaction import SignedTransaction")
                elif type_info.list_inner_model == "BoxReference" and type_info.is_box_reference:
                    imports.add("from algokit_transact.models.app_call import BoxReference")
                elif type_info.list_inner_model == "LocalsReference" and type_info.is_locals_reference:
                    imports.add("from algokit_transact.models.app_call import LocalsReference")
                elif type_info.list_inner_model == "HoldingReference" and type_info.is_holding_reference:
                    imports.add("from algokit_transact.models.app_call import HoldingReference")
                else:
                    # Only add local import if not a special external type
                    dep_entry = self.registry.entries_by_python_name.get(type_info.list_inner_model)
                    if dep_entry:
                        dep_module = _get_import_module(dep_entry.python_name, dep_entry.module_name)
                        if dep_module != entry.module_name:
                            imports.add(f"from .{dep_module} import {dep_entry.python_name}")
            if type_info.enum:
                dep_entry = self.registry.entries_by_python_name.get(type_info.enum)
                if dep_entry:
                    imports.add(f"from .{dep_entry.module_name} import {dep_entry.python_name}")
            if type_info.list_inner_enum:
                dep_entry = self.registry.entries_by_python_name.get(type_info.list_inner_enum)
                if dep_entry:
                    imports.add(f"from .{dep_entry.module_name} import {dep_entry.python_name}")
            if "encode_model_sequence" in field.metadata or "decode_model_sequence" in field.metadata:
                imports.add("from ._serde_helpers import decode_model_sequence, encode_model_sequence")
            if "encode_enum_sequence" in field.metadata or "decode_enum_sequence" in field.metadata:
                imports.add("from ._serde_helpers import decode_enum_sequence, encode_enum_sequence")
            if "encode_model_mapping" in field.metadata or "mapping_encoder" in field.metadata:
                imports.add("from ._serde_helpers import encode_model_mapping, mapping_encoder")
            if "decode_model_mapping" in field.metadata or "mapping_decoder" in field.metadata:
                imports.add("from ._serde_helpers import decode_model_mapping, mapping_decoder")
            if "encode_bytes" in field.metadata or "decode_bytes" in field.metadata:
                imports.add("from ._serde_helpers import decode_bytes, encode_bytes")
            if "decode_bytes_base64" in field.metadata:
                imports.add("from ._serde_helpers import decode_bytes_base64, encode_bytes")
            if "encode_bytes_sequence" in field.metadata or "decode_bytes_sequence" in field.metadata:
                imports.add("from ._serde_helpers import decode_bytes_sequence, encode_bytes_sequence")
            if "encode_fixed_bytes" in field.metadata or "decode_fixed_bytes" in field.metadata:
                imports.add("from ._serde_helpers import decode_fixed_bytes, encode_fixed_bytes")
            if "encode_fixed_bytes_sequence" in field.metadata or "decode_fixed_bytes_sequence" in field.metadata:
                imports.add("from ._serde_helpers import decode_fixed_bytes_sequence, encode_fixed_bytes_sequence")
            if "nested(" in field.metadata:
                uses_nested = True
            if "flatten(" in field.metadata:
                uses_flatten = True
            if "enum_value(" in field.metadata:
                uses_enum_value = True
            if "Any" in field.type_hint:
                needs_any = True
                imports.add("from typing import Any")
            fields.append(field)

        # Sort fields: required without defaults first, then required with defaults, then optional
        # This ensures dataclass field ordering rules are satisfied (non-default before default)
        def field_sort_key(f: ctx.ModelField) -> tuple[int, str]:
            has_default = f.default_value is not None or f.default_factory is not None
            if f.required and not has_default:
                return (0, f.name)  # Required without default: first
            elif f.required and has_default:
                return (1, f.name)  # Required with default: second
            else:
                return (2, f.name)  # Optional (always has default): third

        fields.sort(key=field_sort_key)
        return ctx.ModelDescriptor(
            name=entry.python_name,
            module_name=entry.module_name,
            description=entry.description,
            fields=fields,
            imports=sorted(imports),
            requires_datetime=any("datetime" in imp for imp in imports),
            uses_nested=uses_nested,
            uses_flatten=uses_flatten,
            uses_enum_value=uses_enum_value,
            needs_any=needs_any,
        )

    def _apply_forward_reference_annotation(self, annotation: str, entry: SchemaEntry, type_info: TypeInfo) -> str:
        forward_refs = self._forward_reference_tokens(entry, type_info)
        if not forward_refs:
            return annotation
        if self._requires_direct_forward_reference(entry, type_info):
            stripped = annotation.strip()
            if stripped.startswith(('"', "'")) and stripped.endswith(('"', "'")):
                return annotation
            return f'"{stripped}"'
        for token in sorted(forward_refs, key=len, reverse=True):
            if annotation == token:
                annotation = f'"{token}"'
                continue
            if re.fullmatch(rf"\s*{re.escape(token)}\s*\|\s*None\s*", annotation):
                annotation = f'"{annotation.strip()}"'
                continue
            if re.fullmatch(rf"\s*None\s*\|\s*{re.escape(token)}\s*", annotation):
                annotation = f'"{annotation.strip()}"'
                continue
            pattern = rf'(?<!["\'])\b{re.escape(token)}\b'
            annotation = re.sub(pattern, f'"{token}"', annotation)
        return annotation

    def _forward_reference_tokens(self, entry: SchemaEntry, type_info: TypeInfo) -> set[str]:
        tokens: set[str] = set()
        for ref_name in filter(None, [type_info.model, type_info.enum]):
            if self._is_same_module(entry, ref_name):
                tokens.add(ref_name)
        for ref_name in filter(None, [type_info.list_inner_model, type_info.list_inner_enum]):
            if self._is_same_module(entry, ref_name):
                tokens.add(ref_name)
        return tokens

    def _requires_direct_forward_reference(self, entry: SchemaEntry, type_info: TypeInfo) -> bool:
        if not type_info.model:
            return False
        if type_info.model in ("SignedTransaction", "BoxReference", "LocalsReference", "HoldingReference"):
            return False
        if type_info.model == entry.python_name:
            return True
        dep_entry = self.registry.entries_by_python_name.get(type_info.model)
        return bool(dep_entry and dep_entry.module_name == entry.module_name)

    def _is_same_module(self, entry: SchemaEntry, ref_name: str) -> bool:
        if ref_name == entry.python_name:
            return True
        dep_entry = self.registry.entries_by_python_name.get(ref_name)
        return bool(dep_entry and dep_entry.module_name == entry.module_name)

    def _build_enum(self, entry: SchemaEntry) -> ctx.EnumDescriptor:
        members: list[ctx.EnumValue] = []
        for value in entry.schema.get("enum", []) or []:
            member_name = self.sanitizer.const(str(value))
            members.append(ctx.EnumValue(member_name=member_name, value=value))
        return ctx.EnumDescriptor(
            name=entry.python_name,
            module_name=entry.module_name,
            values=members,
            description=entry.description,
        )

    def _build_metadata(self, wire_name: str, type_info: TypeInfo, *, required: bool = False) -> str:
        alias = wire_name.replace('"', '\\"')
        if type_info.model and not type_info.is_list:
            # Pass required flag for nested fields to enable default instance construction
            if required:
                return f'nested("{alias}", lambda: {type_info.model}, required=True)'
            return f'nested("{alias}", lambda: {type_info.model})'
        if type_info.enum and not type_info.is_list:
            return f'enum_value("{alias}", {type_info.enum})'
        if type_info.is_list and type_info.list_inner_model:
            return (
                "wire(\n"
                f'            "{alias}",\n'
                "            encode=encode_model_sequence,\n"
                f"            decode=lambda raw: decode_model_sequence(lambda: {type_info.list_inner_model}, raw),\n"
                "        )"
            )
        if type_info.is_list and type_info.list_inner_enum:
            return (
                "wire(\n"
                f'            "{alias}",\n'
                "            encode=encode_enum_sequence,\n"
                f"            decode=lambda raw: decode_enum_sequence(lambda: {type_info.list_inner_enum}, raw),\n"
                "        )"
            )
        if type_info.is_list and type_info.list_inner_is_bytes:
            # Handle fixed-length bytes in sequences
            if type_info.list_inner_byte_length is not None:
                return (
                    "wire(\n"
                    f'            "{alias}",\n'
                    f"            encode=lambda v: encode_fixed_bytes_sequence(v, {type_info.list_inner_byte_length}),\n"
                    f"            decode=lambda raw: decode_fixed_bytes_sequence(raw, {type_info.list_inner_byte_length}),\n"
                    "        )"
                )
            return (
                "wire(\n"
                f'            "{alias}",\n'
                "            encode=encode_bytes_sequence,\n"
                "            decode=decode_bytes_sequence,\n"
                "        )"
            )
        if type_info.is_bytes:
            # Use decode_bytes_base64 for fields marked with x-algokit-bytes-base64
            decode_fn = "decode_bytes_base64" if type_info.is_bytes_b64 else "decode_bytes"
            # Handle fixed-length bytes
            if type_info.byte_length is not None:
                return (
                    "wire(\n"
                    f'            "{alias}",\n'
                    f"            encode=lambda v: encode_fixed_bytes(v, {type_info.byte_length}),\n"
                    f"            decode=lambda raw: decode_fixed_bytes(raw, {type_info.byte_length}),\n"
                    "        )"
                )
            return (
                "wire(\n"
                f'            "{alias}",\n'
                "            encode=encode_bytes,\n"
                f"            decode={decode_fn},\n"
                "        )"
            )
        if type_info.is_signed_transaction:
            return f'nested("{alias}", lambda: SignedTransaction)'
        if type_info.is_box_reference:
            return f'nested("{alias}", lambda: BoxReference)'
        if type_info.is_locals_reference:
            return f'nested("{alias}", lambda: LocalsReference)'
        if type_info.is_holding_reference:
            return f'nested("{alias}", lambda: HoldingReference)'
        return f'wire("{alias}")'

    def _collect_alias_imports(self, annotation: str, entry: SchemaEntry) -> list[str]:
        imports: set[str] = set()
        tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", annotation))
        builtins = {
            "list",
            "dict",
            "set",
            "tuple",
            "frozenset",
            "Optional",
            "Union",
            "Literal",
            "int",
            "float",
            "str",
            "bool",
            "object",
        }
        for token in tokens:
            if token in builtins or token == entry.python_name:
                continue
            if token == "Any":
                imports.add("from typing import Any")
                continue
            if token == "SignedTransaction":
                imports.add("from algokit_transact.models.signed_transaction import SignedTransaction")
                continue
            if token == "BoxReference":
                imports.add("from algokit_transact.models.app_call import BoxReference")
                continue
            if token == "LocalsReference":
                imports.add("from algokit_transact.models.app_call import LocalsReference")
                continue
            if token == "HoldingReference":
                imports.add("from algokit_transact.models.app_call import HoldingReference")
                continue
            dep_entry = self.registry.entries_by_python_name.get(token)
            if dep_entry:
                imports.add(f"from .{dep_entry.module_name} import {dep_entry.python_name}")
        if "Any" in annotation:
            imports.add("from typing import Any")
        return sorted(imports)


class OperationBuilder:
    RAW_LEDGER_STATE_DELTA_OPERATIONS: ClassVar[set[str]] = {
        "LedgerStateDelta",
        "LedgerStateDeltaForTransactionGroup",
        "TransactionGroupLedgerStateDeltasForRound",
    }
    ALGOD_PRIVATE_OPERATIONS: ClassVar[set[str]] = {
        "RawTransaction",
        "ApplicationBoxByName",
        "TransactionParams",
    }
    SKIP_TAGS: ClassVar[set[str]] = {"private", "experimental", "skip"}

    def __init__(
        self,
        spec: ctx.ParsedSpec,
        resolver: TypeResolver,
        sanitizer: IdentifierSanitizer,
        registry: SchemaRegistry,
        client_key: str,
    ) -> None:
        self.spec = spec
        self.resolver = resolver
        self.sanitizer = sanitizer
        self.registry = registry
        self.client_key = client_key
        self.uses_signed_transaction = False
        self.uses_msgpack = False
        self.uses_block_models = False
        self.uses_ledger_state_delta = False
        self.uses_literal = False
        self.used_schema_refs: set[str] = set()

    def build(self) -> list[ctx.OperationGroup]:
        grouped: dict[str, list[ctx.OperationDescriptor]] = defaultdict(list)
        for path, path_item in sorted(self.spec.paths.items()):
            for method, operation in path_item.items():
                if method.lower() not in {"get", "post", "put", "delete", "patch"}:
                    continue
                op_id = operation.get("operationId", "")
                tags = operation.get("tags") or ["default"]
                # Check if operation should be skipped before building
                if self._should_skip_operation(op_id, tags):
                    continue
                # Collect schema refs from kept operations
                self._collect_schema_refs(operation, self.used_schema_refs)
                descriptor = self._build_operation(path, method.upper(), operation)
                grouped[descriptor.tag].append(descriptor)
        result: list[ctx.OperationGroup] = []
        for tag, operations in grouped.items():
            operations.sort(key=lambda op: op.name)
            result.append(ctx.OperationGroup(tag=tag, operations=operations))
        return sorted(result, key=lambda group: group.tag)

    def _build_operation(self, path: str, method: str, op: dict[str, Any]) -> ctx.OperationDescriptor:
        operation_id = op.get("operationId") or self._derive_operation_id(method, path)
        tags = op.get("tags") or ["default"]
        tag = tags[0]
        parameters, format_info = self._build_parameters(op.get("parameters", []))
        request_body = self._build_request_body(op.get("requestBody"), operation_id)
        response = self._build_response(op.get("responses", {}), operation_id)
        path_params = [p for p in parameters if p.location == "path"]
        query_params = [p for p in parameters if p.location == "query"]
        header_params = [p for p in parameters if p.location == "header"]
        format_options: list[str] | None = None
        format_default: str | None = None
        format_required = False
        format_single: str | None = None
        if format_info:
            fmt_enum = format_info.get("enum") or []
            format_required = format_info.get("required", False)
            format_default = format_info.get("default")
            if len(fmt_enum) == 1:
                format_single = fmt_enum[0]
                if format_default is None:
                    format_default = format_single
            elif fmt_enum:
                format_options = list(fmt_enum)
                if format_default is not None and format_default not in format_options:
                    format_default = None
                if len(format_options) > 1:
                    self.uses_literal = True
        else:
            format_single = None
        sanitized_name = self.sanitizer.snake(operation_id)
        is_private = self._is_private_operation(operation_id)
        if is_private and not sanitized_name.startswith("_"):
            sanitized_name = f"_{sanitized_name}"
        return ctx.OperationDescriptor(
            name=sanitized_name,
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
            format_options=format_options,
            format_default=format_default,
            format_required=format_required,
            format_single=format_single,
            is_private=is_private,
        )

    def _derive_operation_id(self, method: str, path: str) -> str:
        slug = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
        raw = f"{method}_{slug}" if slug else method
        return self.sanitizer.pascal(raw)

    def _is_private_operation(self, operation_id: str) -> bool:
        if self.client_key == ctx.ClientType.ALGOD_CLIENT:
            return operation_id in self.ALGOD_PRIVATE_OPERATIONS
        return False

    def _should_skip_operation(self, operation_id: str, tags: list[str]) -> bool:
        """Check if an operation should be skipped from generation.

        Operations are skipped if they have any tags that match SKIP_TAGS
        ('private', 'experimental', 'skip').
        """
        return any(tag in self.SKIP_TAGS for tag in tags)

    def _collect_schema_refs(self, obj: Any, refs: set[str]) -> None:
        """Recursively collect all schema $ref names from an object."""
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                if ref.startswith("#/components/schemas/"):
                    schema_name = ref.split("/")[-1]
                    if schema_name not in refs:
                        refs.add(schema_name)
                        # Also collect refs from the schema itself (for nested refs)
                        schema = self.spec.schemas.get(schema_name, {})
                        self._collect_schema_refs(schema, refs)
            for v in obj.values():
                self._collect_schema_refs(v, refs)
        elif isinstance(obj, list):
            for item in obj:
                self._collect_schema_refs(item, refs)

    def _build_parameters(
        self, params: list[dict[str, Any]]
    ) -> tuple[list[ctx.ParameterDescriptor], dict[str, Any] | None]:
        result: list[ctx.ParameterDescriptor] = []
        format_info: dict[str, Any] | None = None
        for raw_param in params:
            param = self._resolve_parameter_ref(raw_param)
            schema = param.get("schema") or {}
            name = param.get("name", "param")
            wire_name = name
            if name == "format" and param.get("in") == "query":
                enum_values = schema.get("enum") or []
                format_info = {
                    "enum": list(enum_values),
                    "default": schema.get("default"),
                    "required": param.get("required", False),
                }
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
        return result, format_info

    def _resolve_parameter_ref(self, param: dict[str, Any]) -> dict[str, Any]:
        if "$ref" not in param:
            return param
        ref_name = param["$ref"].split("/")[-1]
        parameters = self.spec.components.get("parameters", {}) or {}
        return parameters.get(ref_name, {})

    def _build_request_body(
        self, request_body: dict[str, Any] | None, operation_id: str
    ) -> ctx.RequestBodyDescriptor | None:
        if not request_body:
            return None
        if "$ref" in request_body:
            request_body = self._resolve_request_body_ref(request_body)
        content = request_body.get("content") or {}
        schema: ctx.RawSchema | None = None
        media_types: list[str] = []
        for media_type in sorted(content):
            candidate = content[media_type].get("schema")
            if candidate is not None and schema is None:
                schema = candidate
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
        if operation_id in self.RAW_LEDGER_STATE_DELTA_OPERATIONS:
            if not media_types:
                media_types = ["application/msgpack"]
            if "application/msgpack" in media_types:
                self.uses_msgpack = True
            self.uses_ledger_state_delta = True
            model_name = (
                "TransactionGroupLedgerStateDeltasForRound"
                if operation_id == "TransactionGroupLedgerStateDeltasForRound"
                else "LedgerStateDelta"
            )
            return ctx.ResponseDescriptor(
                type_hint=model_name,
                media_types=media_types,
                description=payload.get("description"),
                model=model_name,
            )
        if operation_id == "Block" and schema is not None:
            self.uses_block_models = True
            media_types = media_types or ["application/json"]
            return ctx.ResponseDescriptor(
                type_hint="models.BlockResponse",
                media_types=media_types,
                description=payload.get("description"),
                is_binary=False,
                model="BlockResponse",
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

    def _resolve_request_body_ref(self, body: dict[str, Any]) -> dict[str, Any]:
        ref_name = body["$ref"].split("/")[-1]
        request_bodies = self.spec.components.get("requestBodies", {}) or {}
        return request_bodies.get(ref_name, {})


def build_client_descriptor(
    spec: ctx.ParsedSpec, package_name: str, sanitizer: IdentifierSanitizer
) -> ctx.ClientDescriptor:
    package_leaf = package_name.split(".")[-1]
    client_key = ctx.ClientType(package_leaf.removeprefix("algokit_"))
    class_name = sanitizer.pascal(client_key)
    registry = SchemaRegistry(spec, sanitizer)
    resolver = TypeResolver(registry)
    operation_builder = OperationBuilder(spec, resolver, sanitizer, registry, client_key)
    groups = operation_builder.build()
    model_builder = ModelBuilder(registry, resolver, sanitizer)
    models, enums, aliases = model_builder.build()
    models = [model for model in models if model.name not in LEDGER_STATE_DELTA_MODEL_NAMES]

    # Filter out schemas only used by skipped operations
    used_schema_refs = operation_builder.used_schema_refs
    if used_schema_refs:
        # Build set of used python names from used schema refs
        used_python_names: set[str] = set()
        for schema_name in used_schema_refs:
            entry = registry.entries.get(schema_name)
            if entry:
                used_python_names.add(entry.python_name)

        # Filter models, enums, and aliases to only include used schemas
        # Keep synthetic schemas (inline) as they are generated from used operations
        models = [
            m
            for m in models
            if m.name in used_python_names
            or registry.entries_by_python_name.get(m.name, SchemaEntry("", {}, "", "", None, "", True)).synthetic
        ]
        enums = [
            e
            for e in enums
            if e.name in used_python_names
            or registry.entries_by_python_name.get(e.name, SchemaEntry("", {}, "", "", None, "", True)).synthetic
        ]
        aliases = [
            a
            for a in aliases
            if a.name in used_python_names
            or registry.entries_by_python_name.get(a.name, SchemaEntry("", {}, "", "", None, "", True)).synthetic
        ]

    uses_signed_txn = model_builder.uses_signed_transaction or operation_builder.uses_signed_transaction
    defaults = {
        ctx.ClientType.ALGOD_CLIENT: ("http://localhost:4001", "X-Algo-API-Token"),
        ctx.ClientType.INDEXER_CLIENT: ("http://localhost:8980", "X-Indexer-API-Token"),
        ctx.ClientType.KMD_CLIENT: ("http://localhost:7833", "X-KMD-API-Token"),
    }
    base_url, token_header = defaults.get(client_key, ("http://localhost", "X-Algo-API-Token"))
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
        uses_box_reference=model_builder.uses_box_reference,
        uses_locals_reference=model_builder.uses_locals_reference,
        uses_holding_reference=model_builder.uses_holding_reference,
        uses_msgpack=operation_builder.uses_msgpack,
        include_block_models=operation_builder.uses_block_models,
        include_ledger_state_delta=operation_builder.uses_ledger_state_delta,
        is_algod_client=client_key == ctx.ClientType.ALGOD_CLIENT,
    )
