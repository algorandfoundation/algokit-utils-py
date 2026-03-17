#!/usr/bin/env python3
"""Generate Pydantic validation schemas from OpenAPI specs."""

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

# Algorand uses uint64 for amounts, rounds, etc.
UINT64_MAX = 2**64 - 1  # 18446744073709551615

SPECS = {
    "algod": "https://raw.githubusercontent.com/algorandfoundation/algokit-oas-generator/main/specs/algod.oas3.json",
    "kmd": "https://raw.githubusercontent.com/algorandfoundation/algokit-oas-generator/main/specs/kmd.oas3.json",
    "indexer": "https://raw.githubusercontent.com/algorandfoundation/algokit-oas-generator/main/specs/indexer.oas3.json",
}


def fetch_spec(url: str) -> dict[str, Any]:
    """Fetch OpenAPI spec from URL."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return cast(dict[str, Any], json.loads(response.read()))
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        raise SystemExit(f"Failed to fetch spec from {url}: {e}") from e


def map_type(details: dict[str, Any], *, required: bool) -> str:
    """Map OpenAPI type to Python type hint."""
    if "$ref" in details:
        ref = details["$ref"].split("/")[-1] + "Schema"
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


def build_field(prop: str, details: dict[str, Any], *, required: bool) -> str:
    """Build a Pydantic field definition."""
    field_name = prop.replace("-", "_")

    # Avoid shadowing BaseModel attributes
    if field_name in {"model_config", "model_fields", "model_computed_fields", "schema"}:
        field_name += "_"
    field_type = map_type(details, required=required)

    # String literal for schema refs, actual type for primitives (enables validation)
    type_str = f'"{field_type}"' if "Schema" in field_type else field_type

    constraints = [] if required else ["default=None"]
    if details.get("format") == "uint64":
        constraints.extend(["ge=0", f"le={UINT64_MAX}"])
    if "minimum" in details:
        constraints.append(f"ge={details['minimum']}")
    if "maximum" in details:
        constraints.append(f"le={details['maximum']}")

    # Build Field() call — alias is always present, constraints may be empty
    parts = [*constraints, f'alias="{prop}"']
    return f"    {field_name}: {type_str} = Field({', '.join(parts)})"


def generate_schema(name: str, schema: dict[str, Any]) -> str:
    """Generate a Pydantic schema class."""
    desc = f'    """{schema.get("description", "")}"""' if schema.get("description") else ""

    # Array schema
    if schema.get("type") == "array":
        item = map_type(schema.get("items", {}), required=True)
        item_str = f'"{item}"' if "Schema" in item else item
        typing_import = "from typing import Any\n" if "Any" in item_str else ""
        return f"""{typing_import}from pydantic import RootModel

class {name}Schema(RootModel[list[{item_str}]]):
{desc}
    pass
"""

    properties = schema.get("properties", {})

    # Empty object schema
    if not properties:
        return f"""from typing import Any
from pydantic import BaseModel, ConfigDict

class {name}Schema(BaseModel):
{desc}
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, extra="allow")
"""

    # Regular object schema
    required_fields = schema.get("required", [])
    fields = [build_field(prop, details, required=prop in required_fields) for prop, details in properties.items()]

    typing_import = "from typing import Any\n" if any("Any" in f for f in fields) else ""
    return f"""{typing_import}from pydantic import BaseModel, ConfigDict, Field

class {name}Schema(BaseModel):
{desc}
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

{chr(10).join(fields)}
"""


def write_schemas(client: str, schemas: dict[str, str]) -> None:
    """Write schemas to files."""
    output_dir = Path(f"tests/fixtures/schemas/{client}")
    output_dir.mkdir(parents=True, exist_ok=True)

    files = []
    for name, code in schemas.items():
        path = output_dir / f"{name.lower()}.py"
        path.write_text(code)
        files.append((name, path.stem))

    # Generate __init__.py with imports and model_rebuild
    init = '"""Generated Pydantic validation schemas."""\n\n'
    init += "".join(f"from .{mod} import {name}Schema\n" for name, mod in sorted(files))
    init += "\n# Rebuild models to resolve forward references\n"
    init += "".join(f"{name}Schema.model_rebuild()\n" for name, _ in sorted(files))
    init += "\n__all__ = [\n" + "".join(f'    "{name}Schema",\n' for name, _ in sorted(files)) + "]\n"

    (output_dir / "__init__.py").write_text(init)


def main() -> None:
    """Generate schemas from OpenAPI specs."""
    total = 0
    for client, url in SPECS.items():
        print(f"\n{client.upper()}: ", end="", flush=True)
        spec = fetch_spec(url)
        schemas = {name: generate_schema(name, s) for name, s in spec["components"]["schemas"].items()}
        write_schemas(client, schemas)
        total += len(schemas)
        print(f"{len(schemas)} schemas")

    print(f"\nTotal: {total} schemas ✓")


if __name__ == "__main__":
    main()
