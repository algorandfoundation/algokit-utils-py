---
title: "Automated testing"
description: "Automated testing is a higher-order use case capability provided by AlgoKit Utils that builds on top of the core capabilities. It allows you to use terse, robust automated testing primitives..."
---

Automated testing is a higher-order use case capability provided by AlgoKit Utils that builds on top of the core capabilities. It allows you to use terse, robust automated testing primitives that work with [pytest](https://docs.pytest.org/en/latest/) to facilitate fixture management, quickly generating isolated and funded test accounts, transaction logging, and log capture.

To see some usage examples check out all of the [automated tests](https://github.com/algorandfoundation/algokit-utils-py/tree/main/tests). Alternatively, you can see examples of using this library to test smart contracts with the various test files in the repository (AlgoKit Utils [dogfoods](https://en.wikipedia.org/wiki/Eating_your_own_dog_food) its own testing library).

## Module import

AlgoKit Utils testing functionality is accessed through the main `algokit_utils` module along with standard pytest patterns:

```python
import pytest
from algokit_utils import AlgorandClient, AddressWithSigners
from algokit_utils.models.amount import AlgoAmount
```

## Algorand fixture

In general, the primary entrypoint for testing is creating a pytest fixture that provides an [`AlgorandClient`](../../core/algorand-client) configured for LocalNet. This fixture, combined with account fixtures, exposes all the functionality you need to write isolated, repeatable tests.

```python
import pytest
from algokit_utils import AlgorandClient

@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()
```

### Using with pytest

To integrate with [pytest](https://docs.pytest.org/en/latest/) you define fixtures and use them in your test functions. Pytest's fixture system provides automatic dependency injection and scope control.

#### Per-test isolation

```python
import pytest
from algokit_utils import AlgorandClient, AddressWithSigners
from algokit_utils.models.amount import AlgoAmount

@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()

@pytest.fixture
def test_account(algorand: AlgorandClient) -> AddressWithSigners:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account,
        dispenser,
        min_spending_balance=AlgoAmount.from_algo(10),
    )
    algorand.set_signer(sender=new_account.addr, signer=new_account.signer)
    return new_account

def test_my_test(algorand: AlgorandClient, test_account: AddressWithSigners):
    # Test stuff!
    pass
```

#### Test suite isolation

```python
import pytest
from algokit_utils import AlgorandClient, AddressWithSigners
from algokit_utils.models.amount import AlgoAmount

@pytest.fixture(scope="module")
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()

@pytest.fixture(scope="module")
def test_account(algorand: AlgorandClient) -> AddressWithSigners:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account,
        dispenser,
        min_spending_balance=AlgoAmount.from_algo(10),
    )
    algorand.set_signer(sender=new_account.addr, signer=new_account.signer)
    return new_account

def test_my_test(algorand: AlgorandClient, test_account: AddressWithSigners):
    # Test stuff!
    pass
```

Refer to [pytest fixture scopes](https://docs.pytest.org/en/latest/how-to/fixtures.html#fixture-scopes) for more information on how to control the lifecycle of fixtures.

### Fixture configuration

When creating your `AlgorandClient` fixture you can optionally configure the client setup:

- `AlgorandClient.default_localnet()` - Creates a client against default LocalNet (default, no configuration needed)
- `AlgorandClient.from_environment()` - Creates a client against environment variables defined network
- `AlgorandClient.from_clients(algod=..., indexer=..., kmd=...)` - Creates a client from specific SDK client instances
- `AlgorandClient.from_config(algod_config=..., indexer_config=..., kmd_config=...)` - Creates a client from specific client configurations

For test account funding, you can control the amount:

```python
@pytest.fixture
def test_account(algorand: AlgorandClient) -> AddressWithSigners:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account,
        dispenser,
        min_spending_balance=AlgoAmount.from_algo(100),  # Custom funding amount
    )
    return new_account
```

### Using the fixture context

The `algorand` fixture provides access to an [`AlgorandClient`](../../core/algorand-client) instance which exposes the following properties commonly used in testing:

- `algorand.client.algod` - Algod client instance
- `algorand.client.indexer` - Indexer client instance (if configured)
- `algorand.client.kmd` - KMD client instance (if configured)
- `algorand.account` - [`AccountManager`](../../core/account) for creating and managing test accounts
- `algorand.send` - Methods for sending transactions
- `algorand.app` - Methods for interacting with applications

You can create additional test account fixtures for specific test needs:

```python
@pytest.fixture
def funded_account(algorand: AlgorandClient) -> AddressWithSigners:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account,
        dispenser,
        min_spending_balance=AlgoAmount.from_algo(10),
    )
    algorand.set_signer(sender=new_account.addr, signer=new_account.signer)
    return new_account
```

## Log capture fixture

If you want to capture log messages from AlgoKit that are issued within your test so that you can assert on them or parse them for debugging information, you can configure the AlgoKit logger in a pytest fixture.

```python
import logging

@pytest.fixture(autouse=True)
def capture_logs(caplog: pytest.LogCaptureFixture):
    with caplog.at_level(logging.DEBUG):
        yield caplog
```

### Using with pytest

To capture logs in pytest, use the built-in `caplog` fixture:

```python
import logging
import pytest

@pytest.fixture(autouse=True)
def capture_logs(caplog: pytest.LogCaptureFixture):
    with caplog.at_level(logging.DEBUG):
        yield caplog

def test_my_test(algorand: AlgorandClient, test_account: AddressWithSigners, capture_logs):
    # Test stuff!

    # Access captured logs
    captured = capture_logs.text
    # do stuff with the logs
```

### Snapshot testing the logs

If you want to quickly pin some behaviour of what logic you have does in terms of invoking AlgoKit methods you can use [pytest-snapshot](https://pypi.org/project/pytest-snapshot/) or [syrupy](https://github.com/toptal/syrupy) for snapshot / approval testing of captured log output.

This might look something like this:

```python
def test_deploy_logging(algorand, test_account, capture_logs, snapshot):
    factory = algorand.client.get_app_factory(
        app_spec=app_spec,
        default_sender=test_account.addr,
    )
    app_client, result = factory.deploy()

    assert capture_logs.text == snapshot
```

## Getting a test account

When testing, it's often useful to ephemerally generate random accounts, fund them with some number of Algo and then use that account to perform transactions. By creating an ephemeral, random account you naturally get isolation between tests and test runs and don't need to start from a specific blockchain network state. This makes tests less flakey, and also means the same test can be run against LocalNet and (say) TestNet.

The key when generating a test account is getting hold of a [dispenser](./transfer#dispenser) and then [ensuring the test account is funded](./transfer#ensure_funded).

To make it easier to quickly get a test account, the following mechanisms are available:

- `algorand.account.random()` - Generates a new random Algorand account
- `algorand.account.localnet_dispenser()` - Gets the LocalNet [dispenser](./transfer#dispenser) account for funding
- `algorand.account.dispenser_from_environment()` - Gets dispenser from environment variables or LocalNet
- `algorand.account.ensure_funded(account, dispenser, min_spending_balance=...)` - [Ensures the account is funded](./transfer#ensure_funded) with a minimum balance
- `algorand.account.from_environment(name)` - Loads an account from environment variables (auto-creates on LocalNet)

A typical pattern for creating funded test accounts is:

```python
def generate_account(algorand: AlgorandClient, initial_funds: AlgoAmount = AlgoAmount.from_algo(10)) -> AddressWithSigners:
    account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        account,
        dispenser,
        min_spending_balance=initial_funds,
    )
    algorand.set_signer(sender=account.addr, signer=account.signer)
    return account
```
