# algokit_utils.applications.app_factory

## Classes

| [`AppFactoryParams`](#algokit_utils.applications.app_factory.AppFactoryParams)                                           |                                                      |
|--------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| [`AppFactoryCreateParams`](#algokit_utils.applications.app_factory.AppFactoryCreateParams)                               | Parameters for creating application with bare call.  |
| [`AppFactoryCreateMethodCallParams`](#algokit_utils.applications.app_factory.AppFactoryCreateMethodCallParams)           | Parameters for creating application with method call |
| [`AppFactoryCreateMethodCallResult`](#algokit_utils.applications.app_factory.AppFactoryCreateMethodCallResult)           | Base class for transaction results.                  |
| [`SendAppFactoryTransactionResult`](#algokit_utils.applications.app_factory.SendAppFactoryTransactionResult)             | Result of an application transaction.                |
| [`SendAppUpdateFactoryTransactionResult`](#algokit_utils.applications.app_factory.SendAppUpdateFactoryTransactionResult) | Result of updating an application.                   |
| [`SendAppCreateFactoryTransactionResult`](#algokit_utils.applications.app_factory.SendAppCreateFactoryTransactionResult) | Result of creating a new application.                |
| [`AppFactoryDeployResult`](#algokit_utils.applications.app_factory.AppFactoryDeployResult)                               | Result from deploying an application via AppFactory  |
| [`AppFactory`](#algokit_utils.applications.app_factory.AppFactory)                                                       |                                                      |

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

### *class* algokit_utils.applications.app_factory.AppFactory(params: [AppFactoryParams](#algokit_utils.applications.app_factory.AppFactoryParams))

#### *property* app_name *: str*

#### *property* app_spec *: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract)*

#### *property* algorand *: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient)*

#### *property* params *: \_MethodParamsBuilder*

#### *property* send *: \_TransactionSender*

#### *property* create_transaction *: \_TransactionCreator*

#### deploy(\*, on_update: algokit_utils.applications.app_deployer.OnUpdate | None = None, on_schema_break: algokit_utils.applications.app_deployer.OnSchemaBreak | None = None, create_params: [algokit_utils.applications.app_client.AppClientMethodCallCreateParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientMethodCallCreateParams) | [algokit_utils.applications.app_client.AppClientBareCallCreateParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientBareCallCreateParams) | None = None, update_params: [algokit_utils.applications.app_client.AppClientMethodCallParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientMethodCallParams) | [algokit_utils.applications.app_client.AppClientBareCallParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientBareCallParams) | None = None, delete_params: [algokit_utils.applications.app_client.AppClientMethodCallParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientMethodCallParams) | [algokit_utils.applications.app_client.AppClientBareCallParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientBareCallParams) | None = None, existing_deployments: [algokit_utils.applications.app_deployer.ApplicationLookup](../app_deployer/index.md#algokit_utils.applications.app_deployer.ApplicationLookup) | None = None, ignore_cache: bool = False, app_name: str | None = None, send_params: [algokit_utils.models.transaction.SendParams](../../models/transaction/index.md#algokit_utils.models.transaction.SendParams) | None = None, compilation_params: [algokit_utils.applications.app_client.AppClientCompilationParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientCompilationParams) | None = None) → tuple[[algokit_utils.applications.app_client.AppClient](../app_client/index.md#algokit_utils.applications.app_client.AppClient), [AppFactoryDeployResult](#algokit_utils.applications.app_factory.AppFactoryDeployResult)]

Deploy the application with the specified parameters.

#### get_app_client_by_id(app_id: int, app_name: str | None = None, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, approval_source_map: algosdk.source_map.SourceMap | None = None, clear_source_map: algosdk.source_map.SourceMap | None = None) → [algokit_utils.applications.app_client.AppClient](../app_client/index.md#algokit_utils.applications.app_client.AppClient)

#### get_app_client_by_creator_and_name(creator_address: str, app_name: str, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, ignore_cache: bool | None = None, app_lookup_cache: [algokit_utils.applications.app_deployer.ApplicationLookup](../app_deployer/index.md#algokit_utils.applications.app_deployer.ApplicationLookup) | None = None, approval_source_map: algosdk.source_map.SourceMap | None = None, clear_source_map: algosdk.source_map.SourceMap | None = None) → [algokit_utils.applications.app_client.AppClient](../app_client/index.md#algokit_utils.applications.app_client.AppClient)

#### export_source_maps() → [algokit_utils.models.application.AppSourceMaps](../../models/application/index.md#algokit_utils.models.application.AppSourceMaps)

#### import_source_maps(source_maps: [algokit_utils.models.application.AppSourceMaps](../../models/application/index.md#algokit_utils.models.application.AppSourceMaps)) → None

#### compile(compilation_params: [algokit_utils.applications.app_client.AppClientCompilationParams](../app_client/index.md#algokit_utils.applications.app_client.AppClientCompilationParams) | None = None) → [algokit_utils.applications.app_client.AppClientCompilationResult](../app_client/index.md#algokit_utils.applications.app_client.AppClientCompilationResult)
