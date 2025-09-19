# algokit_utils.applications.app_deployer.AppDeployParams

#### *class* algokit_utils.applications.app_deployer.AppDeployParams

Parameters for deploying an app

#### metadata *: [AppDeploymentMetaData](AppDeploymentMetaData.md#algokit_utils.applications.app_deployer.AppDeploymentMetaData)*

The deployment metadata

#### deploy_time_params *: algokit_utils.models.state.TealTemplateParams | None* *= None*

Optional template parameters to use during compilation

#### on_schema_break *: Literal['replace', 'fail', 'append'] | [algokit_utils.applications.enums.OnSchemaBreak](../enums/OnSchemaBreak.md#algokit_utils.applications.enums.OnSchemaBreak) | None* *= None*

Optional on schema break action

#### on_update *: Literal['update', 'replace', 'fail', 'append'] | [algokit_utils.applications.enums.OnUpdate](../enums/OnUpdate.md#algokit_utils.applications.enums.OnUpdate) | None* *= None*

Optional on update action

#### create_params *: [algokit_utils.transactions.transaction_composer.AppCreateParams](../../transactions/transaction_composer/AppCreateParams.md#algokit_utils.transactions.transaction_composer.AppCreateParams) | [algokit_utils.transactions.transaction_composer.AppCreateMethodCallParams](../../transactions/transaction_composer/AppCreateMethodCallParams.md#algokit_utils.transactions.transaction_composer.AppCreateMethodCallParams)*

The creation parameters

#### update_params *: [algokit_utils.transactions.transaction_composer.AppUpdateParams](../../transactions/transaction_composer/AppUpdateParams.md#algokit_utils.transactions.transaction_composer.AppUpdateParams) | [algokit_utils.transactions.transaction_composer.AppUpdateMethodCallParams](../../transactions/transaction_composer/AppUpdateMethodCallParams.md#algokit_utils.transactions.transaction_composer.AppUpdateMethodCallParams)*

The update parameters

#### delete_params *: [algokit_utils.transactions.transaction_composer.AppDeleteParams](../../transactions/transaction_composer/AppDeleteParams.md#algokit_utils.transactions.transaction_composer.AppDeleteParams) | [algokit_utils.transactions.transaction_composer.AppDeleteMethodCallParams](../../transactions/transaction_composer/AppDeleteMethodCallParams.md#algokit_utils.transactions.transaction_composer.AppDeleteMethodCallParams)*

The deletion parameters

#### existing_deployments *: [ApplicationLookup](ApplicationLookup.md#algokit_utils.applications.app_deployer.ApplicationLookup) | None* *= None*

Optional existing deployments

#### ignore_cache *: bool* *= False*

Whether to ignore the cache

#### max_fee *: int | None* *= None*

Optional maximum fee

#### send_params *: [algokit_utils.models.transaction.SendParams](../../models/transaction/SendParams.md#algokit_utils.models.transaction.SendParams) | None* *= None*

Optional send parameters
