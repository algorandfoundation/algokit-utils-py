# algokit_utils.applications.app_factory

## Classes

| [`AppFactoryParams`](#algokit_utils.applications.app_factory.AppFactoryParams)                                           |                                                                            |
|--------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| [`AppFactoryCreateParams`](#algokit_utils.applications.app_factory.AppFactoryCreateParams)                               | Parameters for creating application with bare call.                        |
| [`AppFactoryCreateMethodCallParams`](#algokit_utils.applications.app_factory.AppFactoryCreateMethodCallParams)           | Parameters for creating application with method call                       |
| [`AppFactoryCreateMethodCallResult`](#algokit_utils.applications.app_factory.AppFactoryCreateMethodCallResult)           | Base class for transaction results.                                        |
| [`SendAppFactoryTransactionResult`](#algokit_utils.applications.app_factory.SendAppFactoryTransactionResult)             | Result of an application transaction.                                      |
| [`SendAppUpdateFactoryTransactionResult`](#algokit_utils.applications.app_factory.SendAppUpdateFactoryTransactionResult) | Result of updating an application.                                         |
| [`SendAppCreateFactoryTransactionResult`](#algokit_utils.applications.app_factory.SendAppCreateFactoryTransactionResult) | Result of creating a new application.                                      |
| [`AppFactoryDeployResult`](#algokit_utils.applications.app_factory.AppFactoryDeployResult)                               | Result from deploying an application via AppFactory                        |
| [`AppFactory`](#algokit_utils.applications.app_factory.AppFactory)                                                       | ARC-56/ARC-32 app factory that, for a given app spec, allows you to create |

## Module Contents

### *class* algokit_utils.applications.app_factory.AppFactoryParams

#### algorand *: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient)*

#### app_spec *: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract) | algokit_utils._legacy_v2.application_specification.ApplicationSpecification | str*

#### app_name *: str | None* *= None*

#### default_sender *: str | None* *= None*

#### default_signer *: algosdk.atomic_transaction_composer.TransactionSigner | None* *= None*

#### version *: str | None* *= None*

#### compilation_params *: [algokit_utils.applications.app_client.AppClientCompilationParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientCompilationParams) | None* *= None*

### *class* algokit_utils.applications.app_factory.AppFactoryCreateParams

Bases: [`algokit_utils.applications.app_client.AppClientBareCallCreateParams`](../app_client/index.md#algokit_utils.applications.app_client.AppClientBareCallCreateParams)

Parameters for creating application with bare call.

#### on_complete *: algokit_utils.applications.app_client.CreateOnComplete | None* *= None*

Optional on complete action

### *class* algokit_utils.applications.app_factory.AppFactoryCreateMethodCallParams

Bases: [`algokit_utils.applications.app_client.AppClientMethodCallCreateParams`](../app_client/index.md#algokit_utils.applications.app_client.AppClientMethodCallCreateParams)

Parameters for creating application with method call

### *class* algokit_utils.applications.app_factory.AppFactoryCreateMethodCallResult

Bases: [`algokit_utils.transactions.transaction_sender.SendSingleTransactionResult`](../../transactions/transaction_sender/index.md#algokit_utils.transactions.transaction_sender.SendSingleTransactionResult), `Generic`[`ABIReturnT`]

Base class for transaction results.

Represents the result of sending a single transaction.

#### app_id *: int*

#### app_address *: str*

#### compiled_approval *: Any | None* *= None*

#### compiled_clear *: Any | None* *= None*

#### abi_return *: ABIReturnT | None* *= None*

### *class* algokit_utils.applications.app_factory.SendAppFactoryTransactionResult

Bases: [`algokit_utils.transactions.transaction_sender.SendAppTransactionResult`](../../transactions/transaction_sender/index.md#algokit_utils.transactions.transaction_sender.SendAppTransactionResult)[[`algokit_utils.applications.abi.Arc56ReturnValueType`](../abi/index.md#algokit_utils.applications.abi.Arc56ReturnValueType)]

Result of an application transaction.

Contains the ABI return value if applicable.

### *class* algokit_utils.applications.app_factory.SendAppUpdateFactoryTransactionResult

Bases: [`algokit_utils.transactions.transaction_sender.SendAppUpdateTransactionResult`](../../transactions/transaction_sender/index.md#algokit_utils.transactions.transaction_sender.SendAppUpdateTransactionResult)[[`algokit_utils.applications.abi.Arc56ReturnValueType`](../abi/index.md#algokit_utils.applications.abi.Arc56ReturnValueType)]

Result of updating an application.

Contains the compiled approval and clear programs.

### *class* algokit_utils.applications.app_factory.SendAppCreateFactoryTransactionResult

Bases: [`algokit_utils.transactions.transaction_sender.SendAppCreateTransactionResult`](../../transactions/transaction_sender/index.md#algokit_utils.transactions.transaction_sender.SendAppCreateTransactionResult)[[`algokit_utils.applications.abi.Arc56ReturnValueType`](../abi/index.md#algokit_utils.applications.abi.Arc56ReturnValueType)]

Result of creating a new application.

Contains the app ID and address of the newly created application.

### *class* algokit_utils.applications.app_factory.AppFactoryDeployResult

Result from deploying an application via AppFactory

#### app *: [algokit_utils.applications.app_deployer.ApplicationMetaData](../app_deployer/index.md#algokit_utils.applications.app_deployer.ApplicationMetaData)*

The application metadata

#### operation_performed *: algokit_utils.applications.app_deployer.OperationPerformed*

The operation performed

#### create_result *: [SendAppCreateFactoryTransactionResult](#algokit_utils.applications.app_factory.SendAppCreateFactoryTransactionResult) | None* *= None*

The create result

#### update_result *: [SendAppUpdateFactoryTransactionResult](#algokit_utils.applications.app_factory.SendAppUpdateFactoryTransactionResult) | None* *= None*

The update result

#### delete_result *: [SendAppFactoryTransactionResult](#algokit_utils.applications.app_factory.SendAppFactoryTransactionResult) | None* *= None*

The delete result

#### *classmethod* from_deploy_result(response: [algokit_utils.applications.app_deployer.AppDeployResult](../app_deployer/index.md#algokit_utils.applications.app_deployer.AppDeployResult), deploy_params: [algokit_utils.applications.app_deployer.AppDeployParams](../app_deployer/index.md#algokit_utils.applications.app_deployer.AppDeployParams), app_spec: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract), app_compilation_data: [algokit_utils.applications.app_client.AppClientCompilationResult](../app_client/index.md#algokit_utils.applications.app_client.AppClientCompilationResult) | None = None) → typing_extensions.Self

Construct an AppFactoryDeployResult from a deployment result.

* **Parameters:**
  * **response** – The deployment response.
  * **deploy_params** – The deployment parameters.
  * **app_spec** – The application specification.
  * **app_compilation_data** – Optional app compilation data.
* **Returns:**
  An instance of AppFactoryDeployResult.

### *class* algokit_utils.applications.app_factory.AppFactory(params: [AppFactoryParams](#algokit_utils.applications.app_factory.AppFactoryParams))

ARC-56/ARC-32 app factory that, for a given app spec, allows you to create
and deploy one or more app instances and to create one or more app clients
to interact with those (or other) app instances.

* **Parameters:**
  **params** – The parameters for the factory
* **Example:**
  ```pycon
  >>> factory = AppFactory(AppFactoryParams(
  >>>        algorand=AlgorandClient.mainnet(),
  >>>        app_spec=app_spec,
  >>>    )
  >>> )
  ```

#### *property* app_name *: str*

The name of the app

#### *property* app_spec *: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract)*

The app spec

#### *property* algorand *: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient)*

The algorand client

#### *property* params *: \_MethodParamsBuilder*

Get parameters to create transactions (create and deploy related calls) for the current app.

A good mental model for this is that these parameters represent a deferred transaction creation.

* **Example:**
  Create a transaction in the future using Algorand Client
  >>> create_app_params = app_factory.params.create(
  …     AppFactoryCreateMethodCallParams(
  …         method=’create_method’,
  …         args=[123, ‘hello’]
  …     )
  … )
  >>> # …
  >>> algorand.send.app_create_method_call(create_app_params)
* **Example:**
  Define a nested transaction as an ABI argument
  >>> create_app_params = appFactory.params.create(
  …     AppFactoryCreateMethodCallParams(
  …         method=’create_method’,
  …         args=[123, ‘hello’]
  …     )
  … )
  >>> app_client.send.call(
  …     AppClientMethodCallParams(
  …         method=’my_method’,
  …         args=[create_app_params]
  …     )
  … )

#### *property* send *: \_TransactionSender*

Get the transaction sender.

* **Returns:**
  The \_TransactionSender instance.

#### *property* create_transaction *: \_TransactionCreator*

Get the transaction creator.

* **Returns:**
  The \_TransactionCreator instance.

#### deploy(\*, on_update: algokit_utils.applications.app_deployer.OnUpdate | None = None, on_schema_break: algokit_utils.applications.app_deployer.OnSchemaBreak | None = None, create_params: [algokit_utils.applications.app_client.AppClientMethodCallCreateParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientMethodCallCreateParams) | [algokit_utils.applications.app_client.AppClientBareCallCreateParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientBareCallCreateParams) | None = None, update_params: [algokit_utils.applications.app_client.AppClientMethodCallParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientMethodCallParams) | [algokit_utils.applications.app_client.AppClientBareCallParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientBareCallParams) | None = None, delete_params: [algokit_utils.applications.app_client.AppClientMethodCallParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientMethodCallParams) | [algokit_utils.applications.app_client.AppClientBareCallParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientBareCallParams) | None = None, existing_deployments: [algokit_utils.applications.app_deployer.ApplicationLookup](../app_deployer/index.md#algokit_utils.applications.app_deployer.ApplicationLookup) | None = None, ignore_cache: bool = False, app_name: str | None = None, send_params: [algokit_utils.models.transaction.SendParams](../../models/transaction/index.md#algokit_utils.models.transaction.SendParams) | None = None, compilation_params: [algokit_utils.applications.app_client.AppClientCompilationParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientCompilationParams) | None = None) → tuple[[algokit_utils.applications.app_client.AppClient](../app_client/index.md#algokit_utils.applications.app_client.AppClient), [AppFactoryDeployResult](#algokit_utils.applications.app_factory.AppFactoryDeployResult)]

Idempotently deploy (create if not exists, update if changed) an app against the given name for the given
creator account, including deploy-time TEAL template placeholder substitutions (if specified).

**Note:** When using the return from this function be sure to check operationPerformed to get access to
various return properties like transaction, confirmation and deleteResult.

**Note:** if there is a breaking state schema change to an existing app (and onSchemaBreak is set to
‘replace’) the existing app will be deleted and re-created.

**Note:** if there is an update (different TEAL code) to an existing app (and onUpdate is set to
‘replace’) the existing app will be deleted and re-created.

* **Parameters:**
  * **on_update** – The action to take if there is an update to the app
  * **on_schema_break** – The action to take if there is a breaking state schema change to the app
  * **create_params** – The arguments to create the app
  * **update_params** – The arguments to update the app
  * **delete_params** – The arguments to delete the app
  * **existing_deployments** – The existing deployments to use
  * **ignore_cache** – Whether to ignore the cache
  * **app_name** – The name of the app
  * **send_params** – The parameters for the send call
  * **compilation_params** – The parameters for the compilation
* **Returns:**
  The app client and the result of the deployment
* **Example:**
  ```pycon
  >>> app_client, result = factory.deploy({
  >>>   create_params=AppClientMethodCallCreateParams(
  >>>     sender='SENDER_ADDRESS',
  >>>     approval_program='APPROVAL PROGRAM',
  >>>     clear_state_program='CLEAR PROGRAM',
  >>>     schema={
  >>>       "global_byte_slices": 0,
  >>>       "global_ints": 0,
  >>>       "local_byte_slices": 0,
  >>>       "local_ints": 0
  >>>     }
  >>>   ),
  >>>   update_params=AppClientMethodCallParams(
  >>>     sender='SENDER_ADDRESS'
  >>>   ),
  >>>   delete_params=AppClientMethodCallParams(
  >>>     sender='SENDER_ADDRESS'
  >>>   ),
  >>>   compilation_params=AppClientCompilationParams(
  >>>     updatable=False,
  >>>     deletable=False
  >>>   ),
  >>>   app_name='my_app',
  >>>   on_schema_break=OnSchemaBreak.AppendApp,
  >>>   on_update=OnUpdate.AppendApp
  >>> })
  ```

#### get_app_client_by_id(app_id: int, app_name: str | None = None, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, approval_source_map: algosdk.source_map.SourceMap | None = None, clear_source_map: algosdk.source_map.SourceMap | None = None) → [algokit_utils.applications.app_client.AppClient](../app_client/index.md#algokit_utils.applications.app_client.AppClient)

Returns a new AppClient client for an app instance of the given ID.

* **Parameters:**
  * **app_id** – The id of the app
  * **app_name** – The name of the app
  * **default_sender** – The default sender address
  * **default_signer** – The default signer
  * **approval_source_map** – The approval source map
  * **clear_source_map** – The clear source map
* **Return AppClient:**
  The app client
* **Example:**
  ```pycon
  >>> app_client = factory.get_app_client_by_id(app_id=123)
  ```

#### get_app_client_by_creator_and_name(creator_address: str, app_name: str, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, ignore_cache: bool | None = None, app_lookup_cache: [algokit_utils.applications.app_deployer.ApplicationLookup](../app_deployer/index.md#algokit_utils.applications.app_deployer.ApplicationLookup) | None = None, approval_source_map: algosdk.source_map.SourceMap | None = None, clear_source_map: algosdk.source_map.SourceMap | None = None) → [algokit_utils.applications.app_client.AppClient](../app_client/index.md#algokit_utils.applications.app_client.AppClient)

Returns a new AppClient client, resolving the app by creator address and name
using AlgoKit app deployment semantics (i.e. looking for the app creation transaction note).

* **Parameters:**
  * **creator_address** – The creator address
  * **app_name** – The name of the app
  * **default_sender** – The default sender address
  * **default_signer** – The default signer
  * **ignore_cache** – Whether to ignore the cache and force a lookup
  * **app_lookup_cache** – Optional cache of existing app deployments to use instead of querying the indexer
  * **approval_source_map** – Optional source map for the approval program
  * **clear_source_map** – Optional source map for the clear state program
* **Returns:**
  An AppClient instance configured for the resolved application
* **Example:**
  ```pycon
  >>> app_client = factory.get_app_client_by_creator_and_name(
  ...     creator_address='SENDER_ADDRESS',
  ...     app_name='my_app'
  ... )
  ```

#### export_source_maps() → [algokit_utils.models.application.AppSourceMaps](../../models/application/index.md#algokit_utils.models.application.AppSourceMaps)

#### import_source_maps(source_maps: [algokit_utils.models.application.AppSourceMaps](../../models/application/index.md#algokit_utils.models.application.AppSourceMaps)) → None

Import the provided source maps into the factory.

* **Parameters:**
  **source_maps** – An AppSourceMaps instance containing the approval and clear source maps.

#### compile(compilation_params: [algokit_utils.applications.app_client.AppClientCompilationParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientCompilationParams) | None = None) → [algokit_utils.applications.app_client.AppClientCompilationResult](../app_client/index.md#algokit_utils.applications.app_client.AppClientCompilationResult)

Compile the app’s TEAL code.

* **Parameters:**
  **compilation_params** – The compilation parameters
* **Return AppClientCompilationResult:**
  The compilation result
* **Example:**
  ```pycon
  >>> compilation_result = factory.compile()
  ```
