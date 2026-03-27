# Validation Schema Generator

## Overview

The validation schema generator creates Pydantic models from OpenAPI specifications for runtime validation of API client responses. This provides a sanity check layer on top of the generated API clients.

> **Note**: Validation schemas are **optional**. Pydantic is a dev dependency, not required for production use of algokit-utils.

## Usage

### Generating Schemas

```bash
# Using poe task
poe generate-schemas

# Or directly
python scripts/generate_schemas.py
```

This fetches OpenAPI specs from GitHub and generates Pydantic schemas in:
- `tests/fixtures/schemas/algod/` (84 schemas)
- `tests/fixtures/schemas/kmd/` (50 schemas)
- `tests/fixtures/schemas/indexer/` (74 schemas)

**Total: 208 validation schemas**

### Using Schemas

Use schemas for validation:
```python
from tests.fixtures.schemas.algod import AccountSchema, NodeStatusResponseSchema

# Validate API response
response_data = algod_client.status()
validated = NodeStatusResponseSchema.model_validate(response_data)

# Access validated data
print(f"Last round: {validated.last_round}")
```

## Features

- **Type Validation**: Ensures fields match expected types (str, int, bool, etc.)
- **Uint64 Bounds**: Validates uint64 fields are within 0 to 2^64-1
- **Nested Schemas**: Handles complex nested object structures
- **Array Types**: Supports both object and array-based schemas (RootModel)
- **Alias Support**: Maps hyphenated API field names to Python-friendly snake_case
- **Forward References**: Uses string annotations to handle cross-schema references

## Testing

Run validation tests:

```bash
# All tests
pytest tests/modules/test_schema_validation.py -v

# Exclude localnet tests
pytest tests/modules/test_schema_validation.py -v -m "not localnet"
```

Tests cover:
- Type validation (str, int, bool)
- Uint64 bounds checking
- Nested schema validation
- Schema imports

## Maintenance

Regenerate schemas when OpenAPI specs are updated:

```bash
poe generate-schemas
```

The generator is decoupled from the OAS generator - it fetches specs independently and can be run anytime.

## Files

- **Generator**: `scripts/generate_schemas.py` (~170 lines)
- **Tests**: `tests/modules/test_schema_validation.py`
- **Dependencies**: `pydantic>=2.0.0,<3` (added to pyproject.toml)
- **Generated**: 208 schema files across 3 client packages
