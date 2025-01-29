# algokit_utils.applications.app_deployer

## Attributes

| [`APP_DEPLOY_NOTE_DAPP`](#algokit_utils.applications.app_deployer.APP_DEPLOY_NOTE_DAPP)   |    |
|-------------------------------------------------------------------------------------------|----|

## Classes

| [`AppDeploymentMetaData`](#algokit_utils.applications.app_deployer.AppDeploymentMetaData)   | Metadata about an application stored in a transaction note during creation.   |
|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`ApplicationReference`](#algokit_utils.applications.app_deployer.ApplicationReference)     | Information about an Algorand app                                             |
| [`ApplicationMetaData`](#algokit_utils.applications.app_deployer.ApplicationMetaData)       | Complete metadata about a deployed app                                        |
| [`ApplicationLookup`](#algokit_utils.applications.app_deployer.ApplicationLookup)           | Cache of {py:class}\`ApplicationMetaData\` for a specific creator             |
| [`AppDeployParams`](#algokit_utils.applications.app_deployer.AppDeployParams)               | Parameters for deploying an app                                               |
| [`AppDeployResult`](#algokit_utils.applications.app_deployer.AppDeployResult)               |                                                                               |
| [`AppDeployer`](#algokit_utils.applications.app_deployer.AppDeployer)                       | Manages deployment and deployment metadata of applications                    |

## Module Contents

### algokit_utils.applications.app_deployer.APP_DEPLOY_NOTE_DAPP *: str* *= 'ALGOKIT_DEPLOYER'*

### *class* algokit_utils.applications.app_deployer.AppDeploymentMetaData

Metadata about an application stored in a transaction note during creation.

#### name *: str*

#### version *: str*

#### deletable *: bool | None*

#### updatable *: bool | None*

#### dictify() → dict[str, str | bool]

### *class* algokit_utils.applications.app_deployer.ApplicationReference

Information about an Algorand app

#### app_id *: int*

#### app_address *: str*

### *class* algokit_utils.applications.app_deployer.ApplicationMetaData

Complete metadata about a deployed app

#### reference *: [ApplicationReference](#algokit_utils.applications.app_deployer.ApplicationReference)*

#### deploy_metadata *: [AppDeploymentMetaData](#algokit_utils.applications.app_deployer.AppDeploymentMetaData)*

#### created_round *: int*

#### updated_round *: int*

#### deleted *: bool* *= False*

#### *property* app_id *: int*

#### *property* app_address *: str*

#### *property* name *: str*

#### *property* version *: str*

#### *property* deletable *: bool | None*

#### *property* updatable *: bool | None*

### *class* algokit_utils.applications.app_deployer.ApplicationLookup

Cache of {py:class}\`ApplicationMetaData\` for a specific creator

Can be used as an argument to {py:class}\`ApplicationClient\` to reduce the number of calls when deploying multiple
apps or discovering multiple app_ids

#### creator *: str*

#### apps *: dict[str, [ApplicationMetaData](#algokit_utils.applications.app_deployer.ApplicationMetaData)]*

### *class* algokit_utils.applications.app_deployer.AppDeployParams

Parameters for deploying an app

#### metadata *: [AppDeploymentMetaData](#algokit_utils.applications.app_deployer.AppDeploymentMetaData)*

#### deploy_time_params *: algokit_utils.models.state.TealTemplateParams | None* *= None*

#### on_schema_break *: Literal['replace', 'fail', 'append'] | [algokit_utils.applications.enums.OnSchemaBreak](../enums/index.md#algokit_utils.applications.enums.OnSchemaBreak) | None* *= None*

#### on_update *: Literal['update', 'replace', 'fail', 'append'] | [algokit_utils.applications.enums.OnUpdate](../enums/index.md#algokit_utils.applications.enums.OnUpdate) | None* *= None*

#### create_params *: [algokit_utils.transactions.transaction_composer.AppCreateParams](../../transactions/transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppCreateParams) | [algokit_utils.transactions.transaction_composer.AppCreateMethodCallParams](../../transactions/transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppCreateMethodCallParams)*

#### update_params *: [algokit_utils.transactions.transaction_composer.AppUpdateParams](../../transactions/transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppUpdateParams) | [algokit_utils.transactions.transaction_composer.AppUpdateMethodCallParams](../../transactions/transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppUpdateMethodCallParams)*

#### delete_params *: [algokit_utils.transactions.transaction_composer.AppDeleteParams](../../transactions/transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppDeleteParams) | [algokit_utils.transactions.transaction_composer.AppDeleteMethodCallParams](../../transactions/transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppDeleteMethodCallParams)*

#### existing_deployments *: [ApplicationLookup](#algokit_utils.applications.app_deployer.ApplicationLookup) | None* *= None*

#### ignore_cache *: bool* *= False*

#### max_fee *: int | None* *= None*

#### send_params *: [algokit_utils.models.transaction.SendParams](../../models/transaction/index.md#algokit_utils.models.transaction.SendParams) | None* *= None*

### *class* algokit_utils.applications.app_deployer.AppDeployResult

#### app *: [ApplicationMetaData](#algokit_utils.applications.app_deployer.ApplicationMetaData)*

#### operation_performed *: [algokit_utils.applications.enums.OperationPerformed](../enums/index.md#algokit_utils.applications.enums.OperationPerformed)*

#### create_result *: [algokit_utils.transactions.transaction_sender.SendAppCreateTransactionResult](../../transactions/transaction_sender/index.md#algokit_utils.transactions.transaction_sender.SendAppCreateTransactionResult)[[algokit_utils.applications.abi.ABIReturn](../abi/index.md#algokit_utils.applications.abi.ABIReturn)] | None* *= None*

#### update_result *: [algokit_utils.transactions.transaction_sender.SendAppUpdateTransactionResult](../../transactions/transaction_sender/index.md#algokit_utils.transactions.transaction_sender.SendAppUpdateTransactionResult)[[algokit_utils.applications.abi.ABIReturn](../abi/index.md#algokit_utils.applications.abi.ABIReturn)] | None* *= None*

#### delete_result *: [algokit_utils.transactions.transaction_sender.SendAppTransactionResult](../../transactions/transaction_sender/index.md#algokit_utils.transactions.transaction_sender.SendAppTransactionResult)[[algokit_utils.applications.abi.ABIReturn](../abi/index.md#algokit_utils.applications.abi.ABIReturn)] | None* *= None*

### *class* algokit_utils.applications.app_deployer.AppDeployer(app_manager: [algokit_utils.applications.app_manager.AppManager](../app_manager/index.md#algokit_utils.applications.app_manager.AppManager), transaction_sender: [algokit_utils.transactions.transaction_sender.AlgorandClientTransactionSender](../../transactions/transaction_sender/index.md#algokit_utils.transactions.transaction_sender.AlgorandClientTransactionSender), indexer: algosdk.v2client.indexer.IndexerClient | None = None)

Manages deployment and deployment metadata of applications

#### deploy(deployment: [AppDeployParams](#algokit_utils.applications.app_deployer.AppDeployParams)) → [AppDeployResult](#algokit_utils.applications.app_deployer.AppDeployResult)

#### get_creator_apps_by_name(\*, creator_address: str, ignore_cache: bool = False) → [ApplicationLookup](#algokit_utils.applications.app_deployer.ApplicationLookup)

Get apps created by an account
