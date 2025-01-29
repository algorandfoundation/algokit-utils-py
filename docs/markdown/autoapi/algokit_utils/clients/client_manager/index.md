# algokit_utils.clients.client_manager

## Classes

| [`AlgoSdkClients`](#algokit_utils.clients.client_manager.AlgoSdkClients)   | Container for Algorand SDK client instances.   |
|----------------------------------------------------------------------------|------------------------------------------------|
| [`NetworkDetail`](#algokit_utils.clients.client_manager.NetworkDetail)     | Details about an Algorand network.             |
| [`ClientManager`](#algokit_utils.clients.client_manager.ClientManager)     | Manager for Algorand SDK clients.              |

## Module Contents

### *class* algokit_utils.clients.client_manager.AlgoSdkClients(algod: algosdk.v2client.algod.AlgodClient, indexer: algosdk.v2client.indexer.IndexerClient | None = None, kmd: algosdk.kmd.KMDClient | None = None)

Container for Algorand SDK client instances.

Holds references to Algod, Indexer and KMD clients.

* **Parameters:**
  * **algod** – Algod client instance
  * **indexer** – Optional Indexer client instance
  * **kmd** – Optional KMD client instance

#### algod

#### indexer *= None*

#### kmd *= None*

### *class* algokit_utils.clients.client_manager.NetworkDetail

Details about an Algorand network.

Contains network type flags and genesis information.

#### is_testnet *: bool*

#### is_mainnet *: bool*

#### is_localnet *: bool*

#### genesis_id *: str*

#### genesis_hash *: str*

### *class* algokit_utils.clients.client_manager.ClientManager(clients_or_configs: [algokit_utils.models.network.AlgoClientConfigs](../../models/network/index.md#algokit_utils.models.network.AlgoClientConfigs) | [AlgoSdkClients](#algokit_utils.clients.client_manager.AlgoSdkClients), algorand_client: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient))

Manager for Algorand SDK clients.

Provides access to Algod, Indexer and KMD clients and helper methods for working with them.

* **Parameters:**
  * **clients_or_configs** – Either client instances or client configurations
  * **algorand_client** – AlgorandClient instance

#### *property* algod *: algosdk.v2client.algod.AlgodClient*

Returns an algosdk Algod API client.

* **Returns:**
  Algod client instance

#### *property* indexer *: algosdk.v2client.indexer.IndexerClient*

Returns an algosdk Indexer API client.

* **Raises:**
  **ValueError** – If no Indexer client is configured
* **Returns:**
  Indexer client instance

#### *property* indexer_if_present *: algosdk.v2client.indexer.IndexerClient | None*

Returns the Indexer client if configured, otherwise None.

* **Returns:**
  Indexer client instance or None

#### *property* kmd *: algosdk.kmd.KMDClient*

Returns an algosdk KMD API client.

* **Raises:**
  **ValueError** – If no KMD client is configured
* **Returns:**
  KMD client instance

#### network() → [NetworkDetail](#algokit_utils.clients.client_manager.NetworkDetail)

Get details about the connected Algorand network.

* **Returns:**
  Network details including type and genesis information

#### is_localnet() → bool

Check if connected to a local network.

* **Returns:**
  True if connected to a local network

#### is_testnet() → bool

Check if connected to TestNet.

* **Returns:**
  True if connected to TestNet

#### is_mainnet() → bool

Check if connected to MainNet.

* **Returns:**
  True if connected to MainNet

#### get_testnet_dispenser(auth_token: str | None = None, request_timeout: int | None = None) → [algokit_utils.clients.dispenser_api_client.TestNetDispenserApiClient](../dispenser_api_client/index.md#algokit_utils.clients.dispenser_api_client.TestNetDispenserApiClient)

Get a TestNet dispenser API client.

* **Parameters:**
  * **auth_token** – Optional authentication token
  * **request_timeout** – Optional request timeout in seconds
* **Returns:**
  TestNet dispenser client instance

#### get_app_factory(app_spec: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../../applications/app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract) | algokit_utils._legacy_v2.application_specification.ApplicationSpecification | str, app_name: str | None = None, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, version: str | None = None, compilation_params: [algokit_utils.applications.app_client.AppClientCompilationParams](../../applications/app_client/index.md#algokit_utils.applications.app_client.AppClientCompilationParams) | None = None) → [algokit_utils.applications.app_factory.AppFactory](../../applications/app_factory/index.md#algokit_utils.applications.app_factory.AppFactory)

Get an application factory for deploying smart contracts.

* **Parameters:**
  * **app_spec** – Application specification
  * **app_name** – Optional application name
  * **default_sender** – Optional default sender address
  * **default_signer** – Optional default transaction signer
  * **version** – Optional version string
  * **compilation_params** – Optional compilation parameters
* **Raises:**
  **ValueError** – If no Algorand client is configured
* **Returns:**
  Application factory instance

#### get_app_client_by_id(app_spec: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../../applications/app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract) | algokit_utils._legacy_v2.application_specification.ApplicationSpecification | str, app_id: int, app_name: str | None = None, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, approval_source_map: algosdk.source_map.SourceMap | None = None, clear_source_map: algosdk.source_map.SourceMap | None = None) → [algokit_utils.applications.app_client.AppClient](../../applications/app_client/index.md#algokit_utils.applications.app_client.AppClient)

Get an application client for an existing application by ID.

* **Parameters:**
  * **app_spec** – Application specification
  * **app_id** – Application ID
  * **app_name** – Optional application name
  * **default_sender** – Optional default sender address
  * **default_signer** – Optional default transaction signer
  * **approval_source_map** – Optional approval program source map
  * **clear_source_map** – Optional clear program source map
* **Raises:**
  **ValueError** – If no Algorand client is configured
* **Returns:**
  Application client instance

#### get_app_client_by_network(app_spec: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../../applications/app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract) | algokit_utils._legacy_v2.application_specification.ApplicationSpecification | str, app_name: str | None = None, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, approval_source_map: algosdk.source_map.SourceMap | None = None, clear_source_map: algosdk.source_map.SourceMap | None = None) → [algokit_utils.applications.app_client.AppClient](../../applications/app_client/index.md#algokit_utils.applications.app_client.AppClient)

Get an application client for an existing application by network.

* **Parameters:**
  * **app_spec** – Application specification
  * **app_name** – Optional application name
  * **default_sender** – Optional default sender address
  * **default_signer** – Optional default transaction signer
  * **approval_source_map** – Optional approval program source map
  * **clear_source_map** – Optional clear program source map
* **Raises:**
  **ValueError** – If no Algorand client is configured
* **Returns:**
  Application client instance

#### get_app_client_by_creator_and_name(creator_address: str, app_name: str, app_spec: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../../applications/app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Arc56Contract) | algokit_utils._legacy_v2.application_specification.ApplicationSpecification | str, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, ignore_cache: bool | None = None, app_lookup_cache: [algokit_utils.applications.app_deployer.ApplicationLookup](../../applications/app_deployer/index.md#algokit_utils.applications.app_deployer.ApplicationLookup) | None = None, approval_source_map: algosdk.source_map.SourceMap | None = None, clear_source_map: algosdk.source_map.SourceMap | None = None) → [algokit_utils.applications.app_client.AppClient](../../applications/app_client/index.md#algokit_utils.applications.app_client.AppClient)

Get an application client by creator address and name.

* **Parameters:**
  * **creator_address** – Creator address
  * **app_name** – Application name
  * **app_spec** – Application specification
  * **default_sender** – Optional default sender address
  * **default_signer** – Optional default transaction signer
  * **ignore_cache** – Optional flag to ignore cache
  * **app_lookup_cache** – Optional app lookup cache
  * **approval_source_map** – Optional approval program source map
  * **clear_source_map** – Optional clear program source map
* **Returns:**
  Application client instance

#### *static* get_algod_client(config: [algokit_utils.models.network.AlgoClientNetworkConfig](../../models/network/index.md#algokit_utils.models.network.AlgoClientNetworkConfig) | None = None) → algosdk.v2client.algod.AlgodClient

Get an Algod client from config or environment.

* **Parameters:**
  **config** – Optional client configuration
* **Returns:**
  Algod client instance

#### *static* get_algod_client_from_environment() → algosdk.v2client.algod.AlgodClient

Get an Algod client from environment variables.

* **Returns:**
  Algod client instance

#### *static* get_kmd_client(config: [algokit_utils.models.network.AlgoClientNetworkConfig](../../models/network/index.md#algokit_utils.models.network.AlgoClientNetworkConfig) | None = None) → algosdk.kmd.KMDClient

Get a KMD client from config or environment.

* **Parameters:**
  **config** – Optional client configuration
* **Returns:**
  KMD client instance

#### *static* get_kmd_client_from_environment() → algosdk.kmd.KMDClient

Get a KMD client from environment variables.

* **Returns:**
  KMD client instance

#### *static* get_indexer_client(config: [algokit_utils.models.network.AlgoClientNetworkConfig](../../models/network/index.md#algokit_utils.models.network.AlgoClientNetworkConfig) | None = None) → algosdk.v2client.indexer.IndexerClient

Get an Indexer client from config or environment.

* **Parameters:**
  **config** – Optional client configuration
* **Returns:**
  Indexer client instance

#### *static* get_indexer_client_from_environment() → algosdk.v2client.indexer.IndexerClient

Get an Indexer client from environment variables.

* **Returns:**
  Indexer client instance

#### *static* genesis_id_is_localnet(genesis_id: str | None) → bool

Check if a genesis ID indicates a local network.

* **Parameters:**
  **genesis_id** – Genesis ID to check
* **Returns:**
  True if genesis ID indicates a local network

#### get_typed_app_client_by_creator_and_name(typed_client: type[TypedAppClientT], \*, creator_address: str, app_name: str, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, ignore_cache: bool | None = None, app_lookup_cache: [algokit_utils.applications.app_deployer.ApplicationLookup](../../applications/app_deployer/index.md#algokit_utils.applications.app_deployer.ApplicationLookup) | None = None) → TypedAppClientT

Get a typed application client by creator address and name.

* **Parameters:**
  * **typed_client** – Typed client class
  * **creator_address** – Creator address
  * **app_name** – Application name
  * **default_sender** – Optional default sender address
  * **default_signer** – Optional default transaction signer
  * **ignore_cache** – Optional flag to ignore cache
  * **app_lookup_cache** – Optional app lookup cache
* **Raises:**
  **ValueError** – If no Algorand client is configured
* **Returns:**
  Typed application client instance

#### get_typed_app_client_by_id(typed_client: type[TypedAppClientT], \*, app_id: int, app_name: str | None = None, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, approval_source_map: algosdk.source_map.SourceMap | None = None, clear_source_map: algosdk.source_map.SourceMap | None = None) → TypedAppClientT

Get a typed application client by ID.

* **Parameters:**
  * **typed_client** – Typed client class
  * **app_id** – Application ID
  * **app_name** – Optional application name
  * **default_sender** – Optional default sender address
  * **default_signer** – Optional default transaction signer
  * **approval_source_map** – Optional approval program source map
  * **clear_source_map** – Optional clear program source map
* **Raises:**
  **ValueError** – If no Algorand client is configured
* **Returns:**
  Typed application client instance

#### get_typed_app_client_by_network(typed_client: type[TypedAppClientT], \*, app_name: str | None = None, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, approval_source_map: algosdk.source_map.SourceMap | None = None, clear_source_map: algosdk.source_map.SourceMap | None = None) → TypedAppClientT

Returns a new typed client, resolves the app ID for the current network.

Uses pre-determined network-specific app IDs specified in the ARC-56 app spec.
If no IDs are in the app spec or the network isn’t recognised, an error is thrown.

* **Parameters:**
  * **typed_client** – The typed client class to instantiate
  * **app_name** – Optional application name
  * **default_sender** – Optional default sender address
  * **default_signer** – Optional default transaction signer
  * **approval_source_map** – Optional approval program source map
  * **clear_source_map** – Optional clear program source map
* **Raises:**
  **ValueError** – If no Algorand client is configured
* **Returns:**
  The typed client instance

#### get_typed_app_factory(typed_factory: type[TypedFactoryT], \*, app_name: str | None = None, default_sender: str | None = None, default_signer: algosdk.atomic_transaction_composer.TransactionSigner | None = None, version: str | None = None, compilation_params: [algokit_utils.applications.app_client.AppClientCompilationParams](../../applications/app_client/index.md#algokit_utils.applications.app_client.AppClientCompilationParams) | None = None) → TypedFactoryT

Get a typed application factory.

* **Parameters:**
  * **typed_factory** – Typed factory class
  * **app_name** – Optional application name
  * **default_sender** – Optional default sender address
  * **default_signer** – Optional default transaction signer
  * **version** – Optional version string
  * **compilation_params** – Optional compilation parameters
* **Raises:**
  **ValueError** – If no Algorand client is configured
* **Returns:**
  Typed application factory instance

#### *static* get_config_from_environment_or_localnet() → [algokit_utils.models.network.AlgoClientConfigs](../../models/network/index.md#algokit_utils.models.network.AlgoClientConfigs)

Retrieve client configuration from environment variables or fallback to localnet defaults.

If ALGOD_SERVER is set in environment variables, it will use environment configuration,
otherwise it will use default localnet configuration.

* **Returns:**
  Configuration for algod, indexer, and optionally kmd

#### *static* get_default_localnet_config(config_or_port: Literal['algod', 'indexer', 'kmd'] | int) → [algokit_utils.models.network.AlgoClientNetworkConfig](../../models/network/index.md#algokit_utils.models.network.AlgoClientNetworkConfig)

Get default configuration for local network services.

* **Parameters:**
  **config_or_port** – Service name or port number
* **Returns:**
  Client configuration for local network

#### *static* get_algod_config_from_environment() → [algokit_utils.models.network.AlgoClientNetworkConfig](../../models/network/index.md#algokit_utils.models.network.AlgoClientNetworkConfig)

Retrieve the algod configuration from environment variables.
Will raise an error if ALGOD_SERVER environment variable is not set

* **Returns:**
  Algod client configuration

#### *static* get_indexer_config_from_environment() → [algokit_utils.models.network.AlgoClientNetworkConfig](../../models/network/index.md#algokit_utils.models.network.AlgoClientNetworkConfig)

Retrieve the indexer configuration from environment variables.
Will raise an error if INDEXER_SERVER environment variable is not set

* **Returns:**
  Indexer client configuration

#### *static* get_kmd_config_from_environment() → [algokit_utils.models.network.AlgoClientNetworkConfig](../../models/network/index.md#algokit_utils.models.network.AlgoClientNetworkConfig)

Retrieve the kmd configuration from environment variables.

* **Returns:**
  KMD client configuration

#### *static* get_algonode_config(network: Literal['testnet', 'mainnet'], config: Literal['algod', 'indexer']) → [algokit_utils.models.network.AlgoClientNetworkConfig](../../models/network/index.md#algokit_utils.models.network.AlgoClientNetworkConfig)

Returns the Algorand configuration to point to the free tier of the AlgoNode service.

* **Parameters:**
  * **network** – Which network to connect to - TestNet or MainNet
  * **config** – Which algod config to return - Algod or Indexer
* **Returns:**
  Configuration for the specified network and service
