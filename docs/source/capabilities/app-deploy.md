# App deployment

Idempotent (safely retryable) deployment of an app, including deploy-time immutability and permanence control and TEAL template substitution

App deployment is a higher-order use case capability provided by AlgoKit Utils that builds on top of the core capabilities,
particularly [App management](./app-client.md). It allows you to idempotently (with safe retryability) deploy an app, including deploy-time immutability and permanence control and
TEAL template substitution.

To see some usage examples check out the [automated tests](https://github.com/algorandfoundation/algokit-utils-py/blob/main/tests/test_deploy_scenarios.py).

## Design

The architecture design behind app deployment is articulated in an [architecture decision record](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/architecture-decisions/2023-01-12_smart-contract-deployment.md).
While the implementation will naturally evolve over time and diverge from this record, the principles and design goals behind the design are comprehensively explained.

Namely, it described the concept of a smart contract development lifecycle:

1. Development
   1. **Write** smart contracts
   2. **Transpile** smart contracts with development-time parameters (code configuration) to TEAL Templates
   3. **Verify** the TEAL Templates maintain [output stability](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/articles/output_stability.md) and any other static code quality checks
2. Deployment
   1. **Substitute** deploy-time parameters into TEAL Templates to create final TEAL code
   2. **Compile** the TEAL to create byte code using algod
   3. **Deploy** the byte code to one or more Algorand networks (e.g. LocalNet, TestNet, MainNet) to create Deployed Application(s)
3. Runtime
   1. **Validate** the deployed app via automated testing of the smart contracts to provide confidence in their correctness
   2. **Call** deployed smart contract with runtime parameters to utilise it

![App deployment lifecycle](../images/lifecycle.jpg)

The App deployment capability provided by AlgoKit Utils helps implement **#2 Deployment**.

Furthermore, the implementation contains the following implementation characteristics per the original architecture design:

- Deploy-time parameters can be provided and substituted into a TEAL Template by convention (by replacing `TMPL_{KEY}`)
- Contracts can be built by any smart contract framework that supports [ARC-0032](https://arc.algorand.foundation/ARCs/arc-0032) and
  [ARC-0004](https://arc.algorand.foundation/ARCs/arc-0004) ([Beaker](https://beaker.algo.xyz/) or otherwise), which also means the deployment language can be
  different to the development language e.g. you can deploy a Python smart contract with TypeScript for instance
- There is explicit control of the immutability (updatability / upgradeability) and permanence (deletability) of the smart contract, which can be varied per environment to allow for easier
  development and testing in non-MainNet environments (by replacing `TMPL_UPDATABLE` and `TMPL_DELETABLE` at deploy-time by convention, if present)
- Contracts are resolvable by a string "name" for a given creator to allow automated determination of whether that contract had been deployed previously or not, but can also be resolved by ID
  instead

## Finding apps by creator

The `AppDeployer.get_creator_apps_by_name()` method performs indexer lookups to find all apps created by an account that were deployed using this framework. The results are cached in an `ApplicationLookup` object.

```
ALGOKIT_DEPLOYER:j{name:string, version:string, updatable?:boolean, deletable?:boolean}
```

Any creation transactions or update transactions are then retrieved and processed in chronological order to result in an `AppLookup` object

Given there are a number of indexer calls to retrieve this data it's a non-trivial object to create, and it's recommended that for the duration you are performing a single deployment
you hold a value of it rather than recalculating it. Most AlgoKit Utils functions that need it will also take an optional value of it that will be used in preference to retrieving a
fresh version.

## Deploying an application

The class that performs the deployment logic is `AppDeployer` with the `deploy` method. It performs an idempotent (safely retryable) deployment. It will detect if the app already exists and if it doesn't it will create it. If the app does already exist then it will:

- Detect if the app has been updated (i.e. the logic has changed) and either fail or perform either an update or a replacement based on the deployment configuration.
- Detect if the app has a breaking schema change (i.e. more global or local storage is needed than was originally requested) and either fail or perform a replacement based on the deployment configuration.

It will automatically add metadata to the transaction note of the create or update calls that indicates the name, version, updatability and deletability of the contract.

`deploy` automatically executes [template substitution](#compilation-and-template-substitution) including deploy-time control of permanence and immutability.

### Input parameters

The `AppDeployParams` dataclass accepts these key parameters:

- `metadata`: Required AppDeploymentMetaData containing name, version, deletable and updatable flags
- `deploy_time_params`: Optional TealTemplateParams for TEAL template substitution
- `on_schema_break`: Optional behavior for schema breaks - can be string literal "replace", "fail", "append" or OnSchemaBreak enum
- `on_update`: Optional behavior for updates - can be string literal "update", "replace", "fail", "append" or OnUpdate enum
- `create_params`: AppCreateParams or AppCreateMethodCallParams specifying app creation parameters
- `update_params`: AppUpdateParams or AppUpdateMethodCallParams specifying app update parameters
- `delete_params`: AppDeleteParams or AppDeleteMethodCallParams specifying app deletion parameters
- `existing_deployments`: Optional ApplicationLookup to cache and reduce indexer calls
- `ignore_cache`: When true, forces fresh indexer lookup even if creator apps are cached
- `max_fee`: Maximum microalgos to spend on any single transaction
- `send_params`: Additional transaction sending parameters (fee, signer, etc.)

### Error Handling

Specific error cases that throw ValueError:

- Schema break with on_schema_break=fail
- Update attempt on non-updatable app
- Replacement attempt on non-deletable app
- Invalid `existing_deployments` cache provided

### Idempotency

`deploy` is idempotent which means you can safely call it again multiple times, and it will only apply any changes it detects. If you call it again straight after calling it then it will
do nothing. This also means it can be used to find an existing app based on the supplied creator and app_spec or name.

### Compilation and template substitution

When compiling TEAL template code, the capabilities described in the [design above](#design) are present, namely the ability to supply deploy-time parameters and the ability to control immutability and permanence of the smart contract at deploy-time.

In order for a smart contract to be able to use this functionality, it must have a TEAL Template that contains the following:

- `TMPL_{key}` - Which can be replaced with a number or a string / byte array which wil be automatically hexadecimal encoded
- `TMPL_UPDATABLE` - Which will be replaced with a `1` if an app should be updatable and `0` if it shouldn't (immutable)
- `TMPL_DELETABLE` - Which will be replaced with a `1` if an app should be deletable and `0` if it shouldn't (permanent)

If you are building a smart contract using the [Python AlgoKit template](https://github.com/algorandfoundation/algokit-python-template) it provides a reference implementation out of the box for the deploy-time immutability and permanence control.

### Return value

`deploy` returns an `AppDeployResult` object containing:

- `operation_performed`: Enum indicating action taken (Create/Update/Replace/Nothing)
- `app`: ApplicationMetaData with final app state
- `create_result`: Transaction result if creation occurred
- `update_result`: Transaction result if update occurred
- `delete_result`: Transaction result if replacement occurred
