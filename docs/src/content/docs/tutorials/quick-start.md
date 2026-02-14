---
title: "Quick Start"
description: "Get up and running with AlgoKit Utils for Python — installation, initialization, and your first transaction."
---

AlgoKit Utils for Python provides intuitive, productive utility functions that make it easier, quicker, and safer to build applications on Algorand. It wraps the underlying Algorand SDK with a higher-level interface, sensible defaults, and capabilities for common tasks.

## Prerequisites

- Python 3.12+
- An Algorand node to connect to (or [AlgoKit LocalNet](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/features/localnet.md) for local development)

## Installation

Install via pip, poetry, or uv:

```bash
pip install algokit-utils
# or
poetry add algokit-utils
# or
uv add algokit-utils
```

## Core Principles

This library follows the [Guiding Principles of AlgoKit](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/algokit.md#guiding-principles):

- **Modularity** — A thin wrapper of modular building blocks over the Algorand SDK; opt-in to which parts you want without an all-or-nothing approach.
- **Type-safety** — Strong type hints with full [MyPy](https://mypy-lang.org/) compatibility for static type checking and IDE intellisense.
- **Productivity** — Common code made easier and terser to write, so you can focus on your application logic.

## Getting Started

The main entrypoint to AlgoKit Utils is the `AlgorandClient` class:

```python
from algokit_utils import AlgorandClient

# Connect to LocalNet (default for local development)
algorand = AlgorandClient.default_localnet()

# Or connect via environment variables
algorand = AlgorandClient.from_environment()

# Or connect to TestNet / MainNet via AlgoNode free tier
algorand = AlgorandClient.testnet()
algorand = AlgorandClient.mainnet()

# Or use custom configuration
from algokit_utils import AlgoClientNetworkConfig
algod_config = AlgoClientNetworkConfig(server="https://...", token="...", port=443)
algorand = AlgorandClient.from_config(algod_config=algod_config)
```

## Sending Your First Transaction

Here's a complete example that creates a funded account on LocalNet and sends a payment:

```python
from algokit_utils import AlgorandClient, AlgoAmount, PaymentParams

# Connect to LocalNet
algorand = AlgorandClient.default_localnet()

# Create and fund a new account
account = algorand.account.random()
dispenser = algorand.account.localnet_dispenser()
algorand.account.ensure_funded(
    account,
    dispenser,
    min_spending_balance=AlgoAmount.from_algo(10),
)

# Send a payment
result = algorand.send.payment(
    PaymentParams(
        sender=account.addr,
        receiver=dispenser.addr,
        amount=AlgoAmount.from_algo(1),
    )
)

print(f"Transaction ID: {result.tx_id}")
```

## Deploying a Smart Contract

Use `AppFactory` to deploy and interact with smart contracts:

```python
from algokit_utils import AlgorandClient, AlgoAmount

algorand = AlgorandClient.default_localnet()
deployer = algorand.account.random()
dispenser = algorand.account.localnet_dispenser()
algorand.account.ensure_funded(
    deployer,
    dispenser,
    min_spending_balance=AlgoAmount.from_algo(10),
)

# Create a factory from an ARC-56/ARC-32 app spec
factory = algorand.client.get_app_factory(
    app_spec="path/to/application.json",
    default_sender=deployer.addr,
)

# Deploy the app
app_client, deploy_result = factory.deploy()

print(f"App ID: {deploy_result.app.app_id}")
print(f"App Address: {deploy_result.app.app_address}")
```

## Config and Logging

Configure AlgoKit Utils behaviour using the config singleton:

```python
from algokit_utils.config import config

# Enable debug mode (automatic tracing, verbose logging)
config.configure(debug=True)

# Enable automatic resource population for app calls
config.configure(populate_app_call_resources=True)
```

> [!WARNING]
> Debug mode may result in extra HTTP calls to algod. Use it carefully in production environments.

## What's Next?

Explore the key capabilities of AlgoKit Utils:

- [**AlgorandClient**](/algokit-utils-py/concepts/core/algorand-client/) — The main entrypoint to all functionality
- [**Account Management**](/algokit-utils-py/concepts/core/account/) — Create and manage accounts
- [**App Client**](/algokit-utils-py/concepts/building/app-client/) — Deploy and interact with smart contracts
- [**Transaction Composer**](/algokit-utils-py/concepts/advanced/transaction-composer/) — Build complex transaction groups
- [**Testing**](/algokit-utils-py/concepts/building/testing/) — Patterns for testing with pytest

> [!NOTE]
> If you prefer TypeScript, there's an equivalent [TypeScript utility library](https://github.com/algorandfoundation/algokit-utils-ts).