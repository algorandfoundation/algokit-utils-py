# algokit_utils.transactions.transaction_composer

## Attributes

| [`ErrorTransformer`](#algokit_utils.transactions.transaction_composer.ErrorTransformer)                                 |    |
|-------------------------------------------------------------------------------------------------------------------------|----|
| [`MethodCallParams`](#algokit_utils.transactions.transaction_composer.MethodCallParams)                                 |    |
| [`AppMethodCallTransactionArgument`](#algokit_utils.transactions.transaction_composer.AppMethodCallTransactionArgument) |    |
| [`TxnParams`](#algokit_utils.transactions.transaction_composer.TxnParams)                                               |    |

## Classes

| [`PaymentParams`](PaymentParams.md#algokit_utils.transactions.transaction_composer.PaymentParams)                                                                      | Parameters for a payment transaction.                                |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`AssetCreateParams`](AssetCreateParams.md#algokit_utils.transactions.transaction_composer.AssetCreateParams)                                                          | Parameters for creating a new asset.                                 |
| [`AssetConfigParams`](AssetConfigParams.md#algokit_utils.transactions.transaction_composer.AssetConfigParams)                                                          | Parameters for configuring an existing asset.                        |
| [`AssetFreezeParams`](AssetFreezeParams.md#algokit_utils.transactions.transaction_composer.AssetFreezeParams)                                                          | Parameters for freezing an asset.                                    |
| [`AssetDestroyParams`](AssetDestroyParams.md#algokit_utils.transactions.transaction_composer.AssetDestroyParams)                                                       | Parameters for destroying an asset.                                  |
| [`OnlineKeyRegistrationParams`](OnlineKeyRegistrationParams.md#algokit_utils.transactions.transaction_composer.OnlineKeyRegistrationParams)                            | Parameters for online key registration.                              |
| [`OfflineKeyRegistrationParams`](OfflineKeyRegistrationParams.md#algokit_utils.transactions.transaction_composer.OfflineKeyRegistrationParams)                         | Parameters for offline key registration.                             |
| [`AssetTransferParams`](AssetTransferParams.md#algokit_utils.transactions.transaction_composer.AssetTransferParams)                                                    | Parameters for transferring an asset.                                |
| [`AssetOptInParams`](AssetOptInParams.md#algokit_utils.transactions.transaction_composer.AssetOptInParams)                                                             | Parameters for opting into an asset.                                 |
| [`AssetOptOutParams`](AssetOptOutParams.md#algokit_utils.transactions.transaction_composer.AssetOptOutParams)                                                          | Parameters for opting out of an asset.                               |
| [`AppCallParams`](AppCallParams.md#algokit_utils.transactions.transaction_composer.AppCallParams)                                                                      | Parameters for calling an application.                               |
| [`AppCreateSchema`](AppCreateSchema.md#algokit_utils.transactions.transaction_composer.AppCreateSchema)                                                                | dict() -> new empty dictionary                                       |
| [`AppCreateParams`](AppCreateParams.md#algokit_utils.transactions.transaction_composer.AppCreateParams)                                                                | Parameters for creating an application.                              |
| [`AppUpdateParams`](AppUpdateParams.md#algokit_utils.transactions.transaction_composer.AppUpdateParams)                                                                | Parameters for updating an application.                              |
| [`AppDeleteParams`](AppDeleteParams.md#algokit_utils.transactions.transaction_composer.AppDeleteParams)                                                                | Parameters for deleting an application.                              |
| [`AppCallMethodCallParams`](AppCallMethodCallParams.md#algokit_utils.transactions.transaction_composer.AppCallMethodCallParams)                                        | Parameters for a regular ABI method call.                            |
| [`AppCreateMethodCallParams`](AppCreateMethodCallParams.md#algokit_utils.transactions.transaction_composer.AppCreateMethodCallParams)                                  | Parameters for an ABI method call that creates an application.       |
| [`AppUpdateMethodCallParams`](AppUpdateMethodCallParams.md#algokit_utils.transactions.transaction_composer.AppUpdateMethodCallParams)                                  | Parameters for an ABI method call that updates an application.       |
| [`AppDeleteMethodCallParams`](AppDeleteMethodCallParams.md#algokit_utils.transactions.transaction_composer.AppDeleteMethodCallParams)                                  | Parameters for an ABI method call that deletes an application.       |
| [`BuiltTransactions`](BuiltTransactions.md#algokit_utils.transactions.transaction_composer.BuiltTransactions)                                                          | Set of transactions built by TransactionComposer.                    |
| [`TransactionComposerBuildResult`](TransactionComposerBuildResult.md#algokit_utils.transactions.transaction_composer.TransactionComposerBuildResult)                   | Result of building transactions with TransactionComposer.            |
| [`SendAtomicTransactionComposerResults`](SendAtomicTransactionComposerResults.md#algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults) | Results from sending an AtomicTransactionComposer transaction group. |
| [`TransactionComposer`](TransactionComposer.md#algokit_utils.transactions.transaction_composer.TransactionComposer)                                                    | A class for composing and managing Algorand transactions.            |

## Functions

| [`calculate_extra_program_pages`](#algokit_utils.transactions.transaction_composer.calculate_extra_program_pages)(→ int)     | Calculate minimum number of extra_pages required for provided approval and clear programs                  |
|------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| [`populate_app_call_resources`](#algokit_utils.transactions.transaction_composer.populate_app_call_resources)(...)           | Populate application call resources based on simulation results.                                           |
| [`prepare_group_for_sending`](#algokit_utils.transactions.transaction_composer.prepare_group_for_sending)(...)               | Take an existing Atomic Transaction Composer and return a new one with changes applied to the transactions |
| [`send_atomic_transaction_composer`](#algokit_utils.transactions.transaction_composer.send_atomic_transaction_composer)(...) | Send an AtomicTransactionComposer transaction group.                                                       |

## Module Contents

### algokit_utils.transactions.transaction_composer.ErrorTransformer

### algokit_utils.transactions.transaction_composer.MethodCallParams

### algokit_utils.transactions.transaction_composer.AppMethodCallTransactionArgument

### algokit_utils.transactions.transaction_composer.TxnParams

### algokit_utils.transactions.transaction_composer.calculate_extra_program_pages(approval: bytes | None, clear: bytes | None) → int

Calculate minimum number of extra_pages required for provided approval and clear programs

### algokit_utils.transactions.transaction_composer.populate_app_call_resources(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, algod: algosdk.v2client.algod.AlgodClient) → algosdk.atomic_transaction_composer.AtomicTransactionComposer

Populate application call resources based on simulation results.

* **Parameters:**
  * **atc** – The AtomicTransactionComposer containing transactions
  * **algod** – Algod client for simulation
* **Returns:**
  Modified AtomicTransactionComposer with populated resources

### algokit_utils.transactions.transaction_composer.prepare_group_for_sending(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, algod: algosdk.v2client.algod.AlgodClient, populate_app_call_resources: bool | None = None, cover_app_call_inner_transaction_fees: bool | None = None, additional_atc_context: AdditionalAtcContext | None = None) → algosdk.atomic_transaction_composer.AtomicTransactionComposer

Take an existing Atomic Transaction Composer and return a new one with changes applied to the transactions
based on the supplied parameters to prepare it for sending.
Please note, that before calling .execute() on the returned ATC, you must call .build_group().

* **Parameters:**
  * **atc** – The AtomicTransactionComposer containing transactions
  * **algod** – Algod client for simulation
  * **populate_app_call_resources** – Whether to populate app call resources
  * **cover_app_call_inner_transaction_fees** – Whether to cover inner txn fees
  * **additional_atc_context** – Additional context for the AtomicTransactionComposer
* **Returns:**
  Modified AtomicTransactionComposer ready for sending

### algokit_utils.transactions.transaction_composer.send_atomic_transaction_composer(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, algod: algosdk.v2client.algod.AlgodClient, \*, max_rounds_to_wait: int | None = 5, skip_waiting: bool = False, suppress_log: bool | None = None, populate_app_call_resources: bool | None = None, cover_app_call_inner_transaction_fees: bool | None = None, additional_atc_context: AdditionalAtcContext | None = None) → [SendAtomicTransactionComposerResults](SendAtomicTransactionComposerResults.md#algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults)

Send an AtomicTransactionComposer transaction group.

Executes a group of transactions atomically using the AtomicTransactionComposer.

* **Parameters:**
  * **atc** – The AtomicTransactionComposer instance containing the transaction group to send
  * **algod** – The Algod client to use for sending the transactions
  * **max_rounds_to_wait** – Maximum number of rounds to wait for confirmation, defaults to 5
  * **skip_waiting** – If True, don’t wait for transaction confirmation, defaults to False
  * **suppress_log** – If True, suppress logging, defaults to None
  * **populate_app_call_resources** – If True, populate app call resources, defaults to None
  * **cover_app_call_inner_transaction_fees** – If True, cover app call inner transaction fees, defaults to None
  * **additional_atc_context** – Additional context for the AtomicTransactionComposer
* **Returns:**
  Results from sending the transaction group
* **Raises:**
  * **Exception** – If there is an error sending the transactions
  * **error** – If there is an error from the Algorand node
