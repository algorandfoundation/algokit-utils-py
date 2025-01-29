# AlgoKit Python Utilities

A set of core Algorand utilities written in Python and released via PyPi that make it easier to build solutions on Algorand. This project is part of [AlgoKit](https://github.com/algorandfoundation/algokit-cli).

The goal of this library is to provide intuitive, productive utility functions that make it easier, quicker and safer to build applications on Algorand. Largely these functions wrap the underlying Algorand SDK, but provide a higher level interface with sensible defaults and capabilities for common tasks.

```{note}
If you prefer TypeScript there's an equivalent [TypeScript utility library](https://github.com/algorandfoundation/algokit-utils-ts).
```

{ref}`Core principles <core-principles>` | {ref}`Installation <installation>` | {ref}`Usage <usage>` | {ref}`Config and logging <config-logging>` | {ref}`Capabilities <capabilities>` | {ref}`Reference docs <reference-documentation>`

```{toctree}
---
maxdepth: 2
caption: Contents
---

capabilities/account
capabilities/algorand-client
capabilities/amount
capabilities/app-client
capabilities/app-deploy
capabilities/app
capabilities/asset
capabilities/client
capabilities/debugging
capabilities/dispenser-client
capabilities/testing
capabilities/transaction-composer
capabilities/transaction
capabilities/transfer
capabilities/typed-app-clients
v3-migration-guide
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
# Point to a pre-created algod client
algorand = AlgorandClient.from_clients(algod=...)
# Point to a pre-created algod and indexer client
algorand = AlgorandClient.from_clients(algod=..., indexer=..., kmd=...)
# Point to custom configuration for algod
algod_config = AlgoClientNetworkConfig(server=..., token=..., port=...)
algorand = AlgorandClient.from_config(algod_config=algod_config)
# Point to custom configuration for algod and indexer and kmd
algod_config = AlgoClientNetworkConfig(server=..., token=..., port=...)
indexer_config = AlgoClientNetworkConfig(server=..., token=..., port=...)
kmd_config = AlgoClientNetworkConfig(server=..., token=..., port=...)
algorand = AlgorandClient.from_config(algod_config=algod_config, indexer_config=indexer_config, kmd_config=kmd_config)
```

# Testing

AlgoKit Utils provides a dedicated documentation page on various useful snippets that can be reused for testing with tools like [Pytest](https://docs.pytest.org/en/latest/):

- [Testing](capabilities/testing)

# Types

The library leverages Python's native type hints and is fully compatible with [MyPy](https://mypy-lang.org/) for static type checking.

All public abstractions and methods are organized in logical modules matching their domain functionality. You can import types either directly from the root module or from their source submodules. Refer to [API documentation](autoapi/index) for more details.

(config-logging)=

# Config and logging

To configure the AlgoKit Utils library you can make use of the [`Config`](autoapi/algokit_utils/config/index) object, which has a configure method that lets you configure some or all of the configuration options.

## Config singleton

The AlgoKit Utils configuration singleton can be updated using `config.configure()`. Refer to the [Config API documentation](autoapi/algokit_utils/config/index) for more details.

## Logging

AlgoKit has an in-built logging abstraction through the [`AlgoKitLogger`](apidocs/algokit_utils/config/index) class that provides standardized logging capabilities. The logger is accessible through the `config.logger` property and provides various logging levels.

Each method supports optional suppression of output using the `suppress_log` parameter.

## Debug mode

To turn on debug mode you can use the following:

```python
from algokit_utils.config import config
config.configure(debug=True)
```

To retrieve the current debug state you can use `debug` property.

This will turn on things like automatic tracing, more verbose logging and [advanced debugging](capabilities/debugger). It's likely this option will result in extra HTTP calls to algod os worth being careful when it's turned on.

(capabilities)=

# Capabilities

The library helps you interact with and develop against the Algorand blockchain with a series of end-to-end capabilities as described below:

- [**AlgorandClient**](./capabilities/algorand-client.md) - The key entrypoint to the AlgoKit Utils functionality
- **Core capabilities**
  - [**Client management**](./capabilities/client.md) - Creation of (auto-retry) algod, indexer and kmd clients against various networks resolved from environment or specified configuration, and creation of other API clients (e.g. TestNet Dispenser API and app clients)
  - [**Account management**](./capabilities/account.md) - Creation, use, and management of accounts including mnemonic, rekeyed, multisig, transaction signer, idempotent KMD accounts and environment variable injected
  - [**Algo amount handling**](./capabilities/amount.md) - Reliable, explicit, and terse specification of microAlgo and Algo amounts and safe conversion between them
  - [**Transaction management**](./capabilities/transaction.md) - Ability to construct, simulate and send transactions with consistent and highly configurable semantics, including configurable control of transaction notes, logging, fees, validity, signing, and sending behaviour
- **Higher-order use cases**
  - [**Asset management**](./capabilities/asset.md) - Creation, transfer, destroying, opting in and out and managing Algorand Standard Assets
  - [**Typed application clients**](./capabilities/typed-app-clients.md) - Type-safe application clients that are [generated](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/features/generate.md#1-typed-clients) from ARC-56 or ARC-32 application spec files and allow you to intuitively and productively interact with a deployed app, which is the recommended way of interacting with apps and builds on top of the following capabilities:
    - [**ARC-56 / ARC-32 App client and App factory**](./capabilities/app-client.md) - Builds on top of the App management and App deployment capabilities (below) to provide a high productivity application client that works with ARC-56 and ARC-32 application spec defined smart contracts
    - [**App management**](./capabilities/app.md) - Creation, updating, deleting, calling (ABI and otherwise) smart contract apps and the metadata associated with them (including state and boxes)
    - [**App deployment**](./capabilities/app-deploy.md) - Idempotent (safely retryable) deployment of an app, including deploy-time immutability and permanence control and TEAL template substitution
  - [**Algo transfers (payments)**](./capabilities/transfer.md) - Ability to easily initiate Algo transfers between accounts, including dispenser management and idempotent account funding
  - [**Automated testing**](./capabilities/testing.md) - Reusable snippets to leverage AlgoKit Utils abstractions in a manner that are useful for when writing tests in tools like [Pytest](https://docs.pytest.org/en/latest/).

(reference-documentation)=

# Reference documentation

For detailed API documentation, see the [auto-generated reference documentation](apidocs/algokit_utils/algokit_utils.md).
