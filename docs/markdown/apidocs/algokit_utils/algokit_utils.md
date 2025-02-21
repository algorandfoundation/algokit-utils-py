# [`algokit_utils`](../../autoapi/algokit_utils/index.md#module-algokit_utils)

## Package Contents

### Classes

| [`ABICallArgs`](#algokit_utils.ABICallArgs)                                   |    |
|-------------------------------------------------------------------------------|----|
| [`ABICallArgsDict`](#algokit_utils.ABICallArgsDict)                           |    |
| [`ABICreateCallArgs`](#algokit_utils.ABICreateCallArgs)                       |    |
| [`ABICreateCallArgsDict`](#algokit_utils.ABICreateCallArgsDict)               |    |
| [`ABITransactionResponse`](#algokit_utils.ABITransactionResponse)             |    |
| [`Account`](#algokit_utils.Account)                                           |    |
| [`AlgoClientConfig`](#algokit_utils.AlgoClientConfig)                         |    |
| [`AppDeployMetaData`](#algokit_utils.AppDeployMetaData)                       |    |
| [`AppLookup`](#algokit_utils.AppLookup)                                       |    |
| [`AppMetaData`](#algokit_utils.AppMetaData)                                   |    |
| [`AppReference`](#algokit_utils.AppReference)                                 |    |
| [`ApplicationClient`](#algokit_utils.ApplicationClient)                       |    |
| [`ApplicationSpecification`](#algokit_utils.ApplicationSpecification)         |    |
| [`CallConfig`](#algokit_utils.CallConfig)                                     |    |
| [`CreateCallParameters`](#algokit_utils.CreateCallParameters)                 |    |
| [`CreateCallParametersDict`](#algokit_utils.CreateCallParametersDict)         |    |
| [`CreateTransactionParameters`](#algokit_utils.CreateTransactionParameters)   |    |
| [`DefaultArgumentDict`](#algokit_utils.DefaultArgumentDict)                   |    |
| [`DeployCallArgs`](#algokit_utils.DeployCallArgs)                             |    |
| [`DeployCallArgsDict`](#algokit_utils.DeployCallArgsDict)                     |    |
| [`DeployCreateCallArgs`](#algokit_utils.DeployCreateCallArgs)                 |    |
| [`DeployCreateCallArgsDict`](#algokit_utils.DeployCreateCallArgsDict)         |    |
| [`DeployResponse`](#algokit_utils.DeployResponse)                             |    |
| [`EnsureBalanceParameters`](#algokit_utils.EnsureBalanceParameters)           |    |
| [`EnsureFundedResponse`](#algokit_utils.EnsureFundedResponse)                 |    |
| [`MethodHints`](#algokit_utils.MethodHints)                                   |    |
| [`OnCompleteCallParameters`](#algokit_utils.OnCompleteCallParameters)         |    |
| [`OnCompleteCallParametersDict`](#algokit_utils.OnCompleteCallParametersDict) |    |
| [`OnSchemaBreak`](#algokit_utils.OnSchemaBreak)                               |    |
| [`OnUpdate`](#algokit_utils.OnUpdate)                                         |    |
| [`OperationPerformed`](#algokit_utils.OperationPerformed)                     |    |
| [`Program`](#algokit_utils.Program)                                           |    |
| [`TestNetDispenserApiClient`](#algokit_utils.TestNetDispenserApiClient)       |    |
| [`TransactionParameters`](#algokit_utils.TransactionParameters)               |    |
| [`TransactionParametersDict`](#algokit_utils.TransactionParametersDict)       |    |
| [`TransactionResponse`](#algokit_utils.TransactionResponse)                   |    |
| [`TransferAssetParameters`](#algokit_utils.TransferAssetParameters)           |    |
| [`TransferParameters`](#algokit_utils.TransferParameters)                     |    |

### Functions

| [`create_kmd_wallet_account`](#algokit_utils.create_kmd_wallet_account)               |    |
|---------------------------------------------------------------------------------------|----|
| [`ensure_funded`](#algokit_utils.ensure_funded)                                       |    |
| [`execute_atc_with_logic_error`](#algokit_utils.execute_atc_with_logic_error)         |    |
| [`get_account`](#algokit_utils.get_account)                                           |    |
| [`get_account_from_mnemonic`](#algokit_utils.get_account_from_mnemonic)               |    |
| [`get_algod_client`](#algokit_utils.get_algod_client)                                 |    |
| [`get_app_id_from_tx_id`](#algokit_utils.get_app_id_from_tx_id)                       |    |
| [`get_creator_apps`](#algokit_utils.get_creator_apps)                                 |    |
| [`get_default_localnet_config`](#algokit_utils.get_default_localnet_config)           |    |
| [`get_dispenser_account`](#algokit_utils.get_dispenser_account)                       |    |
| [`get_indexer_client`](#algokit_utils.get_indexer_client)                             |    |
| [`get_kmd_client_from_algod_client`](#algokit_utils.get_kmd_client_from_algod_client) |    |
| [`get_kmd_wallet_account`](#algokit_utils.get_kmd_wallet_account)                     |    |
| [`get_localnet_default_account`](#algokit_utils.get_localnet_default_account)         |    |
| [`get_next_version`](#algokit_utils.get_next_version)                                 |    |
| [`get_or_create_kmd_wallet_account`](#algokit_utils.get_or_create_kmd_wallet_account) |    |
| [`get_sender_from_signer`](#algokit_utils.get_sender_from_signer)                     |    |
| [`is_localnet`](#algokit_utils.is_localnet)                                           |    |
| [`is_mainnet`](#algokit_utils.is_mainnet)                                             |    |
| [`is_testnet`](#algokit_utils.is_testnet)                                             |    |
| [`num_extra_program_pages`](#algokit_utils.num_extra_program_pages)                   |    |
| [`opt_in`](#algokit_utils.opt_in)                                                     |    |
| [`opt_out`](#algokit_utils.opt_out)                                                   |    |
| [`persist_sourcemaps`](#algokit_utils.persist_sourcemaps)                             |    |
| [`replace_template_variables`](#algokit_utils.replace_template_variables)             |    |
| [`simulate_and_persist_response`](#algokit_utils.simulate_and_persist_response)       |    |
| [`transfer`](#algokit_utils.transfer)                                                 |    |
| [`transfer_asset`](#algokit_utils.transfer_asset)                                     |    |

### Data

| [`AppSpecStateDict`](#algokit_utils.AppSpecStateDict)               |    |
|---------------------------------------------------------------------|----|
| [`DELETABLE_TEMPLATE_NAME`](#algokit_utils.DELETABLE_TEMPLATE_NAME) |    |
| [`DefaultArgumentType`](#algokit_utils.DefaultArgumentType)         |    |
| [`MethodConfigDict`](#algokit_utils.MethodConfigDict)               |    |
| [`NOTE_PREFIX`](#algokit_utils.NOTE_PREFIX)                         |    |
| [`OnCompleteActionName`](#algokit_utils.OnCompleteActionName)       |    |
| [`TemplateValueDict`](#algokit_utils.TemplateValueDict)             |    |
| [`TemplateValueMapping`](#algokit_utils.TemplateValueMapping)       |    |
| [`UPDATABLE_TEMPLATE_NAME`](#algokit_utils.UPDATABLE_TEMPLATE_NAME) |    |

### API

### *class* algokit_utils.ABICallArgs

Bases: [`algokit_utils.deploy.DeployCallArgs`](#algokit_utils.DeployCallArgs), `algokit_utils.deploy.ABICall`

### *class* algokit_utils.ABICallArgsDict

Bases: [`algokit_utils.deploy.DeployCallArgsDict`](#algokit_utils.DeployCallArgsDict), `typing.TypedDict`

### Initialization

### *class* algokit_utils.ABICreateCallArgs

Bases: [`algokit_utils.deploy.DeployCreateCallArgs`](#algokit_utils.DeployCreateCallArgs), `algokit_utils.deploy.ABICall`

### *class* algokit_utils.ABICreateCallArgsDict

Bases: [`algokit_utils.deploy.DeployCreateCallArgsDict`](#algokit_utils.DeployCreateCallArgsDict), `typing.TypedDict`

### Initialization

### *class* algokit_utils.ABITransactionResponse

Bases: [`algokit_utils.models.TransactionResponse`](#algokit_utils.TransactionResponse), `typing.Generic`[`algokit_utils.models.ReturnType`]

#### decode_error *: Exception | None*

None

#### method *: algosdk.abi.Method*

None

#### raw_value *: bytes*

None

#### return_value *: algokit_utils.models.ReturnType*

None

#### tx_info *: dict*

None

### *class* algokit_utils.Account

#### address *: str*

‘field(…)’

#### private_key *: str*

None

#### *property* public_key *: bytes*

#### *property* signer *: algosdk.atomic_transaction_composer.AccountTransactionSigner*

### *class* algokit_utils.AlgoClientConfig

#### server *: str*

None

#### token *: str*

None

### *class* algokit_utils.AppDeployMetaData

### *class* algokit_utils.AppLookup

### *class* algokit_utils.AppMetaData

Bases: [`algokit_utils.deploy.AppReference`](#algokit_utils.AppReference), [`algokit_utils.deploy.AppDeployMetaData`](#algokit_utils.AppDeployMetaData)

### *class* algokit_utils.AppReference

### algokit_utils.AppSpecStateDict *: TypeAlias*

None

### *class* algokit_utils.ApplicationClient(algod_client: algosdk.v2client.algod.AlgodClient, app_spec: [algokit_utils.application_specification.ApplicationSpecification](#algokit_utils.ApplicationSpecification) | pathlib.Path, \*, app_id: int = 0, creator: str | [algokit_utils.models.Account](#algokit_utils.Account) | None = None, indexer_client: IndexerClient | None = None, existing_deployments: [algokit_utils.deploy.AppLookup](#algokit_utils.AppLookup) | None = None, signer: algosdk.atomic_transaction_composer.TransactionSigner | [algokit_utils.models.Account](#algokit_utils.Account) | None = None, sender: str | None = None, suggested_params: algosdk.transaction.SuggestedParams | None = None, template_values: algokit_utils.deploy.TemplateValueMapping | None = None, app_name: str | None = None)

### Initialization

#### add_method_call(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, abi_method: algokit_utils.models.ABIMethod | bool | None = None, \*, abi_args: algokit_utils.models.ABIArgsDict | None = None, app_id: int | None = None, parameters: [algokit_utils.models.TransactionParameters](#algokit_utils.TransactionParameters) | [algokit_utils.models.TransactionParametersDict](#algokit_utils.TransactionParametersDict) | None = None, on_complete: algosdk.transaction.OnComplete = transaction.OnComplete.NoOpOC, local_schema: algosdk.transaction.StateSchema | None = None, global_schema: algosdk.transaction.StateSchema | None = None, approval_program: bytes | None = None, clear_program: bytes | None = None, extra_pages: int | None = None, app_args: list[bytes] | None = None, call_config: [algokit_utils.application_specification.CallConfig](#algokit_utils.CallConfig) = au_spec.CallConfig.CALL) → None

#### call(call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.OnCompleteCallParameters](#algokit_utils.OnCompleteCallParameters) | [algokit_utils.models.OnCompleteCallParametersDict](#algokit_utils.OnCompleteCallParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → [algokit_utils.models.TransactionResponse](#algokit_utils.TransactionResponse) | [algokit_utils.models.ABITransactionResponse](#algokit_utils.ABITransactionResponse)

#### clear_state(transaction_parameters: [algokit_utils.models.TransactionParameters](#algokit_utils.TransactionParameters) | [algokit_utils.models.TransactionParametersDict](#algokit_utils.TransactionParametersDict) | None = None, app_args: list[bytes] | None = None) → [algokit_utils.models.TransactionResponse](#algokit_utils.TransactionResponse)

#### close_out(call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.TransactionParameters](#algokit_utils.TransactionParameters) | [algokit_utils.models.TransactionParametersDict](#algokit_utils.TransactionParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → [algokit_utils.models.TransactionResponse](#algokit_utils.TransactionResponse) | [algokit_utils.models.ABITransactionResponse](#algokit_utils.ABITransactionResponse)

#### compose_call(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, /, call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.OnCompleteCallParameters](#algokit_utils.OnCompleteCallParameters) | [algokit_utils.models.OnCompleteCallParametersDict](#algokit_utils.OnCompleteCallParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → None

#### compose_clear_state(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, /, transaction_parameters: [algokit_utils.models.TransactionParameters](#algokit_utils.TransactionParameters) | [algokit_utils.models.TransactionParametersDict](#algokit_utils.TransactionParametersDict) | None = None, app_args: list[bytes] | None = None) → None

#### compose_close_out(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, /, call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.TransactionParameters](#algokit_utils.TransactionParameters) | [algokit_utils.models.TransactionParametersDict](#algokit_utils.TransactionParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → None

#### compose_create(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, /, call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.CreateCallParameters](#algokit_utils.CreateCallParameters) | [algokit_utils.models.CreateCallParametersDict](#algokit_utils.CreateCallParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → None

#### compose_delete(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, /, call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.TransactionParameters](#algokit_utils.TransactionParameters) | [algokit_utils.models.TransactionParametersDict](#algokit_utils.TransactionParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → None

#### compose_opt_in(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, /, call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.TransactionParameters](#algokit_utils.TransactionParameters) | [algokit_utils.models.TransactionParametersDict](#algokit_utils.TransactionParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → None

#### compose_update(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, /, call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.TransactionParameters](#algokit_utils.TransactionParameters) | [algokit_utils.models.TransactionParametersDict](#algokit_utils.TransactionParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → None

#### create(call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.CreateCallParameters](#algokit_utils.CreateCallParameters) | [algokit_utils.models.CreateCallParametersDict](#algokit_utils.CreateCallParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → [algokit_utils.models.TransactionResponse](#algokit_utils.TransactionResponse) | [algokit_utils.models.ABITransactionResponse](#algokit_utils.ABITransactionResponse)

#### delete(call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.TransactionParameters](#algokit_utils.TransactionParameters) | [algokit_utils.models.TransactionParametersDict](#algokit_utils.TransactionParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → [algokit_utils.models.TransactionResponse](#algokit_utils.TransactionResponse) | [algokit_utils.models.ABITransactionResponse](#algokit_utils.ABITransactionResponse)

#### deploy(version: str | None = None, \*, signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, sender: str | None = None, allow_update: bool | None = None, allow_delete: bool | None = None, on_update: [algokit_utils.deploy.OnUpdate](#algokit_utils.OnUpdate) = au_deploy.OnUpdate.Fail, on_schema_break: [algokit_utils.deploy.OnSchemaBreak](#algokit_utils.OnSchemaBreak) = au_deploy.OnSchemaBreak.Fail, template_values: algokit_utils.deploy.TemplateValueMapping | None = None, create_args: [algokit_utils.deploy.ABICreateCallArgs](#algokit_utils.ABICreateCallArgs) | [algokit_utils.deploy.ABICreateCallArgsDict](#algokit_utils.ABICreateCallArgsDict) | [algokit_utils.deploy.DeployCreateCallArgs](#algokit_utils.DeployCreateCallArgs) | None = None, update_args: [algokit_utils.deploy.ABICallArgs](#algokit_utils.ABICallArgs) | [algokit_utils.deploy.ABICallArgsDict](#algokit_utils.ABICallArgsDict) | [algokit_utils.deploy.DeployCallArgs](#algokit_utils.DeployCallArgs) | None = None, delete_args: [algokit_utils.deploy.ABICallArgs](#algokit_utils.ABICallArgs) | [algokit_utils.deploy.ABICallArgsDict](#algokit_utils.ABICallArgsDict) | [algokit_utils.deploy.DeployCallArgs](#algokit_utils.DeployCallArgs) | None = None) → [algokit_utils.deploy.DeployResponse](#algokit_utils.DeployResponse)

#### export_source_map() → str | None

#### get_global_state(\*, raw: bool = False) → dict[bytes | str, bytes | str | int]

#### get_local_state(account: str | None = None, \*, raw: bool = False) → dict[bytes | str, bytes | str | int]

#### get_signer_sender(signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, sender: str | None = None) → tuple[algosdk.atomic_transaction_composer.TransactionSigner | None, str | None]

#### import_source_map(source_map_json: str) → None

#### opt_in(call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.TransactionParameters](#algokit_utils.TransactionParameters) | [algokit_utils.models.TransactionParametersDict](#algokit_utils.TransactionParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → [algokit_utils.models.TransactionResponse](#algokit_utils.TransactionResponse) | [algokit_utils.models.ABITransactionResponse](#algokit_utils.ABITransactionResponse)

#### prepare(signer: algosdk.atomic_transaction_composer.TransactionSigner | [algokit_utils.models.Account](#algokit_utils.Account) | None = None, sender: str | None = None, app_id: int | None = None, template_values: algokit_utils.deploy.TemplateValueDict | None = None) → [algokit_utils.application_client.ApplicationClient](#algokit_utils.ApplicationClient)

#### resolve(to_resolve: [algokit_utils.application_specification.DefaultArgumentDict](#algokit_utils.DefaultArgumentDict)) → int | str | bytes

#### resolve_signer_sender(signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, sender: str | None = None) → tuple[algosdk.atomic_transaction_composer.TransactionSigner, str]

#### update(call_abi_method: algokit_utils.models.ABIMethod | bool | None = None, transaction_parameters: [algokit_utils.models.TransactionParameters](#algokit_utils.TransactionParameters) | [algokit_utils.models.TransactionParametersDict](#algokit_utils.TransactionParametersDict) | None = None, \*\*abi_kwargs: algokit_utils.models.ABIArgType) → [algokit_utils.models.TransactionResponse](#algokit_utils.TransactionResponse) | [algokit_utils.models.ABITransactionResponse](#algokit_utils.ABITransactionResponse)

### *class* algokit_utils.ApplicationSpecification

#### export(directory: pathlib.Path | str | None = None) → None

### *class* algokit_utils.CallConfig

Bases: `enum.IntFlag`

### Initialization

#### ALL

3

#### CALL

1

#### CREATE

2

#### NEVER

0

### *class* algokit_utils.CreateCallParameters

Bases: [`algokit_utils.models.OnCompleteCallParameters`](#algokit_utils.OnCompleteCallParameters)

### *class* algokit_utils.CreateCallParametersDict

Bases: `typing.TypedDict`, [`algokit_utils.models.OnCompleteCallParametersDict`](#algokit_utils.OnCompleteCallParametersDict)

### Initialization

### *class* algokit_utils.CreateTransactionParameters

Bases: [`algokit_utils.models.TransactionParameters`](#algokit_utils.TransactionParameters)

### algokit_utils.DELETABLE_TEMPLATE_NAME

None

### *class* algokit_utils.DefaultArgumentDict

Bases: `typing.TypedDict`

### Initialization

### algokit_utils.DefaultArgumentType *: TypeAlias*

None

### *class* algokit_utils.DeployCallArgs

### *class* algokit_utils.DeployCallArgsDict

Bases: `typing.TypedDict`

### Initialization

### *class* algokit_utils.DeployCreateCallArgs

Bases: [`algokit_utils.deploy.DeployCallArgs`](#algokit_utils.DeployCallArgs)

### *class* algokit_utils.DeployCreateCallArgsDict

Bases: [`algokit_utils.deploy.DeployCallArgsDict`](#algokit_utils.DeployCallArgsDict), `typing.TypedDict`

### Initialization

### *class* algokit_utils.DeployResponse

### *exception* algokit_utils.DeploymentFailedError

Bases: `Exception`

### *class* algokit_utils.EnsureBalanceParameters

#### account_to_fund *: [algokit_utils.models.Account](#algokit_utils.Account) | algosdk.atomic_transaction_composer.AccountTransactionSigner | str*

None

#### fee_micro_algos *: int | None*

None

#### funding_source *: [algokit_utils.models.Account](#algokit_utils.Account) | algosdk.atomic_transaction_composer.AccountTransactionSigner | [algokit_utils.dispenser_api.TestNetDispenserApiClient](#algokit_utils.TestNetDispenserApiClient) | None*

None

#### max_fee_micro_algos *: int | None*

None

#### min_funding_increment_micro_algos *: int*

0

#### min_spending_balance_micro_algos *: int*

None

#### note *: str | bytes | None*

None

#### suggested_params *: algosdk.transaction.SuggestedParams | None*

None

### *class* algokit_utils.EnsureFundedResponse

#### transaction_id *: str*

None

### *exception* algokit_utils.LogicError(\*, logic_error_str: str, program: str, source_map: AlgoSourceMap | None, transaction_id: str, message: str, pc: int, logic_error: Exception | None = None, traces: list | None = None)

Bases: `Exception`

### algokit_utils.MethodConfigDict *: TypeAlias*

None

### *class* algokit_utils.MethodHints

### algokit_utils.NOTE_PREFIX

‘ALGOKIT_DEPLOYER:j’

### algokit_utils.OnCompleteActionName *: TypeAlias*

None

### *class* algokit_utils.OnCompleteCallParameters

Bases: [`algokit_utils.models.TransactionParameters`](#algokit_utils.TransactionParameters)

### *class* algokit_utils.OnCompleteCallParametersDict

Bases: `typing.TypedDict`, [`algokit_utils.models.TransactionParametersDict`](#algokit_utils.TransactionParametersDict)

### Initialization

### *class* algokit_utils.OnSchemaBreak(\*args, \*\*kwds)

Bases: `enum.Enum`

### Initialization

#### AppendApp

3

#### Fail

0

#### ReplaceApp

2

### *class* algokit_utils.OnUpdate(\*args, \*\*kwds)

Bases: `enum.Enum`

### Initialization

#### AppendApp

3

#### Fail

0

#### ReplaceApp

2

#### UpdateApp

1

### *class* algokit_utils.OperationPerformed(\*args, \*\*kwds)

Bases: `enum.Enum`

### Initialization

#### Create

1

#### Nothing

0

#### Replace

3

#### Update

2

### *class* algokit_utils.Program(program: str, client: algosdk.v2client.algod.AlgodClient)

### Initialization

### algokit_utils.TemplateValueDict *: TypeAlias*

None

### algokit_utils.TemplateValueMapping *: TypeAlias*

None

### *class* algokit_utils.TestNetDispenserApiClient(auth_token: str | None = None, request_timeout: int = DISPENSER_REQUEST_TIMEOUT)

### Initialization

#### fund(address: str, amount: int, asset_id: int) → algokit_utils.dispenser_api.DispenserFundResponse

#### get_limit(address: str) → algokit_utils.dispenser_api.DispenserLimitResponse

#### refund(refund_txn_id: str) → None

### *class* algokit_utils.TransactionParameters

#### accounts *: list[str] | None*

None

#### boxes *: collections.abc.Sequence[tuple[int, bytes | bytearray | str | int]] | None*

None

#### foreign_apps *: list[int] | None*

None

#### foreign_assets *: list[int] | None*

None

#### lease *: bytes | str | None*

None

#### note *: bytes | str | None*

None

#### rekey_to *: str | None*

None

#### sender *: str | None*

None

#### signer *: algosdk.atomic_transaction_composer.TransactionSigner | None*

None

#### suggested_params *: algosdk.transaction.SuggestedParams | None*

None

### *class* algokit_utils.TransactionParametersDict

Bases: `typing.TypedDict`

### Initialization

#### accounts *: list[str]*

None

#### boxes *: collections.abc.Sequence[tuple[int, bytes | bytearray | str | int]]*

None

#### foreign_apps *: list[int]*

None

#### foreign_assets *: list[int]*

None

#### lease *: bytes | str*

None

#### note *: bytes | str*

None

#### rekey_to *: str*

None

#### sender *: str*

None

#### signer *: algosdk.atomic_transaction_composer.TransactionSigner*

None

#### suggested_params *: algosdk.transaction.SuggestedParams*

None

### *class* algokit_utils.TransactionResponse

#### confirmed_round *: int | None*

None

#### *static* from_atr(result: algosdk.atomic_transaction_composer.AtomicTransactionResponse | algosdk.atomic_transaction_composer.SimulateAtomicTransactionResponse, transaction_index: int = -1) → [algokit_utils.models.TransactionResponse](#algokit_utils.TransactionResponse)

#### tx_id *: str*

None

### *class* algokit_utils.TransferAssetParameters

Bases: `algokit_utils._transfer.TransferParametersBase`

### *class* algokit_utils.TransferParameters

Bases: `algokit_utils._transfer.TransferParametersBase`

### algokit_utils.UPDATABLE_TEMPLATE_NAME

None

### algokit_utils.create_kmd_wallet_account(kmd_client: algosdk.kmd.KMDClient, name: str) → [algokit_utils.models.Account](#algokit_utils.Account)

### algokit_utils.ensure_funded(client: algosdk.v2client.algod.AlgodClient, parameters: [algokit_utils._ensure_funded.EnsureBalanceParameters](#algokit_utils.EnsureBalanceParameters)) → [algokit_utils._ensure_funded.EnsureFundedResponse](#algokit_utils.EnsureFundedResponse) | None

### algokit_utils.execute_atc_with_logic_error(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, algod_client: algosdk.v2client.algod.AlgodClient, approval_program: str, wait_rounds: int = 4, approval_source_map: algosdk.source_map.SourceMap | Callable[[], algosdk.source_map.SourceMap | None] | None = None) → algosdk.atomic_transaction_composer.AtomicTransactionResponse

### algokit_utils.get_account(client: algosdk.v2client.algod.AlgodClient, name: str, fund_with_algos: float = 1000, kmd_client: KMDClient | None = None) → [algokit_utils.models.Account](#algokit_utils.Account)

### algokit_utils.get_account_from_mnemonic(mnemonic: str) → [algokit_utils.models.Account](#algokit_utils.Account)

### algokit_utils.get_algod_client(config: [algokit_utils.network_clients.AlgoClientConfig](#algokit_utils.AlgoClientConfig) | None = None) → algosdk.v2client.algod.AlgodClient

### algokit_utils.get_app_id_from_tx_id(algod_client: algosdk.v2client.algod.AlgodClient, tx_id: str) → int

### algokit_utils.get_creator_apps(indexer: algosdk.v2client.indexer.IndexerClient, creator_account: [algokit_utils.models.Account](#algokit_utils.Account) | str) → [algokit_utils.deploy.AppLookup](#algokit_utils.AppLookup)

### algokit_utils.get_default_localnet_config(config: Literal[algod, indexer, kmd]) → [algokit_utils.network_clients.AlgoClientConfig](#algokit_utils.AlgoClientConfig)

### algokit_utils.get_dispenser_account(client: algosdk.v2client.algod.AlgodClient) → [algokit_utils.models.Account](#algokit_utils.Account)

### algokit_utils.get_indexer_client(config: [algokit_utils.network_clients.AlgoClientConfig](#algokit_utils.AlgoClientConfig) | None = None) → algosdk.v2client.indexer.IndexerClient

### algokit_utils.get_kmd_client_from_algod_client(client: algosdk.v2client.algod.AlgodClient) → algosdk.kmd.KMDClient

### algokit_utils.get_kmd_wallet_account(client: algosdk.v2client.algod.AlgodClient, kmd_client: algosdk.kmd.KMDClient, name: str, predicate: Callable[[dict[str, Any]], bool] | None = None) → [algokit_utils.models.Account](#algokit_utils.Account) | None

### algokit_utils.get_localnet_default_account(client: algosdk.v2client.algod.AlgodClient) → [algokit_utils.models.Account](#algokit_utils.Account)

### algokit_utils.get_next_version(current_version: str) → str

### algokit_utils.get_or_create_kmd_wallet_account(client: algosdk.v2client.algod.AlgodClient, name: str, fund_with_algos: float = 1000, kmd_client: KMDClient | None = None) → [algokit_utils.models.Account](#algokit_utils.Account)

### algokit_utils.get_sender_from_signer(signer: algosdk.atomic_transaction_composer.TransactionSigner | None) → str | None

### algokit_utils.is_localnet(client: algosdk.v2client.algod.AlgodClient) → bool

### algokit_utils.is_mainnet(client: algosdk.v2client.algod.AlgodClient) → bool

### algokit_utils.is_testnet(client: algosdk.v2client.algod.AlgodClient) → bool

### algokit_utils.num_extra_program_pages(approval: bytes, clear: bytes) → int

### algokit_utils.opt_in(algod_client: algosdk.v2client.algod.AlgodClient, account: [algokit_utils.models.Account](#algokit_utils.Account), asset_ids: list[int]) → dict[int, str]

### algokit_utils.opt_out(algod_client: algosdk.v2client.algod.AlgodClient, account: [algokit_utils.models.Account](#algokit_utils.Account), asset_ids: list[int]) → dict[int, str]

### algokit_utils.persist_sourcemaps(\*, sources: list[algokit_utils._debugging.PersistSourceMapInput], project_root: pathlib.Path, client: algosdk.v2client.algod.AlgodClient, with_sources: bool = True) → None

### algokit_utils.replace_template_variables(program: str, template_values: algokit_utils.deploy.TemplateValueMapping) → str

### algokit_utils.simulate_and_persist_response(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, project_root: pathlib.Path, algod_client: algosdk.v2client.algod.AlgodClient, buffer_size_mb: float = 256) → algosdk.atomic_transaction_composer.SimulateAtomicTransactionResponse

### algokit_utils.transfer(client: algosdk.v2client.algod.AlgodClient, parameters: [algokit_utils._transfer.TransferParameters](#algokit_utils.TransferParameters)) → algosdk.transaction.PaymentTxn

### algokit_utils.transfer_asset(client: algosdk.v2client.algod.AlgodClient, parameters: [algokit_utils._transfer.TransferAssetParameters](#algokit_utils.TransferAssetParameters)) → algosdk.transaction.AssetTransferTxn
