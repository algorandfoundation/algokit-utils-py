# algokit_utils.transactions.transaction_composer

## Attributes

| [`MAX_TRANSACTION_GROUP_SIZE`](#algokit_utils.transactions.transaction_composer.MAX_TRANSACTION_GROUP_SIZE)                     |    |
|---------------------------------------------------------------------------------------------------------------------------------|----|
| [`AppMethodCallTransactionArgument`](#algokit_utils.transactions.transaction_composer.AppMethodCallTransactionArgument)         |    |
| [`ErrorTransformer`](#algokit_utils.transactions.transaction_composer.ErrorTransformer)                                         |    |
| [`SendAtomicTransactionComposerResults`](#algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults) |    |

## Exceptions

| [`ErrorTransformerError`](#algokit_utils.transactions.transaction_composer.ErrorTransformerError)                         | Raised when an error transformer throws.                    |
|---------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| [`InvalidErrorTransformerValueError`](#algokit_utils.transactions.transaction_composer.InvalidErrorTransformerValueError) | Raised when an error transformer returns a non-error value. |

## Classes

| [`TransactionComposerConfig`](#algokit_utils.transactions.transaction_composer.TransactionComposerConfig)           |                                                                     |
|---------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| [`TransactionComposerParams`](#algokit_utils.transactions.transaction_composer.TransactionComposerParams)           |                                                                     |
| [`TransactionWithSigner`](#algokit_utils.transactions.transaction_composer.TransactionWithSigner)                   |                                                                     |
| [`BuiltTransactions`](#algokit_utils.transactions.transaction_composer.BuiltTransactions)                           |                                                                     |
| [`SendTransactionComposerResults`](#algokit_utils.transactions.transaction_composer.SendTransactionComposerResults) |                                                                     |
| [`TransactionComposer`](#algokit_utils.transactions.transaction_composer.TransactionComposer)                       | Light-weight transaction composer built on top of algokit_transact. |

## Module Contents

### algokit_utils.transactions.transaction_composer.MAX_TRANSACTION_GROUP_SIZE *= 16*

### algokit_utils.transactions.transaction_composer.AppMethodCallTransactionArgument

### *exception* algokit_utils.transactions.transaction_composer.ErrorTransformerError

Bases: `RuntimeError`

Raised when an error transformer throws.

### algokit_utils.transactions.transaction_composer.ErrorTransformer

### *exception* algokit_utils.transactions.transaction_composer.InvalidErrorTransformerValueError(original_error: Exception, value: object)

Bases: `RuntimeError`

Raised when an error transformer returns a non-error value.

### *class* algokit_utils.transactions.transaction_composer.TransactionComposerConfig

#### cover_app_call_inner_transaction_fees *: bool* *= False*

#### populate_app_call_resources *: bool* *= True*

### *class* algokit_utils.transactions.transaction_composer.TransactionComposerParams

#### algod *: algokit_algod_client.AlgodClient*

#### get_signer *: collections.abc.Callable[[str], [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)]*

#### get_suggested_params *: collections.abc.Callable[[], algokit_algod_client.models.SuggestedParams] | None* *= None*

#### default_validity_window *: int | None* *= None*

#### app_manager *: [algokit_utils.applications.app_manager.AppManager](../../applications/app_manager/index.md#algokit_utils.applications.app_manager.AppManager) | None* *= None*

#### error_transformers *: list[ErrorTransformer] | None* *= None*

#### composer_config *: [TransactionComposerConfig](#algokit_utils.transactions.transaction_composer.TransactionComposerConfig) | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.TransactionWithSigner

#### txn *: algokit_transact.models.transaction.Transaction*

#### signer *: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

#### method *: ABIMethod | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.BuiltTransactions

#### transactions *: list[algokit_transact.models.transaction.Transaction]*

#### method_calls *: dict[int, ABIMethod]*

#### signers *: dict[int, [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)]*

### *class* algokit_utils.transactions.transaction_composer.SendTransactionComposerResults

#### tx_ids *: list[str]*

#### transactions *: list[algokit_transact.models.transaction.Transaction]*

#### confirmations *: list[algokit_algod_client.models.PendingTransactionResponse]*

#### returns *: list[[algokit_utils.applications.abi.ABIReturn](../../applications/abi/index.md#algokit_utils.applications.abi.ABIReturn)]*

#### group_id *: str | None* *= None*

#### simulate_response *: algokit_algod_client.models.SimulateTransactionResponseModel | None* *= None*

### algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults

### *class* algokit_utils.transactions.transaction_composer.TransactionComposer(params: [TransactionComposerParams](#algokit_utils.transactions.transaction_composer.TransactionComposerParams))

Light-weight transaction composer built on top of algokit_transact.

#### clone(composer_config: [TransactionComposerConfig](#algokit_utils.transactions.transaction_composer.TransactionComposerConfig) | None = None) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Create a shallow copy of this composer, optionally overriding config flags.

#### register_error_transformer(transformer: ErrorTransformer) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_transaction(txn: algokit_transact.models.transaction.Transaction, signer: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner) | None = None) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_payment(params: [algokit_utils.transactions.types.PaymentParams](../types/index.md#algokit_utils.transactions.types.PaymentParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_asset_create(params: [algokit_utils.transactions.types.AssetCreateParams](../types/index.md#algokit_utils.transactions.types.AssetCreateParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_asset_config(params: [algokit_utils.transactions.types.AssetConfigParams](../types/index.md#algokit_utils.transactions.types.AssetConfigParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_asset_freeze(params: [algokit_utils.transactions.types.AssetFreezeParams](../types/index.md#algokit_utils.transactions.types.AssetFreezeParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_asset_destroy(params: [algokit_utils.transactions.types.AssetDestroyParams](../types/index.md#algokit_utils.transactions.types.AssetDestroyParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_asset_transfer(params: [algokit_utils.transactions.types.AssetTransferParams](../types/index.md#algokit_utils.transactions.types.AssetTransferParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_asset_opt_in(params: [algokit_utils.transactions.types.AssetOptInParams](../types/index.md#algokit_utils.transactions.types.AssetOptInParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_asset_opt_out(params: [algokit_utils.transactions.types.AssetOptOutParams](../types/index.md#algokit_utils.transactions.types.AssetOptOutParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_app_create(params: [algokit_utils.transactions.types.AppCreateParams](../types/index.md#algokit_utils.transactions.types.AppCreateParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_app_update(params: [algokit_utils.transactions.types.AppUpdateParams](../types/index.md#algokit_utils.transactions.types.AppUpdateParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_app_delete(params: [algokit_utils.transactions.types.AppDeleteParams](../types/index.md#algokit_utils.transactions.types.AppDeleteParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_app_call(params: [algokit_utils.transactions.types.AppCallParams](../types/index.md#algokit_utils.transactions.types.AppCallParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_app_create_method_call(params: [algokit_utils.transactions.types.AppCreateMethodCallParams](../types/index.md#algokit_utils.transactions.types.AppCreateMethodCallParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_app_update_method_call(params: [algokit_utils.transactions.types.AppUpdateMethodCallParams](../types/index.md#algokit_utils.transactions.types.AppUpdateMethodCallParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_app_delete_method_call(params: [algokit_utils.transactions.types.AppDeleteMethodCallParams](../types/index.md#algokit_utils.transactions.types.AppDeleteMethodCallParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_app_call_method_call(params: [algokit_utils.transactions.types.AppCallMethodCallParams](../types/index.md#algokit_utils.transactions.types.AppCallMethodCallParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_online_key_registration(params: [algokit_utils.transactions.types.OnlineKeyRegistrationParams](../types/index.md#algokit_utils.transactions.types.OnlineKeyRegistrationParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### add_offline_key_registration(params: [algokit_utils.transactions.types.OfflineKeyRegistrationParams](../types/index.md#algokit_utils.transactions.types.OfflineKeyRegistrationParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### count() → int

#### rebuild() → [BuiltTransactions](#algokit_utils.transactions.transaction_composer.BuiltTransactions)

#### *static* arc2_note(note: algokit_utils.models.transaction.Arc2TransactionNote) → bytes

#### add_transaction_composer(composer: [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

#### build() → [BuiltTransactions](#algokit_utils.transactions.transaction_composer.BuiltTransactions)

Build transactions with grouping, resource population, and fee adjustments applied.

#### build_transactions() → [BuiltTransactions](#algokit_utils.transactions.transaction_composer.BuiltTransactions)

Build queued transactions without resource population or grouping.

Returns raw transactions, method call metadata, and any explicit signers. This does not
populate unnamed resources or adjust fees, and it leaves grouping unchanged.

#### gather_signatures() → list[algokit_transact.models.signed_transaction.SignedTransaction]

#### send(params: [algokit_utils.models.transaction.SendParams](../../models/transaction/index.md#algokit_utils.models.transaction.SendParams) | None = None) → [SendTransactionComposerResults](#algokit_utils.transactions.transaction_composer.SendTransactionComposerResults)

Compose the transaction group and send it to the network.

#### simulate(\*, skip_signatures: bool = False, throw_on_failure: bool | None = None, result_on_failure: bool = False, \*\*raw_options: Any) → [SendTransactionComposerResults](#algokit_utils.transactions.transaction_composer.SendTransactionComposerResults)

Compose the transaction group and simulate execution without submitting to the network.

Args:
: skip_signatures: Whether to skip signatures for all built transactions and use an empty signer instead.
  : This will set allow_empty_signatures and fix_signers when sending the request to algod.
  <br/>
  throw_on_failure: Whether to raise on simulation failure. If None, defaults to not result_on_failure.
  result_on_failure: Whether to return the result on simulation failure instead of throwing an error.
  <br/>
  > Defaults to False (throws on failure).
  <br/>
  ```
  **
  ```
  <br/>
  raw_options: Additional options to pass to the simulate request.

Returns:
: SendTransactionComposerResults containing simulation results.

#### set_max_fees(max_fees: dict[int, [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount)]) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Override max_fee for queued transactions by index before building.
