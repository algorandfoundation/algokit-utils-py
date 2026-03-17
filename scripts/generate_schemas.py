#!/usr/bin/env python3
"""Generate Pydantic validation schemas from OpenAPI specs.

Produces one Python module per API client (algod.py, kmd.py, indexer.py)
containing all Pydantic BaseModel schemas derived from the OpenAPI spec.
Schemas are topologically sorted so forward references are unnecessary.
"""

import builtins
import json
import keyword
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

# Algorand uses uint64 for amounts, rounds, etc.
UINT64_MAX = 2**64 - 1  # 18446744073709551615

# Replicates the OAS generator's IdentifierSanitizer.snake() logic
# to ensure schema field names match the generated dataclass field names.
_NON_WORD = re.compile(r"[^0-9a-zA-Z]+")
_ACRONYM_BOUNDARY = re.compile(r"([A-Z]+)([A-Z][a-z])")
_LOWER_TO_UPPER = re.compile(r"([a-z0-9])([A-Z])")
_PY_RESERVED = {*keyword.kwlist, *keyword.softkwlist, *dir(builtins), "self", "cls"}

SPECS = {
    "algod": "https://raw.githubusercontent.com/algorandfoundation/algokit-oas-generator/main/specs/algod.oas3.json",
    "kmd": "https://raw.githubusercontent.com/algorandfoundation/algokit-oas-generator/main/specs/kmd.oas3.json",
    "indexer": "https://raw.githubusercontent.com/algorandfoundation/algokit-oas-generator/main/specs/indexer.oas3.json",
}

# Max docstring content: 120 (line) - 4 (indent) - 3 (open """) - 3 (...) - 3 (close """) = 107
_MAX_DOC = 107


def _to_snake(raw: str) -> str:
    """Convert an OAS field name to the same snake_case the OAS generator produces."""
    cleaned = _NON_WORD.sub(" ", raw)
    spaced = _ACRONYM_BOUNDARY.sub(r"\1 \2", cleaned)
    spaced = _LOWER_TO_UPPER.sub(r"\1 \2", spaced)
    parts = [part for part in spaced.strip().split() if part]
    candidate = "_".join(word.lower() for word in parts) if parts else "value"
    if candidate in _PY_RESERVED:
        candidate += "_"
    return candidate


def _sanitize_docstring(desc: str) -> str:
    """Escape invalid sequences and truncate long docstrings."""
    # Escape bare backslashes (e.g. \[apar\] from OAS descriptions)
    desc = desc.replace("\\", "\\\\")
    # Truncate to avoid E501
    if len(desc) > _MAX_DOC:
        desc = desc[:_MAX_DOC] + "..."
    return desc


def _class_name(oas_name: str) -> str:
    """Ensure OAS schema name starts with uppercase for PEP 8 class naming."""
    return oas_name[0].upper() + oas_name[1:] if oas_name else oas_name


def fetch_spec(url: str) -> dict[str, Any]:
    """Fetch OpenAPI spec from URL."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return cast(dict[str, Any], json.loads(response.read()))
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        raise SystemExit(f"Failed to fetch spec from {url}: {e}") from e


# ---------------------------------------------------------------------------
# Dependency analysis & topological sort
# ---------------------------------------------------------------------------


def _collect_refs(schema: dict[str, Any]) -> set[str]:
    """Collect all $ref schema names referenced by a schema."""
    refs: set[str] = set()
    if "$ref" in schema:
        refs.add(schema["$ref"].split("/")[-1])
    for key in ("properties", "items", "additionalProperties"):
        val = schema.get(key)
        if isinstance(val, dict):
            if key == "properties":
                for prop in val.values():
                    refs |= _collect_refs(prop)
            else:
                refs |= _collect_refs(val)
    return refs


def _topological_sort(schemas: dict[str, dict[str, Any]]) -> list[str]:
    """Sort schema names so dependencies come before dependents."""
    deps = {name: _collect_refs(s) & schemas.keys() for name, s in schemas.items()}
    sorted_names: list[str] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(name: str) -> None:
        if name in visited or name in visiting:
            return  # circular deps handled by `from __future__ import annotations`
        visiting.add(name)
        for dep in sorted(deps.get(name, set())):
            visit(dep)
        visiting.discard(name)
        visited.add(name)
        sorted_names.append(name)

    for name in sorted(schemas):
        visit(name)
    return sorted_names


# ---------------------------------------------------------------------------
# Type mapping
# ---------------------------------------------------------------------------


def map_type(details: dict[str, Any], *, required: bool) -> str:
    """Map OpenAPI type to Python type hint."""
    if "$ref" in details:
        ref = _class_name(details["$ref"].split("/")[-1]) + "Schema"
        return ref if required else f"{ref} | None"

    match details.get("type"):
        case "array":
            item = map_type(details.get("items", {}), required=True)
            base = f"list[{item}]"
            return base if required else f"{base} | None"
        case "object":
            if "additionalProperties" in details:
                val = map_type(details["additionalProperties"], required=True)
                base = f"dict[str, {val}]"
            else:
                base = "dict[str, Any]"
            return base if required else f"{base} | None"
        case "string":
            base = "str"
        case "integer":
            base = "int"
        case "number":
            base = "float"
        case "boolean":
            base = "bool"
        case _:
            base = "Any"

    return base if required else f"{base} | None"


# ---------------------------------------------------------------------------
# Schema class generation
# ---------------------------------------------------------------------------


def _is_byte_array(schema: dict[str, Any]) -> bool:
    """Check if schema is an array of uint8 (byte array)."""
    items = schema.get("items", {})
    return schema.get("type") == "array" and items.get("type") == "integer" and items.get("format") == "uint8"


def build_field(prop: str, details: dict[str, Any], *, required: bool) -> str:
    """Build a Pydantic field definition line."""
    rename = details.get("x-algokit-field-rename")
    field_name = _to_snake(rename) if rename else _to_snake(prop)

    if field_name in {"model_config", "model_fields", "model_computed_fields", "schema"}:
        field_name += "_"

    field_type = map_type(details, required=required)

    constraints = [] if required else ["default=None"]
    if details.get("format") == "uint64":
        constraints.extend(["ge=0", f"le={UINT64_MAX}"])
    if "minimum" in details:
        constraints.append(f"ge={details['minimum']}")
    if "maximum" in details:
        constraints.append(f"le={details['maximum']}")

    parts = [*constraints, f'alias="{prop}"']
    return f"    {field_name}: {field_type} = Field({', '.join(parts)})"


def _docstring(schema: dict[str, Any]) -> str:
    """Generate an indented docstring line, or empty string if no description."""
    raw = schema.get("description", "")
    if not raw:
        return ""
    return f'    """{_sanitize_docstring(raw)}"""\n\n'


def generate_class(name: str, schema: dict[str, Any]) -> str:
    """Generate a single schema class definition (no imports)."""
    cls = _class_name(name)
    desc = _docstring(schema)

    # String, byte array, or opaque schema → RootModel[str]
    is_string = schema.get("type") == "string"
    is_opaque = not schema.get("properties") and not schema.get("type")
    if is_string or _is_byte_array(schema) or is_opaque:
        body = desc if desc else "    pass\n"
        return f"class {cls}Schema(RootModel[str]):\n{body}"

    # Array schema → RootModel[list[...]]
    if schema.get("type") == "array":
        item = map_type(schema.get("items", {}), required=True)
        body = desc if desc else "    pass\n"
        return f"class {cls}Schema(RootModel[list[{item}]]):\n{body}"

    properties = schema.get("properties", {})

    # Empty object schema
    if not properties:
        return (
            f"class {cls}Schema(BaseModel):\n{desc}"
            '    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, extra="allow")\n'
        )

    # Regular object schema
    required_fields = schema.get("required", [])
    fields = [build_field(p, d, required=p in required_fields) for p, d in properties.items()]
    fields_str = "\n".join(fields)
    return (
        f"class {cls}Schema(BaseModel):\n{desc}"
        "    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)\n\n"
        f"{fields_str}\n"
    )


# ---------------------------------------------------------------------------
# Module assembly
# ---------------------------------------------------------------------------


def generate_module(schemas: dict[str, dict[str, Any]]) -> str:
    """Generate a complete Python module containing all schemas for one client."""
    sorted_names = _topological_sort(schemas)
    classes = [generate_class(name, schemas[name]) for name in sorted_names]
    needs_any = any("dict[str, Any]" in code for code in classes)

    # Build header
    lines = ['"""Generated Pydantic validation schemas from OpenAPI spec."""\n\n']
    lines.append("from __future__ import annotations\n\n")
    if needs_any:
        lines.append("from typing import Any\n\n")
    lines.append("from pydantic import BaseModel, ConfigDict, Field, RootModel\n")

    for code in classes:
        lines.append(f"\n\n{code}")

    return "".join(lines)


def write_module(client: str, content: str) -> None:
    """Write a single schema module file."""
    output_dir = Path("tests/fixtures/schemas")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{client}.py").write_text(content)


def main() -> None:
    """Generate schemas from OpenAPI specs."""
    total = 0
    for client, url in SPECS.items():
        print(f"\n{client.upper()}: ", end="", flush=True)
        spec = fetch_spec(url)
        schemas = spec["components"]["schemas"]
        content = generate_module(schemas)
        write_module(client, content)
        total += len(schemas)
        print(f"{len(schemas)} schemas")

    print(f"\nTotal: {total} schemas ✓")


if __name__ == "__main__":
    main()
