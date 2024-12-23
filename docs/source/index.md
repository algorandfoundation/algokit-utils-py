# AlgoKit Python Utilities

A set of core Algorand utilities written in Python and released via PyPi that make it easier to build solutions on Algorand. This project is part of [AlgoKit](https://github.com/algorandfoundation/algokit-cli).

The goal of this library is to provide intuitive, productive utility functions that make it easier, quicker and safer to build applications on Algorand. Largely these functions wrap the underlying Algorand SDK, but provide a higher level interface with sensible defaults and capabilities for common tasks.

```{note}
If you prefer TypeScript there's an equivalent [TypeScript utility library](https://github.com/algorandfoundation/algokit-utils-ts).
```

[Core principles](#core-principles) | [Installation](#installation) | [Usage](#usage) | [Config and logging](#config-and-logging) | [Capabilities](#capabilities) | [Reference docs](#reference-documentation)

```{toctree}
---
maxdepth: 2
caption: Contents
---

capabilities/account
capabilities/client
capabilities/app-client
capabilities/app-deploy
capabilities/transfer
capabilities/dispenser-client
capabilities/debugger
capabilities/asset
capabilities/testing
capabilities/indexer
capabilities/transaction
capabilities/amount
capabilities/app
apidocs/algokit_utils/algokit_utils
```

(core-principles)=

# Core principles

This library follows the [Guiding Principles of AlgoKit](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/algokit.md#guiding-principles) and is designed with the following principles:

- **Modularity** - This library is a thin wrapper of modular building blocks over the Algorand SDK; the primitives from the underlying Algorand SDK are exposed and used wherever possible so you can opt-in to which parts of this library you want to use without having to use an all or nothing approach.
- **Type-safety** - This library provides strong type hints with effort put into creating types that provide good type safety and intellisense when used with tools like MyPy.
- **Productivity** - This library is built to make solution developers highly productive; it has a number of mechanisms to make common code easier and terser to write.

(installation)=

# Installation

This library can be installed from PyPi using pip or poetry:

```bash
pip install algokit-utils
# or
poetry add algokit-utils
```

(usage)=

# Usage

The main entrypoint to the bulk of the functionality in AlgoKit Utils is the `AlgorandClient` class. You can get started by using one of the static initialization methods to create an Algorand client:

```python
# Point to the network configured through environment variables or
# if no environment variables it will point to the default LocalNet configuration
algorand = AlgorandClient.from_environment()
# Point to default LocalNet configuration
algorand = AlgorandClient.default_localnet()
# Point to TestNet using AlgoNode free tier
algorand = AlgorandClient.testnet()
# Point to MainNet using AlgoNode free tier
algorand = AlgorandClient.mainnet()
```

# Config and logging

The library provides configuration and logging capabilities through the `config` module:

```python
from algokit_utils.config import config

# Enable debug mode
config.configure(debug=True)
# Configure project root for debug traces
config.configure(project_root=Path("./my-project"))
# Enable tracing of all operations
config.configure(trace_all=True)
```

(capabilities)=

# Capabilities

The library provides a comprehensive set of capabilities to interact with Algorand:

## Core capabilities

### Client Management

- Create and manage algod, indexer and kmd clients
- Auto-retry functionality for transient errors
- Environment-based configuration
- Network detection and information

### Account Management

- Create and manage various account types (mnemonic, multisig, rekeyed)
- Transaction signing and management
- KMD integration for LocalNet
- Environment variable injection

### Transaction Management

- Atomic transaction composition
- Transaction simulation
- Automatic resource population
- Fee management
- ABI method call support

### Amount Handling

- Safe Algo amount manipulation
- Explicit microAlgo/Algo conversion
- Arithmetic operations
- Comparison operations

## Higher-order Use Cases

### Application Management

- Smart contract deployment
- ARC-32/56 application clients
- State management
- Box storage
- Application calls

### Asset Management

- ASA creation and configuration
- Asset transfers
- Opt-in/out management
- Asset destruction

### Testing and Debugging

- Transaction simulation
- AVM Debugger support
- Trace management

### Utility Functions

- Algo transfers
- Account funding
- TestNet dispenser integration
- Indexer pagination

(reference-documentation)=

# Reference documentation

For detailed API documentation, see the [auto-generated reference documentation](apidocs/algokit_utils/algokit_utils.md).

# Contributing

This is an open source project managed by the Algorand Foundation. See the [AlgoKit contributing page](https://github.com/algorandfoundation/algokit-cli/blob/main/CONTRIBUTING.MD) to learn about making improvements.

To successfully run the tests in this repository you need to be running LocalNet via [AlgoKit](https://github.com/algorandfoundation/algokit-cli):

```bash
algokit localnet start
```

# Indices and tables

- {ref}`genindex`
