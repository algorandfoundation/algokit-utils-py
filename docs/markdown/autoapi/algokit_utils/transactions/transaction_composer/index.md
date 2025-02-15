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

| [`calculate_extra_program_pages`](#algokit_utils.transactions.transaction_composer.calculate_extra_program_pages)(→ int)     | Calculate minimum number of extra_pages required for provided approval and clear programs   |
|------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| [`populate_app_call_resources`](#algokit_utils.transactions.transaction_composer.populate_app_call_resources)(...)           | Populate application call resources based on simulation results.                            |
| [`prepare_group_for_sending`](#algokit_utils.transactions.transaction_composer.prepare_group_for_sending)(...)               | Prepare a transaction group for sending by handling execution info and resources.           |
| [`send_atomic_transaction_composer`](#algokit_utils.transactions.transaction_composer.send_atomic_transaction_composer)(...) | Send an AtomicTransactionComposer transaction group.                                        |

## Module Contents

### *class* algokit_utils.transactions.transaction_composer.PaymentParams

Bases: `_CommonTxnParams`

Parameters for a payment transaction.

#### receiver *: str*

The account that will receive the ALGO

#### amount *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount)*

Amount to send

#### close_remainder_to *: str | None* *= None*

If given, close the sender account and send the remaining balance to this address, defaults to None

### *class* algokit_utils.transactions.transaction_composer.AssetCreateParams

Bases: `_CommonTxnParams`

Parameters for creating a new asset.

#### total *: int*

The total amount of the smallest divisible unit to create

#### asset_name *: str | None* *= None*

The full name of the asset

#### unit_name *: str | None* *= None*

The short ticker name for the asset

#### url *: str | None* *= None*

The metadata URL for the asset

#### decimals *: int | None* *= None*

The amount of decimal places the asset should have

#### default_frozen *: bool | None* *= None*

Whether the asset is frozen by default in the creator address

#### manager *: str | None* *= None*

The address that can change the manager, reserve, clawback, and freeze addresses

#### reserve *: str | None* *= None*

The address that holds the uncirculated supply

#### freeze *: str | None* *= None*

The address that can freeze the asset in any account

#### clawback *: str | None* *= None*

The address that can clawback the asset from any account

#### metadata_hash *: bytes | None* *= None*

Hash of the metadata contained in the metadata URL

### *class* algokit_utils.transactions.transaction_composer.AssetConfigParams

Bases: `_CommonTxnParams`

Parameters for configuring an existing asset.

#### asset_id *: int*

The ID of the asset

#### manager *: str | None* *= None*

The address that can change the manager, reserve, clawback, and freeze addresses, defaults to None

#### reserve *: str | None* *= None*

The address that holds the uncirculated supply, defaults to None

#### freeze *: str | None* *= None*

The address that can freeze the asset in any account, defaults to None

#### clawback *: str | None* *= None*

The address that can clawback the asset from any account, defaults to None

### *class* algokit_utils.transactions.transaction_composer.AssetFreezeParams

Bases: `_CommonTxnParams`

Parameters for freezing an asset.

#### asset_id *: int*

The ID of the asset

#### account *: str*

The account to freeze or unfreeze

#### frozen *: bool*

Whether the assets in the account should be frozen

### *class* algokit_utils.transactions.transaction_composer.AssetDestroyParams

Bases: `_CommonTxnParams`

Parameters for destroying an asset.

#### asset_id *: int*

The ID of the asset

### *class* algokit_utils.transactions.transaction_composer.OnlineKeyRegistrationParams

Bases: `_CommonTxnParams`

Parameters for online key registration.

#### vote_key *: str*

The root participation public key

#### selection_key *: str*

The VRF public key

#### vote_first *: int*

The first round that the participation key is valid

#### vote_last *: int*

The last round that the participation key is valid

#### vote_key_dilution *: int*

The dilution for the 2-level participation key

#### state_proof_key *: bytes | None* *= None*

The 64 byte state proof public key commitment, defaults to None

### *class* algokit_utils.transactions.transaction_composer.OfflineKeyRegistrationParams

Bases: `_CommonTxnParams`

Parameters for offline key registration.

#### prevent_account_from_ever_participating_again *: bool*

Whether to prevent the account from ever participating again

### *class* algokit_utils.transactions.transaction_composer.AssetTransferParams

Bases: `_CommonTxnParams`

Parameters for transferring an asset.

#### asset_id *: int*

The ID of the asset

#### amount *: int*

The amount of the asset to transfer (smallest divisible unit)

#### receiver *: str*

The account to send the asset to

#### clawback_target *: str | None* *= None*

The account to take the asset from, defaults to None

#### close_asset_to *: str | None* *= None*

The account to close the asset to, defaults to None

### *class* algokit_utils.transactions.transaction_composer.AssetOptInParams

Bases: `_CommonTxnParams`

Parameters for opting into an asset.

#### asset_id *: int*

The ID of the asset

### *class* algokit_utils.transactions.transaction_composer.AssetOptOutParams

Bases: `_CommonTxnParams`

Parameters for opting out of an asset.

#### asset_id *: int*

The ID of the asset

#### creator *: str*

The creator address of the asset

### *class* algokit_utils.transactions.transaction_composer.AppCallParams

Bases: `_CommonTxnParams`

Parameters for calling an application.

#### on_complete *: algosdk.transaction.OnComplete*

The OnComplete action, defaults to None

#### app_id *: int | None* *= None*

The ID of the application, defaults to None

#### approval_program *: str | bytes | None* *= None*

The program to execute for all OnCompletes other than ClearState, defaults to None

#### clear_state_program *: str | bytes | None* *= None*

The program to execute for ClearState OnComplete, defaults to None

#### schema *: dict[str, int] | None* *= None*

The state schema for the app, defaults to None

#### args *: list[bytes] | None* *= None*

Application arguments, defaults to None

#### account_references *: list[str] | None* *= None*

Account references, defaults to None

#### app_references *: list[int] | None* *= None*

App references, defaults to None

#### asset_references *: list[int] | None* *= None*

Asset references, defaults to None

#### extra_pages *: int | None* *= None*

Number of extra pages required for the programs, defaults to None

#### box_references *: list[[algokit_utils.models.state.BoxReference](../../models/state/index.md#algokit_utils.models.state.BoxReference) | algokit_utils.models.state.BoxIdentifier] | None* *= None*

Box references, defaults to None

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

The number of global ints in the schema

#### global_byte_slices *: int*

The number of global byte slices in the schema

#### local_ints *: int*

The number of local ints in the schema

#### local_byte_slices *: int*

The number of local byte slices in the schema

### *class* algokit_utils.transactions.transaction_composer.AppCreateParams

Bases: `_CommonTxnParams`

Parameters for creating an application.

#### approval_program *: str | bytes*

The program to execute for all OnCompletes other than ClearState

#### clear_state_program *: str | bytes*

The program to execute for ClearState OnComplete

#### schema *: [AppCreateSchema](#algokit_utils.transactions.transaction_composer.AppCreateSchema) | None* *= None*

The state schema for the app, defaults to None

#### on_complete *: algosdk.transaction.OnComplete | None* *= None*

The OnComplete action, defaults to None

#### args *: list[bytes] | None* *= None*

Application arguments, defaults to None

#### account_references *: list[str] | None* *= None*

Account references, defaults to None

#### app_references *: list[int] | None* *= None*

App references, defaults to None

#### asset_references *: list[int] | None* *= None*

Asset references, defaults to None

#### box_references *: list[[algokit_utils.models.state.BoxReference](../../models/state/index.md#algokit_utils.models.state.BoxReference) | algokit_utils.models.state.BoxIdentifier] | None* *= None*

Box references, defaults to None

#### extra_program_pages *: int | None* *= None*

Number of extra pages required for the programs, defaults to None

### *class* algokit_utils.transactions.transaction_composer.AppUpdateParams

Bases: `_CommonTxnParams`

Parameters for updating an application.

#### app_id *: int*

The ID of the application

#### approval_program *: str | bytes*

The program to execute for all OnCompletes other than ClearState

#### clear_state_program *: str | bytes*

The program to execute for ClearState OnComplete

#### args *: list[bytes] | None* *= None*

Application arguments, defaults to None

#### account_references *: list[str] | None* *= None*

Account references, defaults to None

#### app_references *: list[int] | None* *= None*

App references, defaults to None

#### asset_references *: list[int] | None* *= None*

Asset references, defaults to None

#### box_references *: list[[algokit_utils.models.state.BoxReference](../../models/state/index.md#algokit_utils.models.state.BoxReference) | algokit_utils.models.state.BoxIdentifier] | None* *= None*

Box references, defaults to None

#### on_complete *: algosdk.transaction.OnComplete | None* *= None*

The OnComplete action, defaults to None

### *class* algokit_utils.transactions.transaction_composer.AppDeleteParams

Bases: `_CommonTxnParams`

Parameters for deleting an application.

#### app_id *: int*

The ID of the application

#### args *: list[bytes] | None* *= None*

Application arguments, defaults to None

#### account_references *: list[str] | None* *= None*

Account references, defaults to None

#### app_references *: list[int] | None* *= None*

App references, defaults to None

#### asset_references *: list[int] | None* *= None*

Asset references, defaults to None

#### box_references *: list[[algokit_utils.models.state.BoxReference](../../models/state/index.md#algokit_utils.models.state.BoxReference) | algokit_utils.models.state.BoxIdentifier] | None* *= None*

Box references, defaults to None

#### on_complete *: algosdk.transaction.OnComplete*

The OnComplete action, defaults to DeleteApplicationOC

### *class* algokit_utils.transactions.transaction_composer.AppCallMethodCallParams

Bases: `_BaseAppMethodCall`

Parameters for a regular ABI method call.

#### app_id *: int*

The ID of the application

#### on_complete *: algosdk.transaction.OnComplete | None* *= None*

The OnComplete action, defaults to None

### *class* algokit_utils.transactions.transaction_composer.AppCreateMethodCallParams

Bases: `_BaseAppMethodCall`

Parameters for an ABI method call that creates an application.

#### approval_program *: str | bytes*

The program to execute for all OnCompletes other than ClearState

#### clear_state_program *: str | bytes*

The program to execute for ClearState OnComplete

#### schema *: [AppCreateSchema](#algokit_utils.transactions.transaction_composer.AppCreateSchema) | None* *= None*

The state schema for the app, defaults to None

#### on_complete *: algosdk.transaction.OnComplete | None* *= None*

The OnComplete action (cannot be ClearState), defaults to None

#### extra_program_pages *: int | None* *= None*

Number of extra pages required for the programs, defaults to None

### *class* algokit_utils.transactions.transaction_composer.AppUpdateMethodCallParams

Bases: `_BaseAppMethodCall`

Parameters for an ABI method call that updates an application.

#### app_id *: int*

The ID of the application

#### approval_program *: str | bytes*

The program to execute for all OnCompletes other than ClearState

#### clear_state_program *: str | bytes*

The program to execute for ClearState OnComplete

#### on_complete *: algosdk.transaction.OnComplete*

The OnComplete action

### *class* algokit_utils.transactions.transaction_composer.AppDeleteMethodCallParams

Bases: `_BaseAppMethodCall`

Parameters for an ABI method call that deletes an application.

#### app_id *: int*

The ID of the application

#### on_complete *: algosdk.transaction.OnComplete*

The OnComplete action

### algokit_utils.transactions.transaction_composer.MethodCallParams

### algokit_utils.transactions.transaction_composer.AppMethodCallTransactionArgument

### algokit_utils.transactions.transaction_composer.TxnParams

### *class* algokit_utils.transactions.transaction_composer.BuiltTransactions

Set of transactions built by TransactionComposer.

#### transactions *: list[algosdk.transaction.Transaction]*

The built transactions

#### method_calls *: dict[int, algosdk.abi.Method]*

Map of transaction index to ABI method

#### signers *: dict[int, algosdk.atomic_transaction_composer.TransactionSigner]*

Map of transaction index to TransactionSigner

### *class* algokit_utils.transactions.transaction_composer.TransactionComposerBuildResult

Result of building transactions with TransactionComposer.

#### atc *: algosdk.atomic_transaction_composer.AtomicTransactionComposer*

The AtomicTransactionComposer instance

#### transactions *: list[algosdk.atomic_transaction_composer.TransactionWithSigner]*

The list of transactions with signers

#### method_calls *: dict[int, algosdk.abi.Method]*

Map of transaction index to ABI method

### *class* algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults

Results from sending an AtomicTransactionComposer transaction group.

#### group_id *: str*

The group ID if this was a transaction group

#### confirmations *: list[algosdk.v2client.algod.AlgodResponseType]*

The confirmation info for each transaction

#### tx_ids *: list[str]*

The transaction IDs that were sent

#### transactions *: list[[algokit_utils.models.transaction.TransactionWrapper](../../models/transaction/index.md#algokit_utils.models.transaction.TransactionWrapper)]*

The transactions that were sent

#### returns *: list[[algokit_utils.applications.abi.ABIReturn](../../applications/abi/index.md#algokit_utils.applications.abi.ABIReturn)]*

The ABI return values from any ABI method calls

#### simulate_response *: dict[str, Any] | None* *= None*

The simulation response if simulation was performed, defaults to None

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

Prepare a transaction group for sending by handling execution info and resources.

* **Parameters:**
  * **atc** – The AtomicTransactionComposer containing transactions
  * **algod** – Algod client for simulation
  * **populate_app_call_resources** – Whether to populate app call resources
  * **cover_app_call_inner_transaction_fees** – Whether to cover inner txn fees
  * **additional_atc_context** – Additional context for the AtomicTransactionComposer
* **Returns:**
  Modified AtomicTransactionComposer ready for sending

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
  * **default_validity_window** – Optional default validity window for transactions in rounds, defaults to 10
  * **app_manager** – Optional AppManager instance for compiling TEAL programs, defaults to None

#### add_transaction(transaction: algosdk.transaction.Transaction, signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add a raw transaction to the composer.

* **Parameters:**
  * **transaction** – The transaction to add
  * **signer** – Optional transaction signer, defaults to getting signer from transaction sender
* **Returns:**
  The transaction composer instance for chaining
* **Example:**
  ```pycon
  >>> composer.add_transaction(transaction)
  ```

#### add_payment(params: [PaymentParams](#algokit_utils.transactions.transaction_composer.PaymentParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add a payment transaction.

* **Example:**
  ```pycon
  >>> params = PaymentParams(
  ...     sender="SENDER_ADDRESS",
  ...     receiver="RECEIVER_ADDRESS",
  ...     amount=AlgoAmount.from_algo(1),
  ...     close_remainder_to="CLOSE_ADDRESS"
  ...     ... (see PaymentParams for more options)
  ... )
  >>> composer.add_payment(params)
  ```
* **Parameters:**
  **params** – The payment transaction parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_create(params: [AssetCreateParams](#algokit_utils.transactions.transaction_composer.AssetCreateParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset creation transaction.

* **Example:**
  ```pycon
  >>> params = AssetCreateParams(
  ...     sender="SENDER_ADDRESS",
  ...     total=1000,
  ...     asset_name="MyAsset",
  ...     unit_name="MA",
  ...     url="https://example.com",
  ...     decimals=0,
  ...     default_frozen=False,
  ...     manager="MANAGER_ADDRESS",
  ...     reserve="RESERVE_ADDRESS",
  ...     freeze="FREEZE_ADDRESS",
  ...     clawback="CLAWBACK_ADDRESS"
  ...     ... (see AssetCreateParams for more options)
  >>> composer.add_asset_create(params)
  ```
* **Parameters:**
  **params** – The asset creation parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_config(params: [AssetConfigParams](#algokit_utils.transactions.transaction_composer.AssetConfigParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset configuration transaction.

* **Example:**
  ```pycon
  >>> params = AssetConfigParams(
  ...     sender="SENDER_ADDRESS",
  ...     asset_id=123456,
  ...     manager="NEW_MANAGER_ADDRESS",
  ...     reserve="NEW_RESERVE_ADDRESS",
  ...     freeze="NEW_FREEZE_ADDRESS",
  ...     clawback="NEW_CLAWBACK_ADDRESS"
  ...     ... (see AssetConfigParams for more options)
  ... )
  >>> composer.add_asset_config(params)
  ```
* **Parameters:**
  **params** – The asset configuration parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_freeze(params: [AssetFreezeParams](#algokit_utils.transactions.transaction_composer.AssetFreezeParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset freeze transaction.

* **Example:**
  ```pycon
  >>> params = AssetFreezeParams(
  ...     sender="SENDER_ADDRESS",
  ...     asset_id=123456,
  ...     account="ACCOUNT_TO_FREEZE",
  ...     frozen=True
  ...     ... (see AssetFreezeParams for more options)
  ... )
  >>> composer.add_asset_freeze(params)
  ```
* **Parameters:**
  **params** – The asset freeze parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_destroy(params: [AssetDestroyParams](#algokit_utils.transactions.transaction_composer.AssetDestroyParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset destruction transaction.

* **Example:**
  ```pycon
  >>> params = AssetDestroyParams(
  ...     sender="SENDER_ADDRESS",
  ...     asset_id=123456
  ...     ... (see AssetDestroyParams for more options)
  >>> composer.add_asset_destroy(params)
  ```
* **Parameters:**
  **params** – The asset destruction parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_transfer(params: [AssetTransferParams](#algokit_utils.transactions.transaction_composer.AssetTransferParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset transfer transaction.

* **Example:**
  ```pycon
  >>> params = AssetTransferParams(
  ...     sender="SENDER_ADDRESS",
  ...     asset_id=123456,
  ...     amount=10,
  ...     receiver="RECEIVER_ADDRESS",
  ...     clawback_target="CLAWBACK_TARGET_ADDRESS",
  ...     close_asset_to="CLOSE_ADDRESS"
  ...     ... (see AssetTransferParams for more options)
  >>> composer.add_asset_transfer(params)
  ```
* **Parameters:**
  **params** – The asset transfer parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_opt_in(params: [AssetOptInParams](#algokit_utils.transactions.transaction_composer.AssetOptInParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset opt-in transaction.

* **Example:**
  ```pycon
  >>> params = AssetOptInParams(
  ...     sender="SENDER_ADDRESS",
  ...     asset_id=123456
  ...     ... (see AssetOptInParams for more options)
  ... )
  >>> composer.add_asset_opt_in(params)
  ```
* **Parameters:**
  **params** – The asset opt-in parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_asset_opt_out(params: [AssetOptOutParams](#algokit_utils.transactions.transaction_composer.AssetOptOutParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an asset opt-out transaction.

* **Example:**
  ```pycon
  >>> params = AssetOptOutParams(
  ...     sender="SENDER_ADDRESS",
  ...     asset_id=123456,
  ...     creator="CREATOR_ADDRESS"
  ...     ... (see AssetOptOutParams for more options)
  >>> composer.add_asset_opt_out(params)
  ```
* **Parameters:**
  **params** – The asset opt-out parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_create(params: [AppCreateParams](#algokit_utils.transactions.transaction_composer.AppCreateParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application creation transaction.

* **Example:**
  ```pycon
  >>> params = AppCreateParams(
  ...     sender="SENDER_ADDRESS",
  ...     approval_program="TEAL_APPROVAL_CODE",
  ...     clear_state_program="TEAL_CLEAR_CODE",
  ...     schema={'global_ints': 1, 'global_byte_slices': 1, 'local_ints': 1, 'local_byte_slices': 1},
  ...     on_complete=OnComplete.NoOpOC,
  ...     args=[b'arg1'],
  ...     account_references=["ACCOUNT1"],
  ...     app_references=[789],
  ...     asset_references=[123],
  ...     box_references=[],
  ...     extra_program_pages=0
  ...     ... (see AppCreateParams for more options)
  ... )
  >>> composer.add_app_create(params)
  ```
* **Parameters:**
  **params** – The application creation parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_update(params: [AppUpdateParams](#algokit_utils.transactions.transaction_composer.AppUpdateParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application update transaction.

* **Example:**
  ```pycon
  >>> params = AppUpdateParams(
  ...     sender="SENDER_ADDRESS",
  ...     app_id=789,
  ...     approval_program="TEAL_NEW_APPROVAL_CODE",
  ...     clear_state_program="TEAL_NEW_CLEAR_CODE",
  ...     args=[b'new_arg1'],
  ...     account_references=["ACCOUNT1"],
  ...     app_references=[789],
  ...     asset_references=[123],
  ...     box_references=[],
  ...     on_complete=OnComplete.UpdateApplicationOC
  ...     ... (see AppUpdateParams for more options)
  >>> composer.add_app_update(params)
  ```
* **Parameters:**
  **params** – The application update parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_delete(params: [AppDeleteParams](#algokit_utils.transactions.transaction_composer.AppDeleteParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application deletion transaction.

* **Example:**
  ```pycon
  >>> params = AppDeleteParams(
  ...     sender="SENDER_ADDRESS",
  ...     app_id=789,
  ...     args=[b'delete_arg'],
  ...     account_references=["ACCOUNT1"],
  ...     app_references=[789],
  ...     asset_references=[123],
  ...     box_references=[],
  ...     on_complete=OnComplete.DeleteApplicationOC
  ...     ... (see AppDeleteParams for more options)
  >>> composer.add_app_delete(params)
  ```
* **Parameters:**
  **params** – The application deletion parameters
* **Returns:**
  The transaction composer instance for chaining

#### add_app_call(params: [AppCallParams](#algokit_utils.transactions.transaction_composer.AppCallParams)) → [TransactionComposer](#algokit_utils.transactions.transaction_composer.TransactionComposer)

Add an application call transaction.

* **Example:**
  ```pycon
  >>> params = AppCallParams(
  ...     sender="SENDER_ADDRESS",
  ...     on_complete=OnComplete.NoOpOC,
  ...     app_id=789,
  ...     approval_program="TEAL_APPROVAL_CODE",
  ...     clear_state_program="TEAL_CLEAR_CODE",
  ...     schema={'global_ints': 1, 'global_byte_slices': 1, 'local_ints': 1, 'local_byte_slices': 1},
  ...     ... (see AppCallParams for more options)
  ... )
  >>> composer.add_app_call(params)
  ```
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
* **Example:**
  ```pycon
  >>> # Basic example
  >>> method = algosdk.abi.Method(
  ...     name="method",
  ...     args=[...],
  ...     returns="string"
  ... )
  >>> composer.add_app_create_method_call(
  ...     AppCreateMethodCallParams(
  ...         sender="CREATORADDRESS",
  ...         approval_program="TEALCODE",
  ...         clear_state_program="TEALCODE",
  ...         method=method,
  ...         args=["arg1_value"]
  ...     )
  ... )
  >>>
  >>> # Advanced example
  >>> method = ABIMethod(
  ...     name="method",
  ...     args=[{"name": "arg1", "type": "string"}],
  ...     returns={"type": "string"}
  ... )
  >>> composer.add_app_create_method_call(
  ...     AppCreateMethodCallParams(
  ...         sender="CREATORADDRESS",
  ...         method=method,
  ...         args=["arg1_value"],
  ...         approval_program="TEALCODE",
  ...         clear_state_program="TEALCODE",
  ...         schema={
  ...             "global_ints": 1,
  ...             "global_byte_slices": 2,
  ...             "local_ints": 3,
  ...             "local_byte_slices": 4
  ...         },
  ...         extra_pages=1,
  ...         on_complete=OnComplete.OptInOC,
  ...         args=[bytes([1, 2, 3, 4])],
  ...         account_references=["ACCOUNT_1"],
  ...         app_references=[123, 1234],
  ...         asset_references=[12345],
  ...         box_references=["box1", {"app_id": 1234, "name": "box2"}],
  ...         lease="lease",
  ...         note="note",
  ...         first_valid_round=1000,
  ...         validity_window=10,
  ...         extra_fee=AlgoAmount.from_micro_algos(1000),
  ...         static_fee=AlgoAmount.from_micro_algos(1000),
  ...         max_fee=AlgoAmount.from_micro_algos(3000)
  ...     )
  ... )
  ```

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
* **Example:**
  ```pycon
  >>> atc = AtomicTransactionComposer()
  >>> atc.add_transaction(TransactionWithSigner(transaction, signer))
  >>> composer.add_atc(atc)
  ```

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
  * **allow_unnamed_resources** – Whether to allow unnamed resources.
  * **extra_opcode_budget** – Additional opcode budget to allocate
  * **exec_trace_config** – Configuration for execution tracing
  * **simulation_round** – Round number to simulate at
  * **skip_signatures** – Whether to skip signature validation
* **Returns:**
  The simulation results
* **Example:**
  ```pycon
  >>> result = composer.simulate(extra_opcode_budget=1000, skip_signatures=True, ...)
  ```

#### *static* arc2_note(note: algokit_utils.models.transaction.Arc2TransactionNote) → bytes

Create an encoded transaction note that follows the ARC-2 spec.

[https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0002.md](https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0002.md)

* **Parameters:**
  **note** – The ARC-2 note to encode
* **Returns:**
  The encoded note bytes
* **Raises:**
  **ValueError** – If the dapp_name is invalid
