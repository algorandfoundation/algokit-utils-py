# Migration Guide - v3

Version 3 of `algokit-utils-ts` moved from a stateless function-based interface to a stateful class-based interfaces. This change allows for:

- Easier and simpler consumption experience guided by IDE autocompletion
- Less redundant parameter passing (e.g., `algod` client)
- Better performance through caching of commonly retrieved values like transaction parameters
- More consistent and intuitive API design
- Stronger type safety and better error messages
- Improved ARC-56 compatibility
- Feature parity with `algokit-utils-ts` >= `v7` interfaces

The entry point to most functionality in AlgoKit Utils is now available via a single entry-point, the `AlgorandClient` class.

The v2 interfaces and abstractions will be removed in future major version bumps, however in order to ensure gradual migration, _all v2 abstractions are available_ with respective deprecation warnings. The new way to use AlgoKit Utils is via the `AlgorandClient` class, which is easier, simpler, and more convenient to use and has powerful new features.

> BREAKING CHANGE: the `beta` module is now removed, any imports from `algokit_utils.beta` will now raise an error with a link to a new expected import path. This is due to the fact that the interfaces introduced in `beta` are now refined and available in the main module.

## Migration Steps

In general, your codebase might fall into one of the following migration scenarios:

- Using `algokit-utils-py` v2.x only without use of abstractions from `beta` module
- Using `algokit-utils-py` v2.x only and with use of abstractions from `beta` module
- Using `algokit-utils-py` v2.x with `algokit-client-generator-py` v1.x
- Using `algokit-client-generator-py` v1.x only (implies implicit dependency on `algokit-utils-py` v2.x)

Given that `algokit-utils-py` v3.x is backwards compatible with `algokit-client-generator-py` v1.x, the following general guidelines are applicable to all scenarios (note that the order of operations is important to ensure straight-forward migration):

1.  Upgrade to `algokit-utils-py` v3.x
    - 1.1 (If used) Update imports from `algokit_utils.beta` to `algokit_utils`
    - 1.2 Follow hints in deprecation warnings to update your codebase to rely on latest v3 interfaces
2.  Upgrade to `algokit-client-generator-py` v2.x and regenerate typed clients
    - 2.1 Follow `algokit-client-generator-py` [v2.x migration guide](https://github.com/algorandfoundation/algokit-client-generator-py/blob/main/docs/v2-migration-guide.md)

The remaining set of guidelines are outlining migrations for specific abstractions that had direct equivalents in `algokit-utils-py` v2.x.

### Prerequisites

It is important to reiterate that if you have previously relied on `beta` versions of `algokit-utils-py` v2.x, you will need to update your imports to rely on the new interfaces. Errors thrown during import from `beta` will provide a description of the new expected import path.

> As with `v2.x` all public abstractions in `algokit_utils` are available for direct imports `from algokit_utils import ...`, however underlying modules have been refined to be structured loosely around common AVM domains such as `applications`, `transactions`, `accounts`, `assets`, etc. See [API reference](https://algokit-utils-py.readthedocs.io/en/latest/api_reference/index.html) for latest and detailed overview.

### Step 1 - Replace SDK Clients with AlgorandClient

First, replace your SDK client initialization with `AlgorandClient`. Look for `get_algod_client` calls and replace with an appropriate `AlgorandClient` initialization:

```python
"""Before"""
import algokit_utils
algod = algokit_utils.get_algod_client()
indexer = algokit_utils.get_indexer_client()

"""After"""
from algokit_utils import AlgorandClient
algorand = AlgorandClient.from_environment()  # or .testnet(), .mainnet(), etc.
```

During migration, you can still access SDK clients if needed:

```python
algod = algorand.client.algod
indexer = algorand.client.indexer
kmd = algorand.client.kmd
```

### Step 2 - Update Account Management

Account management has moved to `algorand.account`:

#### Before:

```python
account = algokit_utils.get_account_from_mnemonic(
    mnemonic=os.getenv("MY_ACCOUNT_MNEMONIC"),
)
dispenser = algokit_utils.get_dispenser_account(algod)
```

#### After:

```python
account = algorand.account.from_mnemonic(os.getenv("MY_ACCOUNT_MNEMONIC"))
dispenser = algorand.account.dispenser_from_environment()
```

Key changes:

- `get_account` → `account.from_environment`
- `get_account_from_mnemonic` → `account.from_mnemonic`
- `get_dispenser_account` → `account.dispenser_from_environment`
- `get_localnet_default_account` → `account.localnet_dispenser`

### Step 3 - Update Transaction Management

Transaction creation and sending is now more structured:

#### Before:

```python
# Single transaction
result = algokit_utils.transfer_algos(
    from_account=account,
    to_addr="RECEIVER",
    amount=algokit_utils.algos(1),
    algod_client=algod,
)

# Transaction groups
atc = AtomicTransactionComposer()
# ... add transactions ...
result = algokit_utils.execute_atc_with_logic_error(atc, algod)
```

#### After:

```python
# Single transaction
result = algorand.send.payment(
    sender=account.address,
    receiver="RECEIVER",
    amount=AlgoAmount.from_algo(1),
)

# Transaction groups
composer = algorand.new_group()
# ... add transactions ...
result = composer.send()
```

Key changes:

- `transfer_algos` → `algorand.send.payment`
- `transfer_asset` → `algorand.send.asset_transfer`
- `execute_atc_with_logic_error` → `composer.send()`
- Transaction parameters are now more consistently named (e.g., `sender` instead of `from_account`)
- Improved amount handling with dedicated `AlgoAmount` class (e.g., `AlgoAmount.from_algo(1)`)

### Step 4 - Update `ApplicationSpecification` usage

`ApplicationSpecification` abstraction is largely identical to v2, however it's been renamed to `Arc32Contract` to better reflect the fact that it's a contract specification for a specific ARC and addition of `Arc56Contract` supporting the latest recommended conventions. Hence the main actionable change is to update your import to `from algokit_utils import Arc32Contract` and rename `ApplicationSpecification` to `Arc32Contract`.

You can instantiate an `Arc56Contract` instance from an `Arc32Contract` instance using the `Arc56Contract.from_arc32` method. For instance:

```python
testing_app_arc32_app_spec = Arc32Contract.from_json(app_spec_json)
arc56_app_spec = Arc56Contract.from_arc32(testing_app_arc32_app_spec)
```

> Despite auto conversion of ARC-32 to ARC-56, we recommend recompiling your contract to a fully compliant ARC-56 specification given that auto conversion would skip populating information that can't be parsed from raw ARC-32.

### Step 5 - Update `ApplicationClient` usage

The application client has been in v2 has been responsible for instantiation, deployment and calling of the application. In v3, this has been split into `AppClient`, `AppDeployer` and `AppFactory` to better reflect the different responsibilities:

```python
"""Before (v2 deployment)"""
from algokit_utils import ApplicationClient, OnUpdate, OnSchemaBreak

# Initialize client with manual configuration
app_client = ApplicationClient(
    algod_client=algod,
    app_spec=app_spec,
    creator=creator,
    app_name="MyApp"
)

# Deployment with versioning and update policies
deploy_result = app_client.deploy(
    version="1.0",
    allow_update=True,
    allow_delete=False,
    on_update=OnUpdate.UpdateApp,
    on_schema_break=OnSchemaBreak.Fail
)

# Post-deployment calls
response = app_client.call("initialize", args=["config"])


"""After (v3 factory-based deployment)"""
from algokit_utils import AppFactory, OnUpdate, OnSchemaBreak

# Factory-based deployment with compiled parameters
app_factory = AppFactory(
    AppFactoryParams(
        algorand=algorand,
        app_spec=app_spec,
        app_name="MyApp",
        compilation_params=AppClientCompilationParams(
            deploy_time_params={"VERSION": 1},
            updatable=True,  # Replaces allow_update
            deletable=False  # Replaces allow_delete
        )
    )
)

app_client, deploy_result = app_factory.deploy(
    version="1.0",
    on_update=OnUpdate.UpdateApp,
    on_schema_break=OnSchemaBreak.Fail,
) # Returns a tuple of (app_client, deploy_result)

# Type-safe post-deployment calls
response = app_client.send.call("setup", args=[{"max_users": 100}])
```

Notable changes:

- Split between `AppClient`, `AppDeployer` (for raw creation/deployment) and `AppFactory` (for creation/deployment using factory patterns). In majority of cases, you will only need `AppFactory` as it provides convenience methods for instantiation of `AppClient` and mediates calls to `AppDeployer`.
- More structured transaction building with `.params`, `.create_transaction`, and `.send`
- Consistent parameter naming (`args` instead of `method_args`, `box_references` instead of `boxes`)
- ARC-56 support for state management
- Improved error handling and debugging support

### Step 6 - Update `AppClient` State Management

State management is now more structured and type-safe:

```python
"""Before"""
global_state = app_client.get_global_state()
local_state = app_client.get_local_state(account_address)
box_value = app_client.get_box_value("box_name")

"""After"""
# Global state
global_state = app_client.state.global_state.get_all()
value = app_client.state.global_state.get_value("key_name")
map_value = app_client.state.global_state.get_map_value("map_name", "key")

# Local state
local_state = app_client.state.local_state(account_address).get_all()
value = app_client.state.local_state(account_address).get_value("key_name")
map_value = app_client.state.local_state(account_address).get_map_value("map_name", "key")

# Box storage
box_value = app_client.state.box.get_value("box_name")
boxes = app_client.state.box.get_all()
map_value = app_client.state.box.get_map_value("map_name", "key")
```

### Step 7 - Update Asset Management

Asset management is now more consistent:

```python
"""Before"""
result = algokit_utils.opt_in(algod, account, [asset_id])

"""After"""
result = algorand.send.asset_opt_in(
    params=AssetOptInParams(
        sender=account.address,
        asset_id=asset_id,
    )
)
```

## Breaking Changes

1. **Client Management**

   - Removal of standalone client creation functions
   - All clients now accessed through `AlgorandClient`

2. **Account Management**

   - Account creation functions moved to `AccountManager` accessible via `algorand.account` property
   - Unified `TransactionSignerAccountProtocol` with compliant and typed `SigningAccount`, `TransactionSignerAccount`, `LogicSigAccount`, `MultiSigAccount` classes encapsulating low level `algosdk` abstractions.
   - Improved typing for account operations, such as obtaining account information from `algod`, returning a typed information object.

3. **Transaction Management**

   - Consistent and intuitive transaction creation and sending interface accessible via `algorand.{send|params|create_transaction}` properties
   - New transaction composition interface accessible via `algorand.new_group`
   - Removing necessity to interact with low level and untyped `algosdk` abstractions for assembling, signing and sending transaction(s).

4. **Application Client**

   - Split into `AppClient`, `AppDeployer` and `AppFactory`
   - New intuitive structured interface for creating or sending `AppCall`|`AppMethodCall` transactions
   - ARC-56 support along with automatic conversion of specs from ARC-32 to ARC-56

5. **State Management**

   - New hierarchical state access available via `app_client.state.{global_state|local_state|box}` properties
   - Improved typing for state values
   - Support for ARC-56 state schemas

6. **Asset Management**
   - Dedicated `AssetManager` class for asset management accessible via `algorand.asset` property
   - Improved typing for asset operations, such as obtaining asset information from `algod`, returning a typed information object.
   - Consistent interface for asset opt-in, transfer, freeze, etc.

## Best Practices

1. Use the new `AlgorandClient` as the main entry point
2. Leverage IDE autocompletion to discover available functionality, consult with [API reference](https://algokit-utils-py.readthedocs.io/en/latest/api_reference/index.html) when unsure
3. Use the transaction parameter builders for type-safe transaction creation (`algorand.params.{}`)
4. Use the state accessor patterns for cleaner state management {`algorand.state.{}`}
5. Use high level `TransactionComposer` interface over low level `algosdk` abstractions (where possible)
6. Use source maps and debug mode to quickly troubleshoot on-chain errors
7. Use idempotent deployment patterns with versioning

## Troubleshooting

### A v2 interface/method/class does not display a deprecation warning correctly or at all

Submit an issue to [algokit-utils-py](https://github.com/algorandfoundation/algokit-utils-py/issues) with a description of the problem and the code that is causing it.

### Useful scenario of converting v2 to v3 not covered in generic migration guide

If you have a scenario that you think is useful and not covered in the generic migration guide, please submit an issue to [algokit-utils-py](https://github.com/algorandfoundation/algokit-utils-py/issues) with a scenario.
