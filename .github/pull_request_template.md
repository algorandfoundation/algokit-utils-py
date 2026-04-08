## Proposed Changes

This pull request introduces optional runtime validation schemas for API client responses using Pydantic models, and adds automation and documentation to support their use and maintenance. The main themes are: adding schema generation and usage, updating developer workflow and dependencies, and documenting the new feature.

### Validation schema generation and usage

- Added a script (`scripts/generate_schemas.py`) that generates Pydantic validation schemas from OpenAPI specs for algod, kmd, and indexer clients, producing 208 schema files in total. These schemas enable runtime type and bounds validation of API responses.
- Added and exported all generated schemas in `src/algokit_algod_client/schemas/__init__.py` for easy import and usage in client code.

### Developer workflow and automation

- Introduced a new `poe` task (`generate-schemas`) in `pyproject.toml` to automate schema generation, and updated the CI workflow to generate schemas and check for uncommitted changes to ensure schema files remain in sync with OpenAPI specs.
- Added `pydantic>=2.0.0,<3` as a development dependency, and excluded generated schemas from mypy type checking in `pyproject.toml`.
- Updated linting configuration to ignore specific rules for generated API client and schema files.

### Documentation

- Added a new documentation file (`api/oas-generator/VALIDATION.md`) detailing the purpose, usage, features, and maintenance of the validation schemas.
- Updated `README.md` with a section introducing validation schemas, installation requirements, usage examples, and links to further documentation.
