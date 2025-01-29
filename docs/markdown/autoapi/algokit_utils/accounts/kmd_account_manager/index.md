# algokit_utils.accounts.kmd_account_manager

## Classes

| [`KmdAccount`](#algokit_utils.accounts.kmd_account_manager.KmdAccount)               | Account retrieved from KMD with signing capabilities, extending base Account.   |
|--------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| [`KmdAccountManager`](#algokit_utils.accounts.kmd_account_manager.KmdAccountManager) | Provides abstractions over KMD that makes it easier to get and manage accounts. |

## Module Contents

### *class* algokit_utils.accounts.kmd_account_manager.KmdAccount(private_key: str, address: str | None = None)

Bases: [`algokit_utils.models.account.SigningAccount`](../../models/account/index.md#algokit_utils.models.account.SigningAccount)

Account retrieved from KMD with signing capabilities, extending base Account.

Provides an account implementation that can be used to sign transactions using keys stored in KMD.

* **Parameters:**
  * **private_key** – Base64 encoded private key
  * **address** – Optional address override for rekeyed accounts, defaults to None

### *class* algokit_utils.accounts.kmd_account_manager.KmdAccountManager(client_manager: [algokit_utils.clients.client_manager.ClientManager](../../clients/client_manager/index.md#algokit_utils.clients.client_manager.ClientManager))

Provides abstractions over KMD that makes it easier to get and manage accounts.

#### kmd() → algosdk.kmd.KMDClient

Returns the KMD client, initializing it if needed.

* **Raises:**
  **Exception** – If KMD client is not configured and not running against LocalNet
* **Returns:**
  The KMD client

#### get_wallet_account(wallet_name: str, predicate: collections.abc.Callable[[dict[str, Any]], bool] | None = None, sender: str | None = None) → [KmdAccount](#algokit_utils.accounts.kmd_account_manager.KmdAccount) | None

Returns an Algorand signing account with private key loaded from the given KMD wallet.

Retrieves an account from a KMD wallet that matches the given predicate, or a random account
if no predicate is provided.

* **Parameters:**
  * **wallet_name** – The name of the wallet to retrieve an account from
  * **predicate** – Optional filter to use to find the account (otherwise gets a random account from the wallet)
  * **sender** – Optional sender address to use this signer for (aka a rekeyed account)
* **Returns:**
  The signing account or None if no matching wallet or account was found

#### get_or_create_wallet_account(name: str, fund_with: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None = None) → [KmdAccount](#algokit_utils.accounts.kmd_account_manager.KmdAccount)

Gets or creates a funded account in a KMD wallet of the given name.

Provides idempotent access to accounts from LocalNet without specifying the private key.

* **Parameters:**
  * **name** – The name of the wallet to retrieve / create
  * **fund_with** – The number of Algos to fund the account with when created
* **Returns:**
  An Algorand account with private key loaded

#### get_localnet_dispenser_account() → [KmdAccount](#algokit_utils.accounts.kmd_account_manager.KmdAccount)

Returns an Algorand account with private key loaded for the default LocalNet dispenser account.

Retrieves the default funded account from LocalNet that can be used to fund other accounts.

* **Raises:**
  **Exception** – If not running against LocalNet or dispenser account not found
* **Returns:**
  The default LocalNet dispenser account
