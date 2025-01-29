# algokit_utils.assets.asset_manager

## Classes

| [`AccountAssetInformation`](#algokit_utils.assets.asset_manager.AccountAssetInformation)   | Information about an account's holding of a particular asset.                                   |
|--------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| [`AssetInformation`](#algokit_utils.assets.asset_manager.AssetInformation)                 | Information about an Algorand Standard Asset (ASA).                                             |
| [`BulkAssetOptInOutResult`](#algokit_utils.assets.asset_manager.BulkAssetOptInOutResult)   | Result from performing a bulk opt-in or bulk opt-out for an account against a series of assets. |
| [`AssetManager`](#algokit_utils.assets.asset_manager.AssetManager)                         | A manager for Algorand Standard Assets (ASAs).                                                  |

## Module Contents

### *class* algokit_utils.assets.asset_manager.AccountAssetInformation

Information about an account’s holding of a particular asset.

* **Variables:**
  * **asset_id** – The ID of the asset
  * **balance** – The amount of the asset held by the account
  * **frozen** – Whether the asset is frozen for this account
  * **round** – The round this information was retrieved at

#### asset_id *: int*

#### balance *: int*

#### frozen *: bool*

#### round *: int*

### *class* algokit_utils.assets.asset_manager.AssetInformation

Information about an Algorand Standard Asset (ASA).

* **Variables:**
  * **asset_id** – The ID of the asset
  * **creator** – The address of the account that created the asset
  * **total** – The total amount of the smallest divisible units that were created of the asset
  * **decimals** – The amount of decimal places the asset was created with
  * **default_frozen** – Whether the asset was frozen by default for all accounts, defaults to None
  * **manager** – The address of the optional account that can manage the configuration of the asset and destroy it,

defaults to None
:ivar reserve: The address of the optional account that holds the reserve (uncirculated supply) units of the asset,
defaults to None
:ivar freeze: The address of the optional account that can be used to freeze or unfreeze holdings of this asset,
defaults to None
:ivar clawback: The address of the optional account that can clawback holdings of this asset from any account,
defaults to None
:ivar unit_name: The optional name of the unit of this asset (e.g. ticker name), defaults to None
:ivar unit_name_b64: The optional name of the unit of this asset as bytes, defaults to None
:ivar asset_name: The optional name of the asset, defaults to None
:ivar asset_name_b64: The optional name of the asset as bytes, defaults to None
:ivar url: Optional URL where more information about the asset can be retrieved, defaults to None
:ivar url_b64: Optional URL where more information about the asset can be retrieved as bytes, defaults to None
:ivar metadata_hash: 32-byte hash of some metadata that is relevant to the asset and/or asset holders,
defaults to None

#### asset_id *: int*

#### creator *: str*

#### total *: int*

#### decimals *: int*

#### default_frozen *: bool | None* *= None*

#### manager *: str | None* *= None*

#### reserve *: str | None* *= None*

#### freeze *: str | None* *= None*

#### clawback *: str | None* *= None*

#### unit_name *: str | None* *= None*

#### unit_name_b64 *: bytes | None* *= None*

#### asset_name *: str | None* *= None*

#### asset_name_b64 *: bytes | None* *= None*

#### url *: str | None* *= None*

#### url_b64 *: bytes | None* *= None*

#### metadata_hash *: bytes | None* *= None*

### *class* algokit_utils.assets.asset_manager.BulkAssetOptInOutResult

Result from performing a bulk opt-in or bulk opt-out for an account against a series of assets.

* **Variables:**
  * **asset_id** – The ID of the asset opted into / out of
  * **transaction_id** – The transaction ID of the resulting opt in / out

#### asset_id *: int*

#### transaction_id *: str*

### *class* algokit_utils.assets.asset_manager.AssetManager(algod_client: algosdk.v2client.algod.AlgodClient, new_group: collections.abc.Callable[[], [algokit_utils.transactions.transaction_composer.TransactionComposer](../../transactions/transaction_composer/index.md#algokit_utils.transactions.transaction_composer.TransactionComposer)])

A manager for Algorand Standard Assets (ASAs).

* **Parameters:**
  * **algod_client** – An algod client
  * **new_group** – A function that creates a new TransactionComposer transaction group

#### get_by_id(asset_id: int) → [AssetInformation](#algokit_utils.assets.asset_manager.AssetInformation)

Returns the current asset information for the asset with the given ID.

* **Parameters:**
  **asset_id** – The ID of the asset
* **Returns:**
  The asset information

#### get_account_information(sender: str | [algokit_utils.models.account.SigningAccount](../../models/account/index.md#algokit_utils.models.account.SigningAccount) | algosdk.atomic_transaction_composer.TransactionSigner, asset_id: int) → [AccountAssetInformation](#algokit_utils.assets.asset_manager.AccountAssetInformation)

Returns the given sender account’s asset holding for a given asset.

* **Parameters:**
  * **sender** – The address of the sender/account to look up
  * **asset_id** – The ID of the asset to return a holding for
* **Returns:**
  The account asset holding information

#### bulk_opt_in(account: str, asset_ids: list[int], signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, rekey_to: str | None = None, note: bytes | None = None, lease: bytes | None = None, static_fee: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None = None, extra_fee: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None = None, max_fee: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None = None, validity_window: int | None = None, first_valid_round: int | None = None, last_valid_round: int | None = None, send_params: [algokit_utils.models.transaction.SendParams](../../models/transaction/index.md#algokit_utils.models.transaction.SendParams) | None = None) → list[[BulkAssetOptInOutResult](#algokit_utils.assets.asset_manager.BulkAssetOptInOutResult)]

Opt an account in to a list of Algorand Standard Assets.

* **Parameters:**
  * **account** – The account to opt-in
  * **asset_ids** – The list of asset IDs to opt-in to
  * **signer** – The signer to use for the transaction, defaults to None
  * **rekey_to** – The address to rekey the account to, defaults to None
  * **note** – The note to include in the transaction, defaults to None
  * **lease** – The lease to include in the transaction, defaults to None
  * **static_fee** – The static fee to include in the transaction, defaults to None
  * **extra_fee** – The extra fee to include in the transaction, defaults to None
  * **max_fee** – The maximum fee to include in the transaction, defaults to None
  * **validity_window** – The validity window to include in the transaction, defaults to None
  * **first_valid_round** – The first valid round to include in the transaction, defaults to None
  * **last_valid_round** – The last valid round to include in the transaction, defaults to None
  * **send_params** – The send parameters to use for the transaction, defaults to None
* **Returns:**
  An array of records matching asset ID to transaction ID of the opt in

#### bulk_opt_out(\*, account: str, asset_ids: list[int], ensure_zero_balance: bool = True, signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, rekey_to: str | None = None, note: bytes | None = None, lease: bytes | None = None, static_fee: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None = None, extra_fee: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None = None, max_fee: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None = None, validity_window: int | None = None, first_valid_round: int | None = None, last_valid_round: int | None = None, send_params: [algokit_utils.models.transaction.SendParams](../../models/transaction/index.md#algokit_utils.models.transaction.SendParams) | None = None) → list[[BulkAssetOptInOutResult](#algokit_utils.assets.asset_manager.BulkAssetOptInOutResult)]

Opt an account out of a list of Algorand Standard Assets.

* **Parameters:**
  * **account** – The account to opt-out
  * **asset_ids** – The list of asset IDs to opt-out of
  * **ensure_zero_balance** – Whether to check if the account has a zero balance first, defaults to True
  * **signer** – The signer to use for the transaction, defaults to None
  * **rekey_to** – The address to rekey the account to, defaults to None
  * **note** – The note to include in the transaction, defaults to None
  * **lease** – The lease to include in the transaction, defaults to None
  * **static_fee** – The static fee to include in the transaction, defaults to None
  * **extra_fee** – The extra fee to include in the transaction, defaults to None
  * **max_fee** – The maximum fee to include in the transaction, defaults to None
  * **validity_window** – The validity window to include in the transaction, defaults to None
  * **first_valid_round** – The first valid round to include in the transaction, defaults to None
  * **last_valid_round** – The last valid round to include in the transaction, defaults to None
  * **send_params** – The send parameters to use for the transaction, defaults to None
* **Raises:**
  **ValueError** – If ensure_zero_balance is True and account has non-zero balance or is not opted in
* **Returns:**
  An array of records matching asset ID to transaction ID of the opt out
