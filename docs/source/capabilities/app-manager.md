# App management

App management is a higher-order use case capability provided by AlgoKit Utils that builds on top of the core capabilities. It allows you to create, update, delete, call (ABI and otherwise) smart contract apps and the metadata associated with them (including state and boxes).

## `AppManager`

The `AppManager` is a class that is used to manage app information.

To get an instance of `AppManager` you need to instantiate it with an algod client:

```python
from algokit_utils import AppManager

app_manager = AppManager(algod_client)
```

## Calling apps

### App Clients

The recommended way of interacting with apps is via [Typed app clients](./typed-app-clients.md) or if you can't use a typed app client then an [untyped app client](./app-client.md). The methods shown on this page are the underlying mechanisms that app clients use and are for advanced use cases when you want more control.

### Creation

To create an app you can use the following parameters:

- `sender: str` - The address of the account that will create the app
- `approval_program: bytes | str` - The program to execute for all OnCompletes other than ClearState as raw TEAL that will be compiled (string) or compiled TEAL (encoded as bytes)
- `clear_state_program: bytes | str` - The program to execute for ClearState OnComplete as raw TEAL that will be compiled (string) or compiled TEAL (encoded as bytes)
- `schema: dict | None` - The storage schema to request for the created app. This is immutable once the app is created. It is a dictionary with:
  - `global_ints: int` - The number of integers saved in global state
  - `global_byte_slices: int` - The number of byte slices saved in global state
  - `local_ints: int` - The number of integers saved in local state
  - `local_byte_slices: int` - The number of byte slices saved in local state
- `extra_program_pages: int | None` - Number of extra pages required for the programs. This is immutable once the app is created.

If you pass in `approval_program` or `clear_state_program` as a string then it will automatically be compiled using Algod and the compilation result will be available via `app_manager.get_compilation_result` (including the source map). To skip this behaviour you can pass in the compiled TEAL as bytes.

### Updating

To update an app you can use the following parameters:

- `sender: str` - The address of the account that will update the app
- `app_id: int` - The ID of the app to update
- `approval_program: bytes | str` - The new program to execute for all OnCompletes other than ClearState
- `clear_state_program: bytes | str` - The new program to execute for ClearState OnComplete

### Deleting

To delete an app you can use the following parameters:

- `sender: str` - The address of the account that will delete the app
- `app_id: int` - The ID of the app to delete

### Calling

To call an app you can use the following parameters:

- `sender: str` - The address of the account that will call the app
- `app_id: int` - The ID of the app to call
- `on_complete: OnComplete | None` - The on-completion action to specify for the call
- `args: list[bytes | str] | None` - Any arguments to pass to the smart contract call
- `accounts: list[str] | None` - Any account addresses to add to the accounts array
- `foreign_apps: list[int] | None` - The ID of any apps to load to the foreign apps array
- `foreign_assets: list[int] | None` - The ID of any assets to load to the foreign assets array
- `boxes: list[BoxReference | BoxIdentifier] | None` - Any boxes to load to the boxes array

### ABI Return Values

The `AppManager` provides a static method to parse ABI return values from transaction confirmations:

```python
abi_return = AppManager.get_abi_return(confirmation, abi_method)
if abi_return:
    raw_return_value = abi_return.raw_return_value
    return_value = abi_return.return_value
```

## Accessing state

### Global state

To access global state you can use the following method from an `AppManager` instance:

- `app_manager.get_global_state(app_id)` - Returns the current global state for the given app ID decoded into a dictionary keyed by the UTF-8 representation of the state key with various parsed versions of the value (base64, UTF-8 and raw binary)

```python
global_state = app_manager.get_global_state(12345)
```

Global state is parsed from the underlying algod response via the following static method from `AppManager`:

- `AppManager.decode_app_state(state)` - Takes the raw response from the algod API for global state and returns a friendly dictionary keyed by the UTF-8 value of the key

```python
app_state = AppManager.decode_app_state(global_app_state)

key_as_binary = app_state['value1'].key_raw
key_as_base64 = app_state['value1'].key_base64
if isinstance(app_state['value1'].value, str):
    value_as_string = app_state['value1'].value
    value_as_binary = app_state['value1'].value_raw
    value_as_base64 = app_state['value1'].value_base64
else:
    value_as_number = app_state['value1'].value
```

### Local state

To access local state you can use the following method from an `AppManager` instance:

- `app_manager.get_local_state(app_id, address)` - Returns the current local state for the given app ID and account address decoded into a dictionary keyed by the UTF-8 representation of the state key with various parsed versions of the value (base64, UTF-8 and raw binary)

```python
local_state = app_manager.get_local_state(12345, 'ACCOUNTADDRESS')
```

### Boxes

To access and parse box values and names for an app you can use the following methods from an `AppManager` instance:

- `app_manager.get_box_names(app_id)` - Returns the current box names for the given app ID
- `app_manager.get_box_value(app_id, box_name)` - Returns the binary value of the given box name for the given app ID
- `app_manager.get_box_values(app_id, box_names)` - Returns the binary values of the given box names for the given app ID
- `app_manager.get_box_value_from_abi_type(app_id, box_name, abi_type)` - Returns the parsed ABI value of the given box name for the given app ID for the provided ABI type
- `app_manager.get_box_values_from_abi_type(app_id, box_names, abi_type)` - Returns the parsed ABI values of the given box names for the given app ID for the provided ABI type
- `AppManager.get_box_reference(box_id)` - Returns a tuple of `(app_id, name_bytes)` representation of the given box identifier/reference

```python
app_id = 12345
box_name = 'my-box'
box_name2 = 'my-box2'

box_names = app_manager.get_box_names(app_id)
box_value = app_manager.get_box_value(app_id, box_name)
box_values = app_manager.get_box_values(app_id, [box_name, box_name2])
box_abi_value = app_manager.get_box_value_from_abi_type(app_id, box_name, algosdk.abi.StringType())
box_abi_values = app_manager.get_box_values_from_abi_type(app_id, [box_name, box_name2], algosdk.abi.StringType())
```

## Getting app information

To get reference information and metadata about an existing app you can use:

- `app_manager.get_by_id(app_id)` - Returns current app information by app ID including approval program, clear state program, creator, schemas, and global state

## Common app parameters

When interacting with apps (creating, updating, deleting, calling), there are some common parameters that you will be able to pass in to all calls:

- `app_id: int` - ID of the application; only specified if the application is not being created
- `on_complete: OnComplete | None` - The on-complete action of the call
- `args: list[bytes | str] | None` - Any arguments to pass to the smart contract call
- `accounts: list[str] | None` - Any account addresses to add to the accounts array
- `foreign_apps: list[int] | None` - The ID of any apps to load to the foreign apps array
- `foreign_assets: list[int] | None` - The ID of any assets to load to the foreign assets array
- `boxes: list[BoxReference | BoxIdentifier] | None` - Any boxes to load to the boxes array

When making an ABI call, the `args` parameter is replaced with ABI-specific arguments and there is also a `method` parameter:

- `method: ABIMethod`
- `args: list[ABIArgument]` - The arguments to pass to the ABI call, which can be one of:
  - `ABIValue` - Which can be one of:
    - `bool`
    - `int`
    - `str`
    - `bytes`
    - A list of one of the above types
  - `Transaction`
  - `TransactionWithSigner`

## Box references

A box can be referenced by either a `BoxIdentifier` (which identifies the name of the box and app ID `0` will be used - i.e. the current app) or `BoxReference`:

```python
# BoxIdentifier can be:
#  * bytes (the actual binary of the box name)
#  * str (that will be encoded to bytes)
#  * AccountTransactionSigner (that will be encoded into the public key address)
BoxIdentifier = str | bytes | AccountTransactionSigner

# BoxReference is a class with:
#  * app_id: int - A unique application id
#  * name: BoxIdentifier - Identifier for a box name
BoxReference = BoxReference
```

## Compilation

The `AppManager` class allows you to compile TEAL code with caching semantics that allows you to avoid duplicate compilation and keep track of source maps from compiled code.

If you call `app_manager.compile_teal(teal_code)` then the compilation result will be stored and retrievable from `app_manager.get_compilation_result(teal_code)`.

```python
teal_code = 'return 1'
compilation_result = app_manager.compile_teal(teal_code)
# ...
previous_compilation_result = app_manager.get_compilation_result(teal_code)
```

### Template compilation

The `AppManager` also supports compiling TEAL templates with variables and deployment metadata:

```python
compilation_result = app_manager.compile_teal_template(
    teal_template_code,
    template_params={"VAR1": "value1"},
    deployment_metadata={"updatable": True, "deletable": True}
)
```
