# v3 Migration Guide

Version 3 of `algokit-utils-ts` moved from a stateless function-based interface to a stateful class-based interfaces. This change allows for:

- Easier and simpler consumption experience guided by IDE autocompletion
- Less redundant parameter passing (e.g., `algod` client)
- Better performance through caching of commonly retrieved values like transaction parameters
- More consistent and intuitive API design
- Stronger type safety and better error messages
- Improved ARC-56 compatibility
- Feature parity with `algokit-utils-ts` >= `v7` interfaces

The entry point to most functionality in AlgoKit Utils is now available via a single entry-point, the `AlgorandClient` class.

The old version (in `algokit_utils._legacy_v2`) will still work until at least v4 (we have maintained backwards compatibility), but it exposes an older, function-based interface that is deprecated. The new way to use AlgoKit Utils is via the `AlgorandClient` class, which is easier, simpler, and more convenient to use and has powerful new features.

## Migration Steps

### Prerequisites

If you have previously relied on `beta` versions of `

### Step 1 - Replace SDK Clients with AlgorandClient

First, replace your SDK client initialization with `AlgorandClient`. Look for `get_algod_client` calls and replace with an appropriate `AlgorandClient` initialization:

```python
"""Before"""
import algokit_utils
algod = algokit_utils.get_algod_client()
indexer = algokit_utils.get_indexer_client()

"""After"""
from algokit_utils import AlgorandClient
algorand = AlgorandClient.from_environment()  # or .test_net(), .main_net(), etc.
```

During migration, you can still access SDK clients if needed:

```python
algod = algorand.client.algod
indexer = algorand.client.indexer
kmd = algorand.client.kmd
```

### Step 2 - Update Account Management

Account management has moved to `algorand.account`:

```python
"""Before"""
account = algokit_utils.get_account_from_mnemonic(
    mnemonic=os.getenv("MY_ACCOUNT_MNEMONIC"),
)
dispenser = algokit_utils.get_dispenser_account(algod)

"""After"""
account = algorand.account.from_mnemonic(os.getenv("MY_ACCOUNT_MNEMONIC"))
dispenser = algorand.account.dispenser_from_environment()
```

Key changes:

- `get_account` → `account.from_environment`
- `get_account_from_mnemonic` → `account.from_mnemonic`
- `get_dispenser_account` → `account.dispenser_from_environment`
- `get_localnet_default_account` → `account.local_net_dispenser`

### Step 3 - Update Transaction Management

Transaction creation and sending is now more structured:

```python
"""Before"""
result = algokit_utils.transfer_algos(
    from_account=account,
    to_addr="RECEIVER",
    amount=algokit_utils.algos(1),
    algod_client=algod,
)

"""After"""
result = algorand.send.payment(
    sender=account.address,
    receiver="RECEIVER",
    amount=(1).algo(),
)

# For transaction groups
"""Before"""
atc = AtomicTransactionComposer()
# ... add transactions ...
result = algokit_utils.execute_atc_with_logic_error(atc, algod)

"""After"""
composer = algorand.new_group()
# ... add transactions ...
result = composer.send()
```

Key changes:

- `transfer_algos` → `send.payment`
- `transfer_asset` → `send.asset_transfer`
- `execute_atc_with_logic_error` → `composer.send()`
- Transaction parameters are now more consistently named (e.g., `sender` instead of `from_account`)
- Amount handling uses extension methods (e.g., `(1).algo()` instead of `algos(1)`)

### Step 4 - Update Application Client Usage

The application client has been split into `AppClient` and `AppFactory`:

```python
"""Before"""
app_client = ApplicationClient(
    algod_client=algod,
    app_spec=app_spec,
    app_id=existing_app_id,
)

"""After"""
# For existing apps
app_client = AppClient(
    app_id=existing_app_id,
    app_spec=app_spec,
    algorand=algorand,
)

# For creating/deploying apps
app_factory = algorand.get_app_factory(
    app_spec=app_spec,
    app_name="MyApp",
)
```

Key changes in method calls:

```python
"""Before"""
result = app_client.call(
    method="hello",
    method_args=["World"],
    boxes=[("name", "box1")],
)

"""After"""
result = app_client.send.call(
    app_client.params.call(
        method="hello",
        args=["World"],
        box_references=[("name", "box1")],
    )
)
```

Notable changes:

- Split between `AppClient` (for existing apps) and `AppFactory` (for creation/deployment)
- More structured transaction building with `.params`, `.create_transaction`, and `.send`
- Consistent parameter naming (`args` instead of `method_args`, `box_references` instead of `boxes`)
- Better ARC-56 support for state management
- Improved error handling and debugging support

### Step 5 - Update State Management

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

### Step 6 - Update Asset Management

Asset management is now more consistent:

```python
"""Before"""
result = algokit_utils.opt_in(algod, account, [asset_id])

"""After"""
result = algorand.send.asset_opt_in(
    sender=account.address,
    asset_id=asset_id,
)
```

## Breaking Changes

1. **Client Management**

   - Removal of standalone client creation functions
   - All clients now accessed through `AlgorandClient`

2. **Account Management**

   - Account creation functions moved to `AccountManager`
   - Changed parameter names for consistency
   - Improved typing for account operations

3. **Transaction Management**

   - Restructured transaction creation and sending
   - Removed `skip_sending` parameter (use `create_transaction` instead)
   - Changed parameter names for consistency
   - New transaction composition interface

4. **Application Client**

   - Split into `AppClient` and `AppFactory`
   - New structured interface for transactions
   - Changed parameter names for consistency
   - Improved ARC-56 support

5. **State Management**

   - New hierarchical state access
   - Improved typing for state values
   - Better support for ARC-56 state schemas

6. **Asset Management**
   - Moved to consistent transaction interface
   - Changed parameter names for consistency

## Best Practices

1. Use the new `AlgorandClient` as the main entry point
2. Leverage IDE autocompletion to discover available functionality
3. Use the new parameter builders for type-safe transaction creation
4. Use the state accessor patterns for cleaner state management
5. Use transaction composition for atomic operations
6. Use source maps and debug mode for development
7. Use idempotent deployment patterns with versioning
8. Properly manage box references to avoid transaction failures
