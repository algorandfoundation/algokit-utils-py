# OAS Generator

Local-only CLI that renders Algorand API clients from OpenAPI specs.

## Layout

```md
api/oas-generator/
├── pyproject.toml # project config + console script
├── README.md # this file
└── src/oas_generator/ # generator package and templates
```

### Key modules

- `cli.py` – argument parser and CLI entrypoint
- `parser.py` / `loader.py` – read & validate OpenAPI specs (supports local paths, URLs, and shorthand)
- `builder.py` / `models.py` – shape spec data for rendering
- `renderer/engine.py` / `filters.py` – Jinja environment and helpers
- `writer.py` – emit generated files into the target package

### Template highlights

- `templates/client.py.j2` – HTTP client implementation
- `templates/config.py.j2` – client configuration dataclass
- `templates/exceptions.py.j2` – error definitions surfaced by clients
- `templates/package_init.py.j2` – package-level exports
- `templates/types.py.j2` – shared type helpers
- `templates/models/*.j2` – request/response models and serde helpers

## Usage

The `--spec` argument accepts:
- **Local paths**: `api/specs/algod.oas3.json`
- **Remote URLs**: `https://raw.githubusercontent.com/.../algod.oas3.json`
- **Shorthand**: `oas://algod` (fetches from `algokit-oas-generator` main branch)
- **Shorthand with branch/tag**: `oas://algod@v1.0.0` or `oas://indexer@feature-branch`

### Examples

```bash
# Using shorthand (recommended - single source of truth)
uv run --project api/oas-generator python -m oas_generator.cli \
  --spec oas://algod \
  --out src \
  --package algokit_algod_client

# Using shorthand with specific branch/tag
uv run --project api/oas-generator python -m oas_generator.cli \
  --spec oas://algod@v1.0.0 \
  --out src \
  --package algokit_algod_client

# Using a remote URL directly
uv run --project api/oas-generator python -m oas_generator.cli \
  --spec https://raw.githubusercontent.com/algorandfoundation/algokit-oas-generator/main/specs/algod.oas3.json \
  --out src \
  --package algokit_algod_client

# Using a local path
uv run --project api/oas-generator python -m oas_generator.cli \
  --spec api/specs/algod.oas3.json \
  --out src \
  --package algokit_algod_client
```

Follow up with `uv run ruff check --fix` and `uv run ruff format` on the regenerated package to keep formatting tidy.
