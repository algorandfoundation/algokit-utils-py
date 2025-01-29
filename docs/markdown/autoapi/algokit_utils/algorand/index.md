# algokit_utils.algorand

## Classes

| [`AlgorandClient`](#algokit_utils.algorand.AlgorandClient)   | A client that brokers easy access to Algorand functionality.   |
|--------------------------------------------------------------|----------------------------------------------------------------|

## Module Contents

### *class* algokit_utils.algorand.AlgorandClient(config: [algokit_utils.models.network.AlgoClientConfigs](../models/network/index.md#algokit_utils.models.network.AlgoClientConfigs) | [algokit_utils.clients.client_manager.AlgoSdkClients](../clients/client_manager/index.md#algokit_utils.clients.client_manager.AlgoSdkClients))

A client that brokers easy access to Algorand functionality.

#### set_default_validity_window(validity_window: int) → typing_extensions.Self

Sets the default validity window for transactions.

* **Parameters:**
  **validity_window** – The number of rounds between the first and last valid rounds
* **Returns:**
  The AlgorandClient so method calls can be chained

#### set_default_signer(signer: algosdk.atomic_transaction_composer.TransactionSigner | [algokit_utils.protocols.account.TransactionSignerAccountProtocol](../protocols/account/index.md#algokit_utils.protocols.account.TransactionSignerAccountProtocol)) → typing_extensions.Self

Sets the default signer to use if no other signer is specified.

* **Parameters:**
  **signer** – The signer to use, either a TransactionSigner or a TransactionSignerAccountProtocol
* **Returns:**
  The AlgorandClient so method calls can be chained

#### set_signer(sender: str, signer: algosdk.atomic_transaction_composer.TransactionSigner) → typing_extensions.Self

Tracks the given account for later signing.

* **Parameters:**
  * **sender** – The sender address to use this signer for
  * **signer** – The signer to sign transactions with for the given sender
* **Returns:**
  The AlgorandClient so method calls can be chained

#### set_signer_account(signer: [algokit_utils.protocols.account.TransactionSignerAccountProtocol](../protocols/account/index.md#algokit_utils.protocols.account.TransactionSignerAccountProtocol)) → typing_extensions.Self

Sets the default signer to use if no other signer is specified.

* **Parameters:**
  **signer** – The signer to use, either a TransactionSigner or a TransactionSignerAccountProtocol
* **Returns:**
  The AlgorandClient so method calls can be chained

#### set_suggested_params(suggested_params: algosdk.transaction.SuggestedParams, until: float | None = None) → typing_extensions.Self

Sets a cache value to use for suggested params.

* **Parameters:**
  * **suggested_params** – The suggested params to use
  * **until** – A timestamp until which to cache, or if not specified then the timeout is used
* **Returns:**
  The AlgorandClient so method calls can be chained

#### set_suggested_params_timeout(timeout: int) → typing_extensions.Self

Sets the timeout for caching suggested params.

* **Parameters:**
  **timeout** – The timeout in milliseconds
* **Returns:**
  The AlgorandClient so method calls can be chained

#### get_suggested_params() → algosdk.transaction.SuggestedParams

Get suggested params for a transaction (either cached or from algod if the cache is stale or empty)

#### new_group() → [algokit_utils.transactions.transaction_composer.TransactionComposer](../transactions/transaction_composer/index.md#algokit_utils.transactions.transaction_composer.TransactionComposer)

Start a new TransactionComposer transaction group

#### *property* client *: [algokit_utils.clients.client_manager.ClientManager](../clients/client_manager/index.md#algokit_utils.clients.client_manager.ClientManager)*

Get clients, including algosdk clients and app clients.

#### *property* account *: [algokit_utils.accounts.account_manager.AccountManager](../accounts/account_manager/index.md#algokit_utils.accounts.account_manager.AccountManager)*

Get or create accounts that can sign transactions.

#### *property* asset *: [algokit_utils.assets.asset_manager.AssetManager](../assets/asset_manager/index.md#algokit_utils.assets.asset_manager.AssetManager)*

Get or create assets.

#### *property* app *: [algokit_utils.applications.app_manager.AppManager](../applications/app_manager/index.md#algokit_utils.applications.app_manager.AppManager)*

#### *property* app_deployer *: [algokit_utils.applications.app_deployer.AppDeployer](../applications/app_deployer/index.md#algokit_utils.applications.app_deployer.AppDeployer)*

Get or create applications.

#### *property* send *: [algokit_utils.transactions.transaction_sender.AlgorandClientTransactionSender](../transactions/transaction_sender/index.md#algokit_utils.transactions.transaction_sender.AlgorandClientTransactionSender)*

Methods for sending a transaction and waiting for confirmation

#### *property* create_transaction *: [algokit_utils.transactions.transaction_creator.AlgorandClientTransactionCreator](../transactions/transaction_creator/index.md#algokit_utils.transactions.transaction_creator.AlgorandClientTransactionCreator)*

Methods for building transactions

#### *static* default_localnet() → [AlgorandClient](#algokit_utils.algorand.AlgorandClient)

Returns an AlgorandClient pointing at default LocalNet ports and API token.

* **Returns:**
  The AlgorandClient

#### *static* testnet() → [AlgorandClient](#algokit_utils.algorand.AlgorandClient)

Returns an AlgorandClient pointing at TestNet using AlgoNode.

* **Returns:**
  The AlgorandClient

#### *static* mainnet() → [AlgorandClient](#algokit_utils.algorand.AlgorandClient)

Returns an AlgorandClient pointing at MainNet using AlgoNode.

* **Returns:**
  The AlgorandClient

#### *static* from_clients(algod: algosdk.v2client.algod.AlgodClient, indexer: algosdk.v2client.indexer.IndexerClient | None = None, kmd: algosdk.kmd.KMDClient | None = None) → [AlgorandClient](#algokit_utils.algorand.AlgorandClient)

Returns an AlgorandClient pointing to the given client(s).

* **Parameters:**
  * **algod** – The algod client to use
  * **indexer** – The indexer client to use
  * **kmd** – The kmd client to use
* **Returns:**
  The AlgorandClient

#### *static* from_environment() → [AlgorandClient](#algokit_utils.algorand.AlgorandClient)

Returns an AlgorandClient loading the configuration from environment variables.

Retrieve configurations from environment variables when defined or get defaults.

Expects to be called from a Python environment.

* **Returns:**
  The AlgorandClient

#### *static* from_config(algod_config: [algokit_utils.models.network.AlgoClientNetworkConfig](../models/network/index.md#algokit_utils.models.network.AlgoClientNetworkConfig), indexer_config: [algokit_utils.models.network.AlgoClientNetworkConfig](../models/network/index.md#algokit_utils.models.network.AlgoClientNetworkConfig) | None = None, kmd_config: [algokit_utils.models.network.AlgoClientNetworkConfig](../models/network/index.md#algokit_utils.models.network.AlgoClientNetworkConfig) | None = None) → [AlgorandClient](#algokit_utils.algorand.AlgorandClient)

Returns an AlgorandClient from the given config.

* **Parameters:**
  * **algod_config** – The config to use for the algod client
  * **indexer_config** – The config to use for the indexer client
  * **kmd_config** – The config to use for the kmd client
* **Returns:**
  The AlgorandClient
