# AlgoKit Python Utilities

A set of core Algorand utilities written in Python and released via PyPi that make it easier to build solutions on Algorand.
This project is part of [AlgoKit](https://github.com/algorandfoundation/algokit-cli).

The goal of this library is to provide intuitive, productive utility functions that make it easier, quicker and safer to build applications on Algorand.
Largely these functions wrap the underlying Algorand SDK, but provide a higher level interface with sensible defaults and capabilities for common tasks.

> **Note**
> If you prefer TypeScript there's an equivalent [TypeScript utility library](https://github.com/algorandfoundation/algokit-utils-ts).

[Install](https://github.com/algorandfoundation/algokit-utils-py#install) | [Documentation](https://algorandfoundation.github.io/algokit-utils-py)

## Install

This library can be installed using pip, e.g.:

```
pip install algokit-utils
```

## Migration from `v2.x` to `v3.x`

Refer to the [v3 migration](./docs/source/v3-migration-guide.md) for more information on how to migrate to latest version of `algokit-utils-py`.

## Guiding principles

This library follows the [Guiding Principles of AlgoKit](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/algokit.md#guiding-principles).

## Contributing

This is an open source project managed by the Algorand Foundation.
See the [AlgoKit contributing page](https://github.com/algorandfoundation/algokit-cli/blob/main/CONTRIBUTING.MD) to learn about making improvements.

To successfully run the tests in this repository you need to be running LocalNet via [AlgoKit](https://github.com/algorandfoundation/algokit-cli):

```
algokit localnet start
```

### Mock Server Tests

Tests under `tests/modules/` use a mock server for deterministic API testing. By default, pytest spins up a Docker container automatically.

**Local development with external server:**

To test against a locally running mock server (e.g., when recording new HARs):

```bash
# Terminal 1: Start mock server (from algokit-polytest repo)
cd path/to/algokit-polytest/resources/mock-server
bun install && ALGOD_PORT=18000 bun bin/server.ts algod ./recordings

# Terminal 2: Run tests pointing to your server
MOCK_ALGOD_URL=http://localhost:18000 pytest tests/modules/algod_client/
```

| Environment Variable | Description |
|---------------------|-------------|
| `MOCK_ALGOD_URL` | External algod mock server URL |
| `MOCK_INDEXER_URL` | External indexer mock server URL |
| `MOCK_KMD_URL` | External KMD mock server URL |

When set, pytest uses the external server instead of Docker. The server must pass a health check.

Variables can be set via `.env` file in project root (copy from `.env.template`).
