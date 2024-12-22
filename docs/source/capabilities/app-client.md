# App Client and App Factory

> [!NOTE]
> This page covers the untyped app client, but we recommend using typed clients (coming soon), which will give you a better developer experience with strong typing specific to the app itself.

App client and App factory are higher-order use case capabilities provided by AlgoKit Utils that builds on top of the core capabilities, particularly [App deployment](./app-deploy.md) and [App management](./app.md). They allow you to access high productivity application clients that work with [ARC-56](https://github.com/algorandfoundation/ARCs/pull/258) and [ARC-32](https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0032.md) application spec defined smart contracts, which you can use to create, update, delete, deploy and call a smart contract and access state data for it.

> [!NOTE]
> If you are confused about when to use the factory vs client the mental model is: use the client if you know the app ID, use the factory if you don't know the app ID (deferred knowledge or the instance doesn't exist yet on the blockchain) or you have multiple app IDs

## `AppFactory`

The `AppFactory` is a class that, for a given app spec, allows you to create and deploy one or more app instances and to create one or more app clients to interact with those (or other) app instances.

To get an instance of `AppFactory` you can use `AlgorandClient` via `algorand.get_app_factory`:

```python
from algokit_utils.clients import AlgorandClient

# Create an Algorand client
algorand = AlgorandClient.from_environment()

# Minimal example
factory = algorand.get_app_factory(
    app_spec=app_spec,  # ARC-0032 or ARC-0056 app spec
)

# Advanced example
factory = algorand.get_app_factory(
    app_spec=app_spec,  # ARC-0032 or ARC-0056 app spec
    app_name="MyApp",
    default_sender="SENDER_ADDRESS",
    default_signer=signer,
    version="1.0.0",
    updatable=True,
    deletable=True,
    deploy_time_params={"TMPL_VALUE": "value"},
)
```

## `AppClient`

The `AppClient` is a class that, for a given app spec, allows you to manage calls and state for a specific deployed instance of an app (with a known app ID).

To get an instance of `AppClient` you can use `AlgorandClient` via `get_app_client_by_id` or use the factory methods:

```python
from algokit_utils.clients import AlgorandClient

# Create an Algorand client
algorand = AlgorandClient.from_environment()

# Get client by ID
client = algorand.get_app_client_by_id(
    app_spec=app_spec,  # ARC-0032 or ARC-0056 app spec
    app_id=existing_app_id,  # Use 0 for new app
    app_name="MyApp",  # Optional: Name of the app
    default_sender="SENDER_ADDRESS",  # Optional: Default sender address
    default_signer=signer,  # Optional: Default signer for transactions
    approval_source_map=approval_map,  # Optional: Source map for approval program
    clear_source_map=clear_map,  # Optional: Source map for clear program
)

# Get client by creator and name using factory
factory = algorand.get_app_factory(app_spec=app_spec)
client = factory.get_app_client_by_creator_and_name(
    creator_address="CREATOR_ADDRESS",
    app_name="MyApp",
    ignore_cache=False,  # Optional: Whether to ignore app lookup cache
)
```

You can get the `app_id` and `app_address` at any time as properties on the `AppClient` along with `app_name` and `app_spec`.

## Dynamically creating clients for a given app spec

As well as allowing you to control creation and deployment of apps, the `AppFactory` allows you to conveniently create multiple `AppClient` instances on-the-fly with information pre-populated.

This is possible via two methods on the app factory:

- `factory.get_app_client_by_id(params)` - Returns a new `AppClient` client for an app instance of the given ID. Automatically populates app_name, default_sender and source maps from the factory if not specified in the params.
- `factory.get_app_client_by_creator_and_name(params)` - Returns a new `AppClient` client, resolving the app by creator address and name using AlgoKit app deployment semantics (i.e. looking for the app creation transaction note). Automatically populates app_name, default_sender and source maps from the factory if not specified in the params.

```python
# Get clients by ID
client1 = factory.get_app_client_by_id(app_id=12345)
client2 = factory.get_app_client_by_id(app_id=12346)
client3 = factory.get_app_client_by_id(
    app_id=12345,
    default_sender="SENDER2_ADDRESS"
)

# Get clients by creator and name
client4 = factory.get_app_client_by_creator_and_name(
    creator_address="CREATOR_ADDRESS",
)
client5 = factory.get_app_client_by_creator_and_name(
    creator_address="CREATOR_ADDRESS",
    app_name="NonDefaultAppName",
)
client6 = factory.get_app_client_by_creator_and_name(
    creator_address="CREATOR_ADDRESS",
    app_name="NonDefaultAppName",
    ignore_cache=True,  # Perform fresh indexer lookups
    default_sender="SENDER2_ADDRESS",
)
```

## Creating and deploying an app

Once you have an [app factory](#appfactory) you can perform the following actions:

- `factory.create(params?)` - Signs and sends a transaction to create an app and returns the result of that call and an `AppClient` instance for the created app
- `factory.deploy(params)` - Uses the creator address and app name pattern to find if the app has already been deployed or not and either creates, updates or replaces that app based on the deployment rules (i.e. it's an idempotent deployment) and returns the result of the deployment and an `AppClient` instance for the created/updated/existing app

### Create

The create method is a wrapper over the `app_create` (bare calls) and `app_create_method_call` (ABI method calls) methods, with the following differences:

- You don't need to specify the `approval_program`, `clear_state_program`, or `schema` because these are all specified or calculated from the app spec (noting you can override the `schema`)
- `sender` is optional and if not specified then the `default_sender` from the `AppFactory` constructor is used (if it was specified, otherwise an error is thrown)
- `deploy_time_params`, `updatable` and `deletable` can be passed in to control deploy-time parameter replacements and deploy-time immutability and permanence control; these values can also be passed into the `AppFactory` constructor instead and if so will be used if not defined in the params to the create call

```python
# Use no-argument bare-call
create_response = factory.send.bare.create()

# Specify parameters for bare-call and override other parameters
create_response = factory.send.bare.create(
    params=factory.params.bare.create(
        args=[bytes([1, 2, 3, 4])],
        on_complete=OnComplete.OptIn,
        deploy_time_params={
            "ONE": 1,
            "TWO": "two",
        },
        updatable=True,
        deletable=False,
        populate_app_call_resources=True,
    )
)

# Specify parameters for ABI method call
create_response = factory.send.create(
    params=factory.params.create(
        method="create_application",
        args=[1, "something"],
    )
)
```

If you want to construct a custom create call, you can get params objects:

- `factory.params.create(params)` - ABI method create call for deploy method
- `factory.params.bare.create(params)` - Bare create call for deploy method

### Deploy

The deploy method is a wrapper over the `AppDeployer`'s `deploy` method, with the following differences:

- You don't need to specify the `approval_program`, `clear_state_program`, or `schema` in the `create_params` because these are all specified or calculated from the app spec (noting you can override the `schema`)
- `sender` is optional for `create_params`, `update_params` and `delete_params` and if not specified then the `default_sender` from the `AppFactory` constructor is used (if it was specified, otherwise an error is thrown)
- You don't need to pass in `metadata` to the deploy params - it's calculated from:
  - `updatable` and `deletable`, which you can optionally pass in directly to the method params
  - `version` and `name`, which are optionally passed into the `AppFactory` constructor
- `deploy_time_params`, `updatable` and `deletable` can all be passed into the `AppFactory` and if so will be used if not defined in the params to the deploy call for deploy-time parameter replacements and deploy-time immutability and permanence control
- `create_params`, `update_params` and `delete_params` are optional, if they aren't specified then default values are used for everything and a no-argument bare call will be made for any create/update/delete calls
- If you want to call an ABI method for create/update/delete calls then you can pass in a string for `method`, which can either be the method name, or if you need to disambiguate between multiple methods of the same name it can be the ABI signature

```python
# Use no-argument bare-calls to deploy with default behaviour
#  for when update or schema break detected (fail the deployment)
client, response = factory.deploy({})

# Specify parameters for bare-calls and override the schema break behaviour
client, response = factory.deploy(
    create_params=factory.params.bare.create(
        args=[bytes([1, 2, 3, 4])],
        on_complete=OnComplete.OptIn,
    ),
    update_params=factory.params.bare.deploy_update(
        args=[bytes([1, 2, 3])],
    ),
    delete_params=factory.params.bare.deploy_delete(
        args=[bytes([1, 2])],
    ),
    deploy_time_params={
        "ONE": 1,
        "TWO": "two",
    },
    on_update=OnUpdate.UpdateApp,
    on_schema_break=OnSchemaBreak.ReplaceApp,
    updatable=True,
    deletable=True,
)

# Specify parameters for ABI method calls
client, response = factory.deploy(
    create_params=factory.params.create(
        method="create_application",
        args=[1, "something"],
    ),
    update_params=factory.params.deploy_update(
        method="update",
    ),
    delete_params=factory.params.deploy_delete(
        method="delete_app(uint64,uint64,uint64)uint64",
        args=[1, 2, 3],
    ),
)
```

If you want to construct a custom deploy call, you can get params objects for the `create_params`, `update_params` and `delete_params`:

- `factory.params.create(params)` - ABI method create call for deploy method
- `factory.params.deploy_update(params)` - ABI method update call for deploy method
- `factory.params.deploy_delete(params)` - ABI method delete call for deploy method
- `factory.params.bare.create(params)` - Bare create call for deploy method
- `factory.params.bare.deploy_update(params)` - Bare update call for deploy method
- `factory.params.bare.deploy_delete(params)` - Bare delete call for deploy method

## Updating and deleting an app

Deploy method aside, the ability to make update and delete calls happens after there is an instance of an app so are done via `AppClient`. The semantics of this are no different than [other calls](#calling-the-app), with the caveat that the update call is a bit different to the others since the code will be compiled when constructing the update params and the update calls thus optionally takes compilation parameters (`deploy_time_params`, `updatable` and `deletable`) for deploy-time parameter replacements and deploy-time immutability and permanence control.

## Calling the app

You can construct a params object, transaction(s) and sign and send a transaction to call the app that a given `AppClient` instance is pointing to.

This is done via the following properties:

- `client.params.{on_complete}(params)` - Params for an ABI method call
- `client.params.bare.{on_complete}(params)` - Params for a bare call
- `client.create_transaction.{on_complete}(params)` - Transaction(s) for an ABI method call
- `client.create_transaction.bare.{on_complete}(params)` - Transaction for a bare call
- `client.send.{on_complete}(params)` - Sign and send an ABI method call
- `client.send.bare.{on_complete}(params)` - Sign and send a bare call

To make one of these calls `{on_complete}` needs to be swapped with the [on complete action](https://developer.algorand.org/docs/get-details/dapps/smart-contracts/apps/#the-lifecycle-of-a-smart-contract) that should be made:

- `update` - An update call
- `opt_in` - An opt-in call
- `delete` - A delete application call
- `clear_state` - A clear state call (note: calls the clear program and only applies to bare calls)
- `close_out` - A close-out call
- `call` - A no-op call (or other call if `on_complete` is specified to anything other than update)

The input payload for all of these calls is the same as the underlying app methods with the caveat that the `app_id` is not passed in (since the `AppClient` already knows the app ID), `sender` is optional (it uses `default_sender` from the `AppClient` constructor if it was specified) and `method` (for ABI method calls) is a string rather than an `ABIMethod` object (which can either be the method name, or if you need to disambiguate between multiple methods of the same name it can be the ABI signature).

```python
update_call = client.send.update(
    params=client.params.update(
        method="update_abi",
        args=["string_io"],
        deploy_time_params=deploy_time_params,
    )
)
delete_call = client.send.delete(
    params=client.params.delete(
        method="delete_abi",
        args=["string_io"],
    )
)
opt_in_call = client.send.opt_in(
    params=client.params.opt_in(
        method="opt_in"
    )
)
clear_state_call = client.send.bare.clear_state()

transaction = client.create_transaction.bare.close_out(
    params=client.params.bare.close_out(
        args=[bytes([1, 2, 3])],
    )
)

params = client.params.opt_in(method="optin")
```

### Nested ABI Method Call Transactions

The ARC4 ABI specification supports ABI method calls as arguments to other ABI method calls, enabling some interesting use cases. While this conceptually resembles a function call hierarchy, in practice, the transactions are organized as a flat, ordered transaction group. Unfortunately, this logically hierarchical structure cannot always be correctly represented as a flat transaction group, making some scenarios impossible.

To illustrate this, let's consider an example of two ABI methods with the following signatures:

- `myMethod(pay, appl): void`
- `myOtherMethod(pay): void`

These signatures are compatible, so `myOtherMethod` can be passed as an ABI method call argument to `myMethod`, which would look like:

Hierarchical method call

```
myMethod(pay, myOtherMethod(pay))
```

Flat transaction group

```
pay (pay)
appl (myOtherMethod)
appl (myMethod)
```

An important limitation to note is that the flat transaction group representation does not allow having two different pay transactions. This invariant is represented in the hierarchical call interface of the app client by passing `None` for the value. This acts as a placeholder and tells the app client that another ABI method call argument will supply the value for this argument. For example:

```python
payment = client.algorand.create_transaction.payment(
    sender="SENDER_ADDRESS",
    receiver="RECEIVER_ADDRESS",
    amount=1_000_000,  # 1 Algo
)

my_other_method_call = client.params.call(
    method="myOtherMethod",
    args=[payment],
)

my_method_call = client.send.call(
    params=client.params.call(
        method="myMethod",
        args=[None, my_other_method_call],
    )
)
```

`my_other_method_call` supplies the pay transaction to the transaction group and, by association, `my_other_method_call` has access to it as defined in its signature.
To ensure the app client builds the correct transaction group, you must supply a value for every argument in a method call signature.

## Funding the app account

Often there is a need to fund an app account to cover minimum balance requirements for boxes and other scenarios. There is an app client method that will do this for you `fund_app_account(params)`.

The input parameters are:

- A `FundAppParams`, which has the same properties as a payment transaction except `receiver` is not required and `sender` is optional (if not specified then it will be set to the app client's default sender if configured).

Note: If you are passing the funding payment in as an ABI argument so it can be validated by the ABI method then you'll want to get the funding call as a transaction, e.g.:

```python
result = client.send.call(
    params=client.params.call(
        method="bootstrap",
        args=[
            client.create_transaction.fund_app_account(
                params=client.params.fund_app_account(
                    amount=200_000,  # microAlgos
                )
            ),
        ],
        box_references=["Box1"],
    )
)
```

You can also get the funding call as a params object via `client.params.fund_app_account(params)`.

## Reading state

`AppClient` has a number of mechanisms to read state (global, local and box storage) from the app instance.

### App spec methods

The ARC-56 app spec can specify detailed information about the encoding format of state values and as such allows for a more advanced ability to automatically read state values and decode them as their high-level language types rather than the limited `int` / `bytes` / `str` ability that the [generic methods](#generic-methods) give you.

You can access this functionality via:

- `client.state.global_state.{method}()` - Global state
- `client.state.local_state(address).{method}()` - Local state
- `client.state.box.{method}()` - Box storage

Where `{method}` is one of:

- `get_all()` - Returns all single-key state values in a record keyed by the key name and the value a decoded ABI value.
- `get_value(name)` - Returns a single state value for the current app with the value a decoded ABI value.
- `get_map_value(map_name, key)` - Returns a single value from the given map for the current app with the value a decoded ABI value. Key can either be a `bytes` with the binary value of the key value on-chain (without the map prefix) or the high level (decoded) value that will be encoded to bytes for the app spec specified `key_type`
- `get_map(map_name)` - Returns all map values for the given map in a key=>value record. It's recommended that this is only done when you have a unique `prefix` for the map otherwise there's a high risk that incorrect values will be included in the map.

```python
values = client.state.global_state.get_all()
value = client.state.local_state("ADDRESS").get_value("value1")
map_value = client.state.box.get_map_value("map1", "mapKey")
map_values = client.state.global_state.get_map("myMap")
```

### Generic methods

There are various methods defined that let you read state from the smart contract app:

- `get_global_state()` - Gets the current global state
- `get_local_state(address: str)` - Gets the current local state for the given account address
- `get_box_names()` - Gets the current box names
- `get_box_value(name)` - Gets the current value of the given box
- `get_box_value_from_abi_type(name, abi_type)` - Gets the current value of the given box decoded using the specified ABI type
- `get_box_values(filter)` - Gets the current values of the boxes
- `get_box_values_from_abi_type(type, filter)` - Gets the current values of the boxes decoded using the specified ABI type

```python
global_state = client.get_global_state()
local_state = client.get_local_state("ACCOUNT_ADDRESS")

box_name = "my-box"
box_name2 = "my-box2"

box_names = client.get_box_names()
box_value = client.get_box_value(box_name)
box_values = client.get_box_values([box_name, box_name2])
box_abi_value = client.get_box_value_from_abi_type(box_name, algosdk.ABIStringType())
box_abi_values = client.get_box_values_from_abi_type([box_name, box_name2], algosdk.ABIStringType())
```

## Handling logic errors and diagnosing errors

Often when calling a smart contract during development you will get logic errors that cause an exception to throw. This may be because of a failing assertion, a lack of fees, exhaustion of opcode budget, or any number of other reasons.

When this occurs, you will generally get an error that looks something like: `TransactionPool.Remember: transaction {TRANSACTION_ID}: logic eval error: {ERROR_MESSAGE}. Details: pc={PROGRAM_COUNTER_VALUE}, opcodes={LIST_OF_OP_CODES}`.

The information in that error message can be parsed and when combined with the source map from compilation you can expose debugging information that makes it much easier to understand what's happening. The ARC-56 app spec, if provided, can also specify human-readable error messages against certain program counter values and further augment the error message.

The app client and app factory automatically provide this functionality for all smart contract calls. When an error is thrown then the resulting error that is re-thrown will be a `LogicError` object, which has the following fields:

- `logic_error_str: str` - The original error message
- `program: str` - The TEAL program
- `source_map: AlgoSourceMap | None` - The source map if available
- `transaction_id: str` - The transaction ID that triggered the error
- `message: str` - The error message
- `pc: int` - The program counter value
- `traces: list[SimulationTrace] | None` - Any traces that were included in the error
- `line_no: int | None` - The line number in the TEAL program that triggered the error
- `lines: list[str]` - The TEAL program split into lines

Note: This information will only show if the app client / app factory has a source map. This will occur if:

- You have called `create`, `update` or `deploy`
- You have called `import_source_maps(source_maps)` and provided the source maps (which you can get by calling `export_source_maps()` after variously calling `create`, `update`, or `deploy` and it returns a serialisable value)
- You had source maps present in an app factory and then used it to create an app client (they are automatically passed through)

If you want to go a step further and automatically issue a simulated transaction and get trace information when there is an error when an ABI method is called you can turn on debug mode:

```python
from algokit_utils.config import config

config.configure(debug=True)
```

If you do that then the exception will have the `traces` property within the underlying exception will have key information from the simulation within it and this will get populated into the `led.traces` property of the thrown error.

When this debug flag is set, it will also emit debugging symbols to allow break-point debugging of the calls if the project root is also configured.

Example error handling:

```python
from algokit_utils.config import config

# Enable debug mode for detailed error information
config.configure(debug=True)

try:
    client.send.call(
        params=client.params.call(
            method="will_fail",
            args=["test"]
        )
    )
except algokit_utils.LogicError as e:
    print(f"Error at line {e.value.line_no}")  # Access via value property
    print(f"Error message: {e.value.message}")
    print(f"Transaction ID: {e.value.transaction_id}")
    print(e.value.trace())  # Shows TEAL execution trace with source mapping

    if e.value.traces:  # Available when debug mode is active
        for trace in e.value.traces:
            print(f"PC: {trace['pc']}, Stack: {trace['stack']}")
```

## Best Practices

1. Use typed ABI methods when possible for better type safety
2. Always handle potential logic errors with proper error handling
3. Use transaction composition for atomic operations
4. Leverage source maps and debug mode for development
5. Use idempotent deployment patterns with versioning
6. Properly manage box references to avoid transaction failures
7. Use template values for flexible application deployment
8. Implement proper state management with type safety
9. Use the client's parameter builders for type-safe transaction creation
10. Leverage the state accessor patterns for cleaner state management

## Common Patterns

### Idempotent Deployment

```python
# Deploy with idempotency and version tracking
client, response = factory.deploy(
    version="1.0.0",
    deploy_time_params={"TMPL_VALUE": "value"},
    on_update=algokit_utils.OnUpdate.UpdateApp,
    on_schema_break=algokit_utils.OnSchemaBreak.ReplaceApp,
    create_params=factory.params.create(
        method="create",
        args=["initial_value"],
    ),
)

if response.app.app_id != 0:
    print(f"Deployed app ID: {response.app.app_id}")
    if response.operation_performed == algokit_utils.OperationPerformed.Create:
        print("New application deployed")
    else:
        print("Existing application found")
```

### Application State Migration

```python
# Deploy with state migration
client, response = factory.deploy(
    version="2.0.0",
    on_schema_break=algokit_utils.OnSchemaBreak.ReplaceApp,
    on_update=algokit_utils.OnUpdate.UpdateApp,
    create_params=factory.params.create(
        method="create",
        args=["initial_value"],
        schema={
            "global_ints": 1,
            "global_byte_slices": 1,
            "local_ints": 0,
            "local_byte_slices": 0,
        },
    ),
)

if response.operation_performed == algokit_utils.OperationPerformed.Replace:
    # Migrate state from old to new app
    # Note: Migration logic should be implemented in the smart contract
    client.send.call(
        params=client.params.call(
            method="migrate_state",
            args=[response.old_app_id],
        )
    )
```

### Opt-in Management

```python
# Create opt-in parameters
opt_in_params = client.params.opt_in(
    method="initialize",  # Optional: Method to call during opt-in
    args=["initial_value"],  # Optional: Arguments for initialization
    boxes=[("user_data", "ACCOUNT_ADDRESS")],  # Optional: Box allocation
)

# Create and send opt-in transaction
transaction = client.create_transaction.opt_in(opt_in_params)
result = client.send.opt_in(opt_in_params)

# Check if account is opted in
is_opted_in = client.is_opted_in("ACCOUNT_ADDRESS")

# Create close-out parameters
close_out_params = client.params.close_out(
    method="cleanup",  # Optional: Method to call during close-out
    args=["cleanup_value"],  # Optional: Arguments for cleanup
)

# Create and send close-out transaction
transaction = client.create_transaction.close_out(close_out_params)
result = client.send.close_out(close_out_params)
```

## Default arguments

If an ABI method call specifies default argument values for any of its arguments you can pass in `None` for the value of that argument for the default value to be automatically populated.
