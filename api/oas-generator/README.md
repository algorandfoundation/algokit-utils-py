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
- `parser.py` / `loader.py` – read & validate OpenAPI specs
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

```bash
uv run --project api/oas-generator python -m oas_generator.cli \
  --spec api/specs/algod.oas3.json \
  --out src \
  --package algokit_algod_client
```

Follow up with `uv run ruff check --fix` and `uv run ruff format` on the regenerated package to keep formatting tidy.
