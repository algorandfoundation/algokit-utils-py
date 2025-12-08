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

Tests under `tests/modules/` use a mock server for deterministic API testing against pre-recorded HAR files. The mock server is managed externally (not by pytest).

**In CI:** Mock servers are automatically started via the [algokit-polytest](https://github.com/algorandfoundation/algokit-polytest) GitHub Action.

**Local development:**

1. Clone algokit-polytest and start the mock servers:

```bash
# Clone algokit-polytest (if not already)
git clone https://github.com/algorandfoundation/algokit-polytest.git

# Start all mock servers (recommended)
cd algokit-polytest/resources/mock-server
./scripts/start_all_servers.sh
```

This starts algod (port 8000), kmd (port 8001), and indexer (port 8002) in the background.

2. Set environment variables and run tests:

```bash
export MOCK_ALGOD_URL=http://localhost:8000
export MOCK_INDEXER_URL=http://localhost:8002
export MOCK_KMD_URL=http://localhost:8001

# Run all module tests
pytest tests/modules/

# Or run specific client tests
pytest tests/modules/algod_client/
```

3. Stop servers when done:

```bash
cd algokit-polytest/resources/mock-server
./scripts/stop_all_servers.sh
```

| Environment Variable | Description | Default Port |
|---------------------|-------------|--------------|
| `MOCK_ALGOD_URL` | Algod mock server URL | 8000 |
| `MOCK_INDEXER_URL` | Indexer mock server URL | 8002 |
| `MOCK_KMD_URL` | KMD mock server URL | 8001 |

Environment variables can also be set via `.env` file in project root (copy from `.env.template`).
