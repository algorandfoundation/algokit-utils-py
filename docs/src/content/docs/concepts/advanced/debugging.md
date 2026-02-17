---
title: "Debugger"
description: "The AlgoKit Python Utilities package provides a set of debugging tools that can be used to simulate and trace transactions on the Algorand blockchain. These tools and methods are optimized for dev..."
---

The AlgoKit Python Utilities package provides a set of debugging tools that can be used to simulate and trace transactions on the Algorand blockchain. These tools and methods are optimized for developers who are building applications on Algorand and need to test and debug their smart contracts via [AlgoKit AVM Debugger extension](https://github.com/algorandfoundation/algokit-avm-vscode-debugger).

## Configuration

The `config.py` file contains the `UpdatableConfig` class which manages and updates configuration settings for the AlgoKit project.

To enable debug mode in your project you can configure it as follows:

```python
from algokit_utils.config import config

config.configure(
    debug=True,
)
```

> Note: Config also contains a set of flags that affect debugging behaviour. Those include `project_root`, `trace_all`, and `trace_buffer_size_mb`. Refer to the [API reference](/algokit-utils-py/api/autoapi/algokit_utils/config/) for details.

## Debugging utilities

Unlike the TypeScript version (which uses a [separate addon package](https://github.com/algorandfoundation/algokit-utils-ts-debug)), the Python debugging utilities are built directly into `algokit-utils-py`. When debug mode is enabled, AlgoKit Utils will automatically:

- Generate transaction traces compatible with the AVM Debugger
- Manage trace file storage with automatic cleanup
- Provide source map generation for TEAL contracts

### Manual debugging operations

The following methods are provided for manual debugging operations:

- `persist_sourcemaps`: Persists sourcemaps for given TEAL contracts as AVM Debugger-compliant artifacts. Parameters:

  - `sources`: List of `PersistSourceMapInput` sources to generate sourcemaps for
  - `project_root`: Project root directory for storage
  - `client`: `AlgodClient` instance
  - `with_sources`: Whether to include TEAL source files (default: `True`)

- `simulate_and_persist_response`: Simulates transactions and persists debug traces. Parameters:
  - `composer`: `TransactionComposer` containing transactions
  - `project_root`: Project root directory for storage
  - `algod`: `AlgodClient` instance
  - `buffer_size_mb`: Maximum trace storage in MB (default: `None`; when `None` and `trace_all` is enabled, falls back to `config.trace_buffer_size_mb` which defaults to `256`)
  - `result`: Optional pre-existing simulation result

### Trace filename format

The trace files are named in a specific format to provide useful information about the transactions they contain. The format is as follows:

```
${timestamp}_lr${last_round}_${transaction_types}.trace.avm.json
```

Where:

- `timestamp`: The time when the trace file was created in UTC, formatted as `YYYYMMDD_HHMMSS` (e.g., `20220301_123456`).
- `last_round`: The last round when the simulation was performed.
- `transaction_types`: A string representing the types and counts of transactions in the atomic group. Each transaction type is represented as `${count}${type}`, and different transaction types are separated by underscores.

For example, a trace file might be named `20220301_123456_lr1000_2pay_1axfer.trace.avm.json`, indicating that the trace file was created at `2022-03-01 12:34:56 UTC`, the last round was `1000`, and the atomic group contained 2 payment transactions and 1 asset transfer transaction.
