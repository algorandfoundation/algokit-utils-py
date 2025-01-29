# algokit_utils.transactions.transaction_composer

## Attributes

| [`MethodCallParams`](#algokit_utils.transactions.transaction_composer.MethodCallParams)                                 |    |
|-------------------------------------------------------------------------------------------------------------------------|----|
| [`AppMethodCallTransactionArgument`](#algokit_utils.transactions.transaction_composer.AppMethodCallTransactionArgument) |    |
| [`TxnParams`](#algokit_utils.transactions.transaction_composer.TxnParams)                                               |    |

## Classes

| [`PaymentParams`](#algokit_utils.transactions.transaction_composer.PaymentParams)                                               | Parameters for a payment transaction.                                |
|---------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`AssetCreateParams`](#algokit_utils.transactions.transaction_composer.AssetCreateParams)                                       | Parameters for creating a new asset.                                 |
| [`AssetConfigParams`](#algokit_utils.transactions.transaction_composer.AssetConfigParams)                                       | Parameters for configuring an existing asset.                        |
| [`AssetFreezeParams`](#algokit_utils.transactions.transaction_composer.AssetFreezeParams)                                       | Parameters for freezing an asset.                                    |
| [`AssetDestroyParams`](#algokit_utils.transactions.transaction_composer.AssetDestroyParams)                                     | Parameters for destroying an asset.                                  |
| [`OnlineKeyRegistrationParams`](#algokit_utils.transactions.transaction_composer.OnlineKeyRegistrationParams)                   | Parameters for online key registration.                              |
| [`OfflineKeyRegistrationParams`](#algokit_utils.transactions.transaction_composer.OfflineKeyRegistrationParams)                 | Parameters for offline key registration.                             |
| [`AssetTransferParams`](#algokit_utils.transactions.transaction_composer.AssetTransferParams)                                   | Parameters for transferring an asset.                                |
| [`AssetOptInParams`](#algokit_utils.transactions.transaction_composer.AssetOptInParams)                                         | Parameters for opting into an asset.                                 |
| [`AssetOptOutParams`](#algokit_utils.transactions.transaction_composer.AssetOptOutParams)                                       | Parameters for opting out of an asset.                               |
| [`AppCallParams`](#algokit_utils.transactions.transaction_composer.AppCallParams)                                               | Parameters for calling an application.                               |
| [`AppCreateSchema`](#algokit_utils.transactions.transaction_composer.AppCreateSchema)                                           | dict() -> new empty dictionary                                       |
| [`AppCreateParams`](#algokit_utils.transactions.transaction_composer.AppCreateParams)                                           | Parameters for creating an application.                              |
| [`AppUpdateParams`](#algokit_utils.transactions.transaction_composer.AppUpdateParams)                                           | Parameters for updating an application.                              |
| [`AppDeleteParams`](#algokit_utils.transactions.transaction_composer.AppDeleteParams)                                           | Parameters for deleting an application.                              |
| [`AppCallMethodCallParams`](#algokit_utils.transactions.transaction_composer.AppCallMethodCallParams)                           | Parameters for a regular ABI method call.                            |
| [`AppCreateMethodCallParams`](#algokit_utils.transactions.transaction_composer.AppCreateMethodCallParams)                       | Parameters for an ABI method call that creates an application.       |
| [`AppUpdateMethodCallParams`](#algokit_utils.transactions.transaction_composer.AppUpdateMethodCallParams)                       | Parameters for an ABI method call that updates an application.       |
| [`AppDeleteMethodCallParams`](#algokit_utils.transactions.transaction_composer.AppDeleteMethodCallParams)                       | Parameters for an ABI method call that deletes an application.       |
| [`BuiltTransactions`](#algokit_utils.transactions.transaction_composer.BuiltTransactions)                                       | Set of transactions built by TransactionComposer.                    |
| [`TransactionComposerBuildResult`](#algokit_utils.transactions.transaction_composer.TransactionComposerBuildResult)             | Result of building transactions with TransactionComposer.            |
| [`SendAtomicTransactionComposerResults`](#algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults) | Results from sending an AtomicTransactionComposer transaction group. |
| [`TransactionComposer`](#algokit_utils.transactions.transaction_composer.TransactionComposer)                                   | A class for composing and managing Algorand transactions.            |

## Functions

| [`send_atomic_transaction_composer`](#algokit_utils.transactions.transaction_composer.send_atomic_transaction_composer)(...)   | Send an AtomicTransactionComposer transaction group.   |
|--------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------|

## Module Contents

### *class* algokit_utils.transactions.transaction_composer.PaymentParams

Bases: `_CommonTxnParams`

Parameters for a payment transaction.

* **Variables:**
  * **receiver** – The account that will receive the ALGO
  * **amount** – Amount to send
  * **close_remainder_to** – If given, close the sender account and send the remaining balance to this address,

defaults to None

#### receiver *: str*

#### amount *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount)*

#### close_remainder_to *: str | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.AssetCreateParams

Bases: `_CommonTxnParams`

Parameters for creating a new asset.

* **Variables:**
  * **total** – The total amount of the smallest divisible unit to create
  * **decimals** – The amount of decimal places the asset should have, defaults to None
  * **default_frozen** – Whether the asset is frozen by default in the creator address, defaults to None
  * **manager** – The address that can change the manager, reserve, clawback, and freeze addresses, defaults to None
  * **reserve** – The address that holds the uncirculated supply, defaults to None
  * **freeze** – The address that can freeze the asset in any account, defaults to None
  * **clawback** – The address that can clawback the asset from any account, defaults to None
  * **unit_name** – The short ticker name for the asset, defaults to None
  * **asset_name** – The full name of the asset, defaults to None
  * **url** – The metadata URL for the asset, defaults to None
  * **metadata_hash** – Hash of the metadata contained in the metadata URL, defaults to None

#### total *: int*

#### asset_name *: str | None* *= None*

#### unit_name *: str | None* *= None*

#### url *: str | None* *= None*

#### decimals *: int | None* *= None*

#### default_frozen *: bool | None* *= None*

#### manager *: str | None* *= None*

#### reserve *: str | None* *= None*

#### freeze *: str | None* *= None*

#### clawback *: str | None* *= None*

#### metadata_hash *: bytes | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.AssetConfigParams

Bases: `_CommonTxnParams`

Parameters for configuring an existing asset.

* **Variables:**
  * **asset_id** – ID of the asset
  * **manager** – The address that can change the manager, reserve, clawback, and freeze addresses, defaults to None
  * **reserve** – The address that holds the uncirculated supply, defaults to None
  * **freeze** – The address that can freeze the asset in any account, defaults to None
  * **clawback** – The address that can clawback the asset from any account, defaults to None

#### asset_id *: int*

#### manager *: str | None* *= None*

#### reserve *: str | None* *= None*

#### freeze *: str | None* *= None*

#### clawback *: str | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.AssetFreezeParams

Bases: `_CommonTxnParams`

Parameters for freezing an asset.

* **Variables:**
  * **asset_id** – The ID of the asset
  * **account** – The account to freeze or unfreeze
  * **frozen** – Whether the assets in the account should be frozen

#### asset_id *: int*

#### account *: str*

#### frozen *: bool*

### *class* algokit_utils.transactions.transaction_composer.AssetDestroyParams

Bases: `_CommonTxnParams`

Parameters for destroying an asset.

* **Variables:**
  **asset_id** – ID of the asset

#### asset_id *: int*

### *class* algokit_utils.transactions.transaction_composer.OnlineKeyRegistrationParams

Bases: `_CommonTxnParams`

Parameters for online key registration.

* **Variables:**
  * **vote_key** – The root participation public key
  * **selection_key** – The VRF public key
  * **vote_first** – The first round that the participation key is valid
  * **vote_last** – The last round that the participation key is valid
  * **vote_key_dilution** – The dilution for the 2-level participation key
  * **state_proof_key** – The 64 byte state proof public key commitment, defaults to None

#### vote_key *: str*

#### selection_key *: str*

#### vote_first *: int*

#### vote_last *: int*

#### vote_key_dilution *: int*

#### state_proof_key *: bytes | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.OfflineKeyRegistrationParams

Bases: `_CommonTxnParams`

Parameters for offline key registration.

* **Variables:**
  **prevent_account_from_ever_participating_again** – Whether to prevent the account from ever participating again

#### prevent_account_from_ever_participating_again *: bool*

### *class* algokit_utils.transactions.transaction_composer.AssetTransferParams

Bases: `_CommonTxnParams`

Parameters for transferring an asset.

* **Variables:**
  * **asset_id** – ID of the asset
  * **amount** – Amount of the asset to transfer (smallest divisible unit)
  * **receiver** – The account to send the asset to
  * **clawback_target** – The account to take the asset from, defaults to None
  * **close_asset_to** – The account to close the asset to, defaults to None

#### asset_id *: int*

#### amount *: int*

#### receiver *: str*

#### clawback_target *: str | None* *= None*

#### close_asset_to *: str | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.AssetOptInParams

Bases: `_CommonTxnParams`

Parameters for opting into an asset.

* **Variables:**
  **asset_id** – ID of the asset

#### asset_id *: int*

### *class* algokit_utils.transactions.transaction_composer.AssetOptOutParams

Bases: `_CommonTxnParams`

Parameters for opting out of an asset.

* **Variables:**
  * **asset_id** – ID of the asset
  * **creator** – The creator address of the asset

#### asset_id *: int*

#### creator *: str*

### *class* algokit_utils.transactions.transaction_composer.AppCallParams

Bases: `_CommonTxnParams`

Parameters for calling an application.

* **Variables:**
  * **on_complete** – The OnComplete action
  * **app_id** – ID of the application, defaults to None
  * **approval_program** – The program to execute for all OnCompletes other than ClearState, defaults to None
  * **clear_state_program** – The program to execute for ClearState OnComplete, defaults to None
  * **schema** – The state schema for the app. This is immutable, defaults to None
  * **args** – Application arguments, defaults to None
  * **account_references** – Account references, defaults to None
  * **app_references** – App references, defaults to None
  * **asset_references** – Asset references, defaults to None
  * **extra_pages** – Number of extra pages required for the programs, defaults to None
  * **box_references** – Box references, defaults to None

#### on_complete *: algosdk.transaction.OnComplete*

#### app_id *: int | None* *= None*

#### approval_program *: str | bytes | None* *= None*

#### clear_state_program *: str | bytes | None* *= None*

#### schema *: dict[str, int] | None* *= None*

#### args *: list[bytes] | None* *= None*

#### account_references *: list[str] | None* *= None*

#### app_references *: list[int] | None* *= None*

#### asset_references *: list[int] | None* *= None*

#### extra_pages *: int | None* *= None*

#### box_references *: list[[algokit_utils.models.state.BoxReference](../../models/state/index.md#algokit_utils.models.state.BoxReference) | algokit_utils.models.state.BoxIdentifier] | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.AppCreateSchema

Bases: `TypedDict`

dict() -> new empty dictionary
dict(mapping) -> new dictionary initialized from a mapping object’s

> (key, value) pairs

dict(iterable) -> new dictionary initialized as if via:
: d = {}
  for k, v in iterable:
  <br/>
  > d[k] = v

dict(

```
**
```

kwargs) -> new dictionary initialized with the name=value pairs
: in the keyword argument list.  For example:  dict(one=1, two=2)

#### global_ints *: int*

#### global_byte_slices *: int*

#### local_ints *: int*

#### local_byte_slices *: int*

### *class* algokit_utils.transactions.transaction_composer.AppCreateParams

Bases: `_CommonTxnParams`

Parameters for creating an application.

* **Variables:**
  **approval_program** – The program to execute for all OnCompletes other than ClearState as raw teal (string)

or compiled teal (bytes)
:ivar clear_state_program: The program to execute for ClearState OnComplete as raw teal (string)
or compiled teal (bytes)
:ivar schema: The state schema for the app. This is immutable, defaults to None
:ivar on_complete: The OnComplete action (cannot be ClearState), defaults to None
:ivar args: Application arguments, defaults to None
:ivar account_references: Account references, defaults to None
:ivar app_references: App references, defaults to None
:ivar asset_references: Asset references, defaults to None
:ivar box_references: Box references, defaults to None
:ivar extra_program_pages: Number of extra pages required for the programs, defaults to None

#### approval_program *: str | bytes*

#### clear_state_program *: str | bytes*

#### schema *: [AppCreateSchema](#algokit_utils.transactions.transaction_composer.AppCreateSchema) | None* *= None*

#### on_complete *: algosdk.transaction.OnComplete | None* *= None*

#### args *: list[bytes] | None* *= None*

#### account_references *: list[str] | None* *= None*

#### app_references *: list[int] | None* *= None*

#### asset_references *: list[int] | None* *= None*

#### box_references *: list[[algokit_utils.models.state.BoxReference](../../models/state/index.md#algokit_utils.models.state.BoxReference) | algokit_utils.models.state.BoxIdentifier] | None* *= None*

#### extra_program_pages *: int | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.AppUpdateParams

Bases: `_CommonTxnParams`

Parameters for updating an application.

* **Variables:**
  * **app_id** – ID of the application
  * **approval_program** – The program to execute for all OnCompletes other than ClearState as raw teal (string)

or compiled teal (bytes)
:ivar clear_state_program: The program to execute for ClearState OnComplete as raw teal (string)
or compiled teal (bytes)
:ivar args: Application arguments, defaults to None
:ivar account_references: Account references, defaults to None
:ivar app_references: App references, defaults to None
:ivar asset_references: Asset references, defaults to None
:ivar box_references: Box references, defaults to None
:ivar on_complete: The OnComplete action, defaults to None

#### app_id *: int*

#### approval_program *: str | bytes*

#### clear_state_program *: str | bytes*

#### args *: list[bytes] | None* *= None*

#### account_references *: list[str] | None* *= None*

#### app_references *: list[int] | None* *= None*

#### asset_references *: list[int] | None* *= None*

#### box_references *: list[[algokit_utils.models.state.BoxReference](../../models/state/index.md#algokit_utils.models.state.BoxReference) | algokit_utils.models.state.BoxIdentifier] | None* *= None*

#### on_complete *: algosdk.transaction.OnComplete | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.AppDeleteParams

Bases: `_CommonTxnParams`

Parameters for deleting an application.

* **Variables:**
  * **app_id** – ID of the application
  * **args** – Application arguments, defaults to None
  * **account_references** – Account references, defaults to None
  * **app_references** – App references, defaults to None
  * **asset_references** – Asset references, defaults to None
  * **box_references** – Box references, defaults to None
  * **on_complete** – The OnComplete action, defaults to DeleteApplicationOC

#### app_id *: int*

#### args *: list[bytes] | None* *= None*

#### account_references *: list[str] | None* *= None*

#### app_references *: list[int] | None* *= None*

#### asset_references *: list[int] | None* *= None*

#### box_references *: list[[algokit_utils.models.state.BoxReference](../../models/state/index.md#algokit_utils.models.state.BoxReference) | algokit_utils.models.state.BoxIdentifier] | None* *= None*

#### on_complete *: algosdk.transaction.OnComplete*

### *class* algokit_utils.transactions.transaction_composer.AppCallMethodCallParams

Bases: `_BaseAppMethodCall`

Parameters for a regular ABI method call.

* **Variables:**
  * **app_id** – ID of the application
  * **method** – The ABI method to call
  * **args** – Arguments to the ABI method, either an ABI value, transaction with explicit signer,

transaction, another method call, or None
:ivar on_complete: The OnComplete action (cannot be UpdateApplication or ClearState), defaults to None

#### app_id *: int*

#### on_complete *: algosdk.transaction.OnComplete | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.AppCreateMethodCallParams

Bases: `_BaseAppMethodCall`

Parameters for an ABI method call that creates an application.

* **Variables:**
  * **approval_program** – The program to execute for all OnCompletes other than ClearState
  * **clear_state_program** – The program to execute for ClearState OnComplete
  * **schema** – The state schema for the app, defaults to None
  * **on_complete** – The OnComplete action (cannot be ClearState), defaults to None
  * **extra_program_pages** – Number of extra pages required for the programs, defaults to None

#### approval_program *: str | bytes*

#### clear_state_program *: str | bytes*

#### schema *: [AppCreateSchema](#algokit_utils.transactions.transaction_composer.AppCreateSchema) | None* *= None*

#### on_complete *: algosdk.transaction.OnComplete | None* *= None*

#### extra_program_pages *: int | None* *= None*

### *class* algokit_utils.transactions.transaction_composer.AppUpdateMethodCallParams

Bases: `_BaseAppMethodCall`

Parameters for an ABI method call that updates an application.

* **Variables:**
  * **app_id** – ID of the application
  * **approval_program** – The program to execute for all OnCompletes other than ClearState
  * **clear_state_program** – The program to execute for ClearState OnComplete
  * **on_complete** – The OnComplete action, defaults to UpdateApplicationOC

#### app_id *: int*

#### approval_program *: str | bytes*

#### clear_state_program *: str | bytes*

#### on_complete *: algosdk.transaction.OnComplete*

### *class* algokit_utils.transactions.transaction_composer.AppDeleteMethodCallParams

Bases: `_BaseAppMethodCall`

Parameters for an ABI method call that deletes an application.

* **Variables:**
  * **app_id** – ID of the application
  * **on_complete** – The OnComplete action, defaults to DeleteApplicationOC

#### app_id *: int*

#### on_complete *: algosdk.transaction.OnComplete*

### algokit_utils.transactions.transaction_composer.MethodCallParams

### algokit_utils.transactions.transaction_composer.AppMethodCallTransactionArgument

### algokit_utils.transactions.transaction_composer.TxnParams

### *class* algokit_utils.transactions.transaction_composer.BuiltTransactions

Set of transactions built by TransactionComposer.

* **Variables:**
  * **transactions** – The built transactions
  * **method_calls** – Any ABIMethod objects associated with any of the transactions in a map keyed by txn id
  * **signers** – Any TransactionSigner objects associated with any of the transactions in a map keyed by txn id

#### transactions *: list[algosdk.transaction.Transaction]*

#### method_calls *: dict[int, algosdk.abi.Method]*

#### signers *: dict[int, algosdk.atomic_transaction_composer.TransactionSigner]*

### *class* algokit_utils.transactions.transaction_composer.TransactionComposerBuildResult

Result of building transactions with TransactionComposer.

* **Variables:**
  * **atc** – The AtomicTransactionComposer instance
  * **transactions** – The list of transactions with signers
  * **method_calls** – Map of transaction index to ABI method

#### atc *: algosdk.atomic_transaction_composer.AtomicTransactionComposer*

#### transactions *: list[algosdk.atomic_transaction_composer.TransactionWithSigner]*

#### method_calls *: dict[int, algosdk.abi.Method]*

### *class* algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults

Results from sending an AtomicTransactionComposer transaction group.

* **Variables:**
  * **group_id** – The group ID if this was a transaction group
  * **confirmations** – The confirmation info for each transaction
  * **tx_ids** – The transaction IDs that were sent
  * **transactions** – The transactions that were sent
  * **returns** – The ABI return values from any ABI method calls
  * **simulate_response** – The simulation response if simulation was performed, defaults to None

#### group_id *: str*

#### confirmations *: list[algosdk.v2client.algod.AlgodResponseType]*

#### tx_ids *: list[str]*

#### transactions *: list[[algokit_utils.models.transaction.TransactionWrapper](../../models/transaction/index.md#algokit_utils.models.transaction.TransactionWrapper)]*

#### returns *: list[[algokit_utils.applications.abi.ABIReturn](../../applications/abi/index.md#algokit_utils.applications.abi.ABIReturn)]*

#### simulate_response *: dict[str, Any] | None* *= None*

### algokit_utils.transactions.transaction_composer.send_atomic_transaction_composer(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer, algod: algosdk.v2client.algod.AlgodClient, \*, max_rounds_to_wait: int | None = 5, skip_waiting: bool = False, suppress_log: bool | None = None, populate_app_call_resources: bool | None = None, cover_app_call_inner_transaction_fees: bool | None = None, additional_atc_context: AdditionalAtcContext | None = None) → [SendAtomicTransactionComposerResults](#algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults)

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

### *class* algokit_utils.transactions.transaction_composer.TransactionComposer(algod: algosdk.v2client.algod.AlgodClient, get_signer: collections.abc.Callable[[str], algosdk.atomic_transaction_composer.TransactionSigner], get_suggested_params: collections.abc.Callable[[], algosdk.transaction.SuggestedParams] | None = None, default_validity_window: int | None = None, app_manager: [algokit_utils.applications.app_manager.AppManager](../../applications/app_manager/index.md#algokit_utils.applications.app_manager.AppManager) | None = None)

A class for composing and managing Algorand transactions.

Provides a high-level interface for building and executing transaction groups using the Algosdk library.
Supports various transaction types including payments, asset operations, application calls, and key registrations.

* **Parameters:**
  * **algod** – An instance of AlgodClient used to get suggested params and send transactions
  * **get_signer** – A function that takes an address and returns a TransactionSigner for that address
  * **get_suggested_params** – Optional function to get suggested transaction parameters,

defaults to using algod.suggested_params()
:param default_validity_window: Optional default validity window for transactions in rounds, defaults to 10
:param app_manager: Optional AppManager instance for compiling TEAL programs, defaults to None

#### add_transaction(transaction: algosdk.transaction.Transaction, signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add a raw transaction to the composer.

* **Parameters:**
  * **transaction** – The transaction to add
  * **signer** – Optional transaction signer, defaults to getting signer from transaction sender
* **Returns:**
  The transaction composer instance for chaining

#### add_payment(params: [PaymentParams](#algokit_utils.transactions.transaction_composer.PaymentParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add a payment transaction.

* **Parameters:**
  **params** – The payment transaction parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_create(params: [AssetCreateParams](#algokit_utils.transactions.transaction_composer.AssetCreateParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset creation transaction.

* **Parameters:**
  **params** – The asset creation parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_config(params: [AssetConfigParams](#algokit_utils.transactions.transaction_composer.AssetConfigParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset configuration transaction.

* **Parameters:**
  **params** – The asset configuration parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_freeze(params: [AssetFreezeParams](#algokit_utils.transactions.transaction_composer.AssetFreezeParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset freeze transaction.

* **Parameters:**
  **params** – The asset freeze parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_destroy(params: [AssetDestroyParams](#algokit_utils.transactions.transaction_composer.AssetDestroyParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset destruction transaction.

* **Parameters:**
  **params** – The asset destruction parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_transfer(params: [AssetTransferParams](#algokit_utils.transactions.transaction_composer.AssetTransferParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset transfer transaction.

* **Parameters:**
  **params** – The asset transfer parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_opt_in(params: [AssetOptInParams](#algokit_utils.transactions.transaction_composer.AssetOptInParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset opt-in transaction.

* **Parameters:**
  **params** – The asset opt-in parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_opt_out(params: [AssetOptOutParams](#algokit_utils.transactions.transaction_composer.AssetOptOutParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset opt-out transaction.

* **Parameters:**
  **params** – The asset opt-out parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_create(params: [AppCreateParams](#algokit_utils.transactions.transaction_composer.AppCreateParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application creation transaction.

* **Parameters:**
  **params** – The application creation parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_update(params: [AppUpdateParams](#algokit_utils.transactions.transaction_composer.AppUpdateParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application update transaction.

* **Parameters:**
  **params** – The application update parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_delete(params: [AppDeleteParams](#algokit_utils.transactions.transaction_composer.AppDeleteParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application deletion transaction.

* **Parameters:**
  **params** – The application deletion parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_call(params: [AppCallParams](#algokit_utils.transactions.transaction_composer.AppCallParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application call transaction.

* **Parameters:**
  **params** – The application call parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_create_method_call(params: [AppCreateMethodCallParams](#algokit_utils.transactions.transaction_composer.AppCreateMethodCallParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application creation method call transaction.

* **Parameters:**
  **params** – The application creation method call parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_update_method_call(params: [AppUpdateMethodCallParams](#algokit_utils.transactions.transaction_composer.AppUpdateMethodCallParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application update method call transaction.

* **Parameters:**
  **params** – The application update method call parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_delete_method_call(params: [AppDeleteMethodCallParams](#algokit_utils.transactions.transaction_composer.AppDeleteMethodCallParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application deletion method call transaction.

* **Parameters:**
  **params** – The application deletion method call parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_call_method_call(params: [AppCallMethodCallParams](#algokit_utils.transactions.transaction_composer.AppCallMethodCallParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application call method call transaction.

* **Parameters:**
  **params** – The application call method call parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_online_key_registration(params: [OnlineKeyRegistrationParams](#algokit_utils.transactions.transaction_composer.OnlineKeyRegistrationParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an online key registration transaction.

* **Parameters:**
  **params** – The online key registration parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_offline_key_registration(params: [OfflineKeyRegistrationParams](#algokit_utils.transactions.transaction_composer.OfflineKeyRegistrationParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an offline key registration transaction.

* **Parameters:**
  **params** – The offline key registration parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_atc(atc: algosdk.atomic_transaction_composer.AtomicTransactionComposer) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an existing AtomicTransactionComposer’s transactions.

* **Parameters:**
  **atc** – The AtomicTransactionComposer to add
* **Returns:**
  The transaction composer instance for chaining

#### count() → int

Get the total number of transactions.

* **Returns:**
  The number of transactions

#### build() → [TransactionComposerBuildResult](#algokit_utils.transactions.transaction_composer.TransactionComposerBuildResult)

Build the transaction group.

* **Returns:**
  The built transaction group result

#### rebuild() → [TransactionComposerBuildResult](#algokit_utils.transactions.transaction_composer.TransactionComposerBuildResult)

Rebuild the transaction group from scratch.

* **Returns:**
  The rebuilt transaction group result

#### build_transactions() → [BuiltTransactions](#algokit_utils.transactions.transaction_composer.BuiltTransactions)

Build and return the transactions without executing them.

* **Returns:**
  The built transactions result

#### execute(\*, max_rounds_to_wait: int | None = None) → [SendAtomicTransactionComposerResults](#algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults)

#### send(params: [algokit_utils.models.transaction.SendParams](../../models/transaction/index.md#algokit_utils.models.transaction.SendParams) | None = None) → [SendAtomicTransactionComposerResults](#algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults)

Send the transaction group to the network.

* **Parameters:**
  **params** – Parameters for the send operation
* **Returns:**
  The transaction send results
* **Raises:**
  **Exception** – If the transaction fails

#### simulate(allow_more_logs: bool | None = None, allow_empty_signatures: bool | None = None, allow_unnamed_resources: bool | None = None, extra_opcode_budget: int | None = None, exec_trace_config: algosdk.v2client.models.SimulateTraceConfig | None = None, simulation_round: int | None = None, skip_signatures: bool | None = None) → [SendAtomicTransactionComposerResults](#algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults)

Simulate transaction group execution with configurable validation rules.

* **Parameters:**
  * **allow_more_logs** – Whether to allow more logs than the standard limit
  * **allow_empty_signatures** – Whether to allow transactions with empty signatures
  * **allow_unnamed_resources** – Whether to allow unnamed resources
  * **extra_opcode_budget** – Additional opcode budget to allocate
  * **exec_trace_config** – Configuration for execution tracing
  * **simulation_round** – Round number to simulate at
  * **skip_signatures** – Whether to skip signature validation
* **Returns:**
  The simulation results

#### *static* arc2_note(note: algokit_utils.models.transaction.Arc2TransactionNote) → bytes

Create an encoded transaction note that follows the ARC-2 spec.

[https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0002.md](https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0002.md)

* **Parameters:**
  **note** – The ARC-2 note to encode
* **Returns:**
  The encoded note bytes
* **Raises:**
  **ValueError** – If the dapp_name is invalid
