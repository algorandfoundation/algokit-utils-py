# algokit_utils.applications.app_client

## Attributes

| [`CreateOnComplete`](#algokit_utils.applications.app_client.CreateOnComplete)   |    |
|---------------------------------------------------------------------------------|----|

## Classes

| [`AppClientCompilationResult`](#algokit_utils.applications.app_client.AppClientCompilationResult)           | Result of compiling an application's TEAL code.                       |
|-------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| [`AppClientCompilationParams`](#algokit_utils.applications.app_client.AppClientCompilationParams)           | Parameters for compiling an application's TEAL code.                  |
| [`FundAppAccountParams`](#algokit_utils.applications.app_client.FundAppAccountParams)                       | Parameters for funding an application's account.                      |
| [`AppClientCallParams`](#algokit_utils.applications.app_client.AppClientCallParams)                         | Parameters for calling an application.                                |
| [`BaseAppClientMethodCallParams`](#algokit_utils.applications.app_client.BaseAppClientMethodCallParams)     | Base parameters for application method calls.                         |
| [`AppClientMethodCallParams`](#algokit_utils.applications.app_client.AppClientMethodCallParams)             | Parameters for application method calls.                              |
| [`AppClientBareCallParams`](#algokit_utils.applications.app_client.AppClientBareCallParams)                 | Parameters for bare application calls.                                |
| [`AppClientCreateSchema`](#algokit_utils.applications.app_client.AppClientCreateSchema)                     | Schema for application creation.                                      |
| [`AppClientBareCallCreateParams`](#algokit_utils.applications.app_client.AppClientBareCallCreateParams)     | Parameters for creating application with bare call.                   |
| [`AppClientMethodCallCreateParams`](#algokit_utils.applications.app_client.AppClientMethodCallCreateParams) | Parameters for creating application with method call.                 |
| [`AppClientParams`](#algokit_utils.applications.app_client.AppClientParams)                                 | Full parameters for creating an app client                            |
| [`AppClient`](#algokit_utils.applications.app_client.AppClient)                                             | A client for interacting with an Algorand smart contract application. |

## Functions

| [`get_constant_block_offset`](#algokit_utils.applications.app_client.get_constant_block_offset)(→ int)   | Calculate the offset after constant blocks in TEAL program.   |
|----------------------------------------------------------------------------------------------------------|---------------------------------------------------------------|

## Module Contents

### algokit_utils.applications.app_client.get_constant_block_offset(program: bytes) → int

Calculate the offset after constant blocks in TEAL program.

Analyzes a compiled TEAL program to find the ending offset position after any bytecblock and intcblock operations.

* **Parameters:**
  **program** – The compiled TEAL program as bytes
* **Returns:**
  The maximum offset position after any constant block operations

### algokit_utils.applications.app_client.CreateOnComplete

### *class* algokit_utils.applications.app_client.AppClientCompilationResult

Result of compiling an application’s TEAL code.

Contains the compiled approval and clear state programs along with optional compilation artifacts.

* **Variables:**
  * **approval_program** – The compiled approval program bytes
  * **clear_state_program** – The compiled clear state program bytes
  * **compiled_approval** – Optional compilation artifacts for approval program
  * **compiled_clear** – Optional compilation artifacts for clear state program

#### approval_program *: bytes*

#### clear_state_program *: bytes*

#### compiled_approval *: [algokit_utils.models.application.CompiledTeal](../../models/application/index.md#algokit_utils.models.application.CompiledTeal) | None* *= None*

#### compiled_clear *: [algokit_utils.models.application.CompiledTeal](../../models/application/index.md#algokit_utils.models.application.CompiledTeal) | None* *= None*

### *class* algokit_utils.applications.app_client.AppClientCompilationParams

Bases: `TypedDict`

Parameters for compiling an application’s TEAL code.

* **Variables:**
  * **deploy_time_params** – Optional template parameters to use during compilation
  * **updatable** – Optional flag indicating if app should be updatable
  * **deletable** – Optional flag indicating if app should be deletable

#### deploy_time_params *: algokit_utils.models.state.TealTemplateParams | None*

#### updatable *: bool | None*

#### deletable *: bool | None*

### *class* algokit_utils.applications.app_client.FundAppAccountParams

Parameters for funding an application’s account.

* **Variables:**
  * **sender** – Optional sender address
  * **signer** – Optional transaction signer
  * **rekey_to** – Optional address to rekey to
  * **note** – Optional transaction note
  * **lease** – Optional lease
  * **static_fee** – Optional static fee
  * **extra_fee** – Optional extra fee
  * **max_fee** – Optional maximum fee
  * **validity_window** – Optional validity window in rounds
  * **first_valid_round** – Optional first valid round
  * **last_valid_round** – Optional last valid round
  * **amount** – Amount to fund
  * **close_remainder_to** – Optional address to close remainder to
  * **on_complete** – Optional on complete action

#### sender *: str | None* *= None*

#### signer *: algosdk.atomic_transaction_composer.TransactionSigner | None* *= None*

#### rekey_to *: str | None* *= None*

#### note *: bytes | None* *= None*

#### lease *: bytes | None* *= None*

#### static_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### extra_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### max_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### validity_window *: int | None* *= None*

#### first_valid_round *: int | None* *= None*

#### last_valid_round *: int | None* *= None*

#### amount *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount)*

#### close_remainder_to *: str | None* *= None*

#### on_complete *: algosdk.transaction.OnComplete | None* *= None*

### *class* algokit_utils.applications.app_client.AppClientCallParams

Parameters for calling an application.

* **Variables:**
  * **method** – Optional ABI method name or signature
  * **args** – Optional arguments to pass to method
  * **boxes** – Optional box references to load
  * **accounts** – Optional account addresses to load
  * **apps** – Optional app IDs to load
  * **assets** – Optional asset IDs to load
  * **lease** – Optional lease
  * **sender** – Optional sender address
  * **note** – Optional transaction note
  * **send_params** – Optional parameters to control transaction sending

#### method *: str | None* *= None*

#### args *: list | None* *= None*

#### boxes *: list | None* *= None*

#### accounts *: list[str] | None* *= None*

#### apps *: list[int] | None* *= None*

#### assets *: list[int] | None* *= None*

#### lease *: str | bytes | None* *= None*

#### sender *: str | None* *= None*

#### note *: bytes | dict | str | None* *= None*

#### send_params *: dict | None* *= None*

### *class* algokit_utils.applications.app_client.BaseAppClientMethodCallParams

Bases: `Generic`[`ArgsT`, `MethodT`]

Base parameters for application method calls.

* **Variables:**
  * **method** – Method to call
  * **args** – Optional arguments to pass to method
  * **account_references** – Optional account references
  * **app_references** – Optional application references
  * **asset_references** – Optional asset references
  * **box_references** – Optional box references
  * **extra_fee** – Optional extra fee
  * **first_valid_round** – Optional first valid round
  * **lease** – Optional lease
  * **max_fee** – Optional maximum fee
  * **note** – Optional note
  * **rekey_to** – Optional rekey to address
  * **sender** – Optional sender address
  * **signer** – Optional transaction signer
  * **static_fee** – Optional static fee
  * **validity_window** – Optional validity window
  * **last_valid_round** – Optional last valid round
  * **on_complete** – Optional on complete action

#### method *: MethodT*

#### args *: ArgsT | None* *= None*

#### account_references *: list[str] | None* *= None*

#### app_references *: list[int] | None* *= None*

#### asset_references *: list[int] | None* *= None*

#### box_references *: collections.abc.Sequence[[algokit_utils.models.state.BoxReference](../../models/state/index.md#algokit_utils.models.state.BoxReference) | algokit_utils.models.state.BoxIdentifier] | None* *= None*

#### extra_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### first_valid_round *: int | None* *= None*

#### lease *: bytes | None* *= None*

#### max_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### note *: bytes | None* *= None*

#### rekey_to *: str | None* *= None*

#### sender *: str | None* *= None*

#### signer *: algosdk.atomic_transaction_composer.TransactionSigner | None* *= None*

#### static_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### validity_window *: int | None* *= None*

#### last_valid_round *: int | None* *= None*

#### on_complete *: algosdk.transaction.OnComplete | None* *= None*

### *class* algokit_utils.applications.app_client.AppClientMethodCallParams

Bases: [`BaseAppClientMethodCallParams`](#algokit_utils.applications.app_client.BaseAppClientMethodCallParams)[`collections.abc.Sequence`[`algokit_utils.applications.abi.ABIValue | algokit_utils.applications.abi.ABIStruct | algokit_utils.transactions.transaction_composer.AppMethodCallTransactionArgument | None`], `str`]

Parameters for application method calls.

### *class* algokit_utils.applications.app_client.AppClientBareCallParams

Parameters for bare application calls.

* **Variables:**
  * **signer** – Optional transaction signer
  * **rekey_to** – Optional rekey to address
  * **lease** – Optional lease
  * **static_fee** – Optional static fee
  * **extra_fee** – Optional extra fee
  * **max_fee** – Optional maximum fee
  * **validity_window** – Optional validity window
  * **first_valid_round** – Optional first valid round
  * **last_valid_round** – Optional last valid round
  * **sender** – Optional sender address
  * **note** – Optional note
  * **args** – Optional arguments
  * **account_references** – Optional account references
  * **app_references** – Optional application references
  * **asset_references** – Optional asset references
  * **box_references** – Optional box references

#### signer *: algosdk.atomic_transaction_composer.TransactionSigner | None* *= None*

#### rekey_to *: str | None* *= None*

#### lease *: bytes | None* *= None*

#### static_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### extra_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### max_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### validity_window *: int | None* *= None*

#### first_valid_round *: int | None* *= None*

#### last_valid_round *: int | None* *= None*

#### sender *: str | None* *= None*

#### note *: bytes | None* *= None*

#### args *: list[bytes] | None* *= None*

#### account_references *: list[str] | None* *= None*

#### app_references *: list[int] | None* *= None*

#### asset_references *: list[int] | None* *= None*

#### box_references *: list[[algokit_utils.models.state.BoxReference](../../models/state/index.md#algokit_utils.models.state.BoxReference) | algokit_utils.models.state.BoxIdentifier] | None* *= None*

### *class* algokit_utils.applications.app_client.AppClientCreateSchema

Schema for application creation.

* **Variables:**
  * **extra_program_pages** – Optional number of extra program pages
  * **schema** – Optional application creation schema

#### extra_program_pages *: int | None* *= None*

#### schema *: [algokit_utils.transactions.transaction_composer.AppCreateSchema](../../transactions/transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppCreateSchema) | None* *= None*

### *class* algokit_utils.applications.app_client.AppClientBareCallCreateParams

Bases: [`AppClientCreateSchema`](#algokit_utils.applications.app_client.AppClientCreateSchema), [`AppClientBareCallParams`](#algokit_utils.applications.app_client.AppClientBareCallParams)

Parameters for creating application with bare call.

#### on_complete *: algosdk.transaction.OnComplete | None* *= None*

### *class* algokit_utils.applications.app_client.AppClientMethodCallCreateParams

Bases: [`AppClientCreateSchema`](#algokit_utils.applications.app_client.AppClientCreateSchema), [`AppClientMethodCallParams`](#algokit_utils.applications.app_client.AppClientMethodCallParams)

Parameters for creating application with method call.

#### on_complete *: CreateOnComplete | None* *= None*

### *class* algokit_utils.applications.app_client.AppClientParams

Full parameters for creating an app client

#### app_spec *: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract) | [algokit_utils.applications.app_spec.arc32.Arc32Contract](../app_spec/arc32/index.md#algokit_utils.applications.app_spec.arc32.Arc32Contract) | str*

#### algorand *: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient)*

#### app_id *: int*

#### app_name *: str | None* *= None*

#### default_sender *: str | None* *= None*

#### default_signer *: algosdk.atomic_transaction_composer.TransactionSigner | None* *= None*

#### approval_source_map *: algosdk.source_map.SourceMap | None* *= None*

#### clear_source_map *: algosdk.source_map.SourceMap | None* *= None*

### *class* algokit_utils.applications.app_client.AppClient(params: [AppClientParams](#algokit_utils.applications.app_client.AppClientParams))

A client for interacting with an Algorand smart contract application.

Provides a high-level interface for interacting with Algorand smart contracts, including
methods for calling application methods, managing state, and handling transactions.

* **Parameters:**
  **params** – Parameters for creating the app client

#### *property* algorand *: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient)*

Get the Algorand client instance.

* **Returns:**
  The Algorand client used by this app client

#### *property* app_id *: int*

Get the application ID.

* **Returns:**
  The ID of the Algorand application

#### *property* app_address *: str*

Get the application’s Algorand address.

* **Returns:**
  The Algorand address associated with this application

#### *property* app_name *: str*

Get the application name.

* **Returns:**
  The name of the application

#### *property* app_spec *: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract)*

Get the application specification.

* **Returns:**
  The ARC-56 contract specification for this application

#### *property* state *: \_StateAccessor*

Get the state accessor.

* **Returns:**
  The state accessor for this application

#### *property* params *: \_MethodParamsBuilder*

Get the method parameters builder.

* **Returns:**
  The method parameters builder for this application

#### *property* send *: \_TransactionSender*

Get the transaction sender.

* **Returns:**
  The transaction sender for this application

#### *property* create_transaction *: \_TransactionCreator*

Get the transaction creator.

* **Returns:**
  The transaction creator for this application

#### *static* normalise_app_spec(app_spec: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract) | [algokit_utils.applications.app_spec.arc32.Arc32Contract](../app_spec/arc32/index.md#algokit_utils.applications.app_spec.arc32.Arc32Contract) | str) → [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract)

Normalize an application specification to ARC-56 format.

* **Parameters:**
  **app_spec** – The application specification to normalize
* **Returns:**
  The normalized ARC-56 contract specification
* **Raises:**
  **ValueError** – If the app spec format is invalid

#### *static* from_network(app_spec: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract) | [algokit_utils.applications.app_spec.arc32.Arc32Contract](../app_spec/arc32/index.md#algokit_utils.applications.app_spec.arc32.Arc32Contract) | str, algorand: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient), app_name: str | None = None, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, approval_source_map: algosdk.source_map.SourceMap | None = None, clear_source_map: algosdk.source_map.SourceMap | None = None) → [AppClient](#algokit_utils.applications.app_client.AppClient)

Create an AppClient instance from network information.

* **Parameters:**
  * **app_spec** – The application specification
  * **algorand** – The Algorand client instance
  * **app_name** – Optional application name
  * **default_sender** – Optional default sender address
  * **default_signer** – Optional default transaction signer
  * **approval_source_map** – Optional approval program source map
  * **clear_source_map** – Optional clear program source map
* **Returns:**
  A new AppClient instance
* **Raises:**
  **Exception** – If no app ID is found for the network

#### *static* from_creator_and_name(creator_address: str, app_name: str, app_spec: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract) | [algokit_utils.applications.app_spec.arc32.Arc32Contract](../app_spec/arc32/index.md#algokit_utils.applications.app_spec.arc32.Arc32Contract) | str, algorand: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient), default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, approval_source_map: algosdk.source_map.SourceMap | None = None, clear_source_map: algosdk.source_map.SourceMap | None = None, ignore_cache: bool | None = None, app_lookup_cache: [algokit_utils.applications.app_deployer.ApplicationLookup](../app_deployer/index.md#algokit_utils.applications.app_deployer.ApplicationLookup) | None = None) → [AppClient](#algokit_utils.applications.app_client.AppClient)

Create an AppClient instance from creator address and application name.

* **Parameters:**
  * **creator_address** – The address of the application creator
  * **app_name** – The name of the application
  * **app_spec** – The application specification
  * **algorand** – The Algorand client instance
  * **default_sender** – Optional default sender address
  * **default_signer** – Optional default transaction signer
  * **approval_source_map** – Optional approval program source map
  * **clear_source_map** – Optional clear program source map
  * **ignore_cache** – Optional flag to ignore cache
  * **app_lookup_cache** – Optional app lookup cache
* **Returns:**
  A new AppClient instance
* **Raises:**
  **ValueError** – If the app is not found for the creator and name

#### *static* compile(app_spec: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract), app_manager: [algokit_utils.applications.app_manager.AppManager](../app_manager/index.md#algokit_utils.applications.app_manager.AppManager), compilation_params: [AppClientCompilationParams](#algokit_utils.applications.app_client.AppClientCompilationParams) | None = None) → [AppClientCompilationResult](#algokit_utils.applications.app_client.AppClientCompilationResult)

Compile the application’s TEAL code.

* **Parameters:**
  * **app_spec** – The application specification
  * **app_manager** – The application manager instance
  * **compilation_params** – Optional compilation parameters
* **Returns:**
  The compilation result
* **Raises:**
  **ValueError** – If attempting to compile without source or byte code

#### compile_app(compilation_params: [AppClientCompilationParams](#algokit_utils.applications.app_client.AppClientCompilationParams) | None = None) → [AppClientCompilationResult](#algokit_utils.applications.app_client.AppClientCompilationResult)

Compile the application’s TEAL code.

* **Parameters:**
  **compilation_params** – Optional compilation parameters
* **Returns:**
  The compilation result

#### clone(app_name: str | None = \_MISSING, default_sender: str | None = \_MISSING, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = \_MISSING, approval_source_map: algosdk.source_map.SourceMap | None = \_MISSING, clear_source_map: algosdk.source_map.SourceMap | None = \_MISSING) → [AppClient](#algokit_utils.applications.app_client.AppClient)

Create a cloned AppClient instance with optionally overridden parameters.

* **Parameters:**
  * **app_name** – Optional new application name
  * **default_sender** – Optional new default sender
  * **default_signer** – Optional new default signer
  * **approval_source_map** – Optional new approval source map
  * **clear_source_map** – Optional new clear source map
* **Returns:**
  A new AppClient instance with the specified parameters

#### export_source_maps() → [algokit_utils.models.application.AppSourceMaps](../../models/application/index.md#algokit_utils.models.application.AppSourceMaps)

Export the application’s source maps.

* **Returns:**
  The application’s source maps
* **Raises:**
  **ValueError** – If source maps haven’t been loaded

#### import_source_maps(source_maps: [algokit_utils.models.application.AppSourceMaps](../../models/application/index.md#algokit_utils.models.application.AppSourceMaps)) → None

Import source maps for the application.

* **Parameters:**
  **source_maps** – The source maps to import
* **Raises:**
  **ValueError** – If source maps are invalid or missing

#### get_local_state(address: str) → dict[str, [algokit_utils.models.application.AppState](../../models/application/index.md#algokit_utils.models.application.AppState)]

Get local state for an account.

* **Parameters:**
  **address** – The account address
* **Returns:**
  The account’s local state for this application

#### get_global_state() → dict[str, [algokit_utils.models.application.AppState](../../models/application/index.md#algokit_utils.models.application.AppState)]

Get the application’s global state.

* **Returns:**
  The application’s global state

#### get_box_names() → list[[algokit_utils.models.state.BoxName](../../models/state/index.md#algokit_utils.models.state.BoxName)]

Get all box names for the application.

* **Returns:**
  List of box names

#### get_box_value(name: algokit_utils.models.state.BoxIdentifier) → bytes

Get the value of a box.

* **Parameters:**
  **name** – The box identifier
* **Returns:**
  The box value as bytes

#### get_box_value_from_abi_type(name: algokit_utils.models.state.BoxIdentifier, abi_type: algokit_utils.applications.abi.ABIType) → algokit_utils.applications.abi.ABIValue

Get a box value decoded according to an ABI type.

* **Parameters:**
  * **name** – The box identifier
  * **abi_type** – The ABI type to decode as
* **Returns:**
  The decoded box value

#### get_box_values(filter_func: collections.abc.Callable[[[algokit_utils.models.state.BoxName](../../models/state/index.md#algokit_utils.models.state.BoxName)], bool] | None = None) → list[[algokit_utils.models.state.BoxValue](../../models/state/index.md#algokit_utils.models.state.BoxValue)]

Get values for multiple boxes.

* **Parameters:**
  **filter_func** – Optional function to filter box names
* **Returns:**
  List of box values

#### get_box_values_from_abi_type(abi_type: algokit_utils.applications.abi.ABIType, filter_func: collections.abc.Callable[[[algokit_utils.models.state.BoxName](../../models/state/index.md#algokit_utils.models.state.BoxName)], bool] | None = None) → list[[algokit_utils.applications.abi.BoxABIValue](../abi/index.md#algokit_utils.applications.abi.BoxABIValue)]

Get multiple box values decoded according to an ABI type.

* **Parameters:**
  * **abi_type** – The ABI type to decode as
  * **filter_func** – Optional function to filter box names
* **Returns:**
  List of decoded box values

#### fund_app_account(params: [FundAppAccountParams](#algokit_utils.applications.app_client.FundAppAccountParams), send_params: [algokit_utils.models.transaction.SendParams](../../models/transaction/index.md#algokit_utils.models.transaction.SendParams) | None = None) → [algokit_utils.transactions.transaction_sender.SendSingleTransactionResult](../../transactions/transaction_sender/index.md#algokit_utils.transactions.transaction_sender.SendSingleTransactionResult)

Fund the application’s account.

* **Parameters:**
  * **params** – The funding parameters
  * **send_params** – Send parameters, defaults to None
* **Returns:**
  The transaction result
