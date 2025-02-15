from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TypeVar
from urllib import parse

import algosdk
from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.kmd import KMDClient
from algosdk.source_map import SourceMap
from algosdk.transaction import SuggestedParams
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.applications.app_deployer import ApplicationLookup
from algokit_utils.applications.app_spec.arc56 import Arc56Contract
from algokit_utils.clients.dispenser_api_client import TestNetDispenserApiClient
from algokit_utils.models.network import AlgoClientConfigs, AlgoClientNetworkConfig
from algokit_utils.protocols.typed_clients import TypedAppClientProtocol, TypedAppFactoryProtocol

if TYPE_CHECKING:
    from algokit_utils.algorand import AlgorandClient
    from algokit_utils.applications.app_client import AppClient, AppClientCompilationParams
    from algokit_utils.applications.app_factory import AppFactory

__all__ = [
    "AlgoSdkClients",
    "ClientManager",
    "NetworkDetail",
]

TypedFactoryT = TypeVar("TypedFactoryT", bound=TypedAppFactoryProtocol)
TypedAppClientT = TypeVar("TypedAppClientT", bound=TypedAppClientProtocol)


class AlgoSdkClients:
    """Container for Algorand SDK client instances.

    Holds references to Algod, Indexer and KMD clients.

    :param algod: Algod client instance
    :param indexer: Optional Indexer client instance
    :param kmd: Optional KMD client instance
    """

    def __init__(
        self,
        algod: algosdk.v2client.algod.AlgodClient,
        indexer: IndexerClient | None = None,
        kmd: KMDClient | None = None,
    ):
        self.algod = algod
        self.indexer = indexer
        self.kmd = kmd


@dataclass(kw_only=True, frozen=True)
class NetworkDetail:
    """Details about an Algorand network.

    Contains network type flags and genesis information.
    """

    is_testnet: bool
    """Whether the network is a testnet"""
    is_mainnet: bool
    """Whether the network is a mainnet"""
    is_localnet: bool
    """Whether the network is a localnet"""
    genesis_id: str
    """The genesis ID of the network"""
    genesis_hash: str
    """The genesis hash of the network"""


def _get_config_from_environment(environment_prefix: str) -> AlgoClientNetworkConfig:
    server = os.getenv(f"{environment_prefix}_SERVER")
    if server is None:
        raise Exception(f"Server environment variable not set: {environment_prefix}_SERVER")
    port = os.getenv(f"{environment_prefix}_PORT")
    if port:
        parsed = parse.urlparse(server)
        server = parsed._replace(netloc=f"{parsed.hostname}").geturl()
    return AlgoClientNetworkConfig(server, os.getenv(f"{environment_prefix}_TOKEN", ""), port=port)


class ClientManager:
    """Manager for Algorand SDK clients.

    Provides access to Algod, Indexer and KMD clients and helper methods for working with them.

    :param clients_or_configs: Either client instances or client configurations
    :param algorand_client: AlgorandClient instance

    :example:
        >>> # Algod only
        >>> client_manager = ClientManager(algod_client)
        >>> # Algod and Indexer
        >>> client_manager = ClientManager(algod_client, indexer_client)
        >>> # Algod config only
        >>> client_manager = ClientManager(ClientManager.get_algod_config_from_environment())
        >>> # Algod and Indexer config
        >>> client_manager = ClientManager(ClientManager.get_algod_config_from_environment(),
        ...     ClientManager.get_indexer_config_from_environment())
    """

    def __init__(self, clients_or_configs: AlgoClientConfigs | AlgoSdkClients, algorand_client: AlgorandClient):
        if isinstance(clients_or_configs, AlgoSdkClients):
            _clients = clients_or_configs
        elif isinstance(clients_or_configs, AlgoClientConfigs):
            _clients = AlgoSdkClients(
                algod=ClientManager.get_algod_client(clients_or_configs.algod_config),
                indexer=ClientManager.get_indexer_client(clients_or_configs.indexer_config)
                if clients_or_configs.indexer_config
                else None,
                kmd=ClientManager.get_kmd_client(clients_or_configs.kmd_config)
                if clients_or_configs.kmd_config
                else None,
            )
        self._algod = _clients.algod
        self._indexer = _clients.indexer
        self._kmd = _clients.kmd
        self._algorand = algorand_client
        self._suggested_params: SuggestedParams | None = None

    @property
    def algod(self) -> AlgodClient:
        """Returns an algosdk Algod API client.

        :return: Algod client instance
        """
        return self._algod

    @property
    def indexer(self) -> IndexerClient:
        """Returns an algosdk Indexer API client.

        :raises ValueError: If no Indexer client is configured
        :return: Indexer client instance
        """
        if not self._indexer:
            raise ValueError("Attempt to use Indexer client in AlgoKit instance with no Indexer configured")
        return self._indexer

    @property
    def indexer_if_present(self) -> IndexerClient | None:
        """Returns the Indexer client if configured, otherwise None.

        :return: Indexer client instance or None
        """
        return self._indexer

    @property
    def kmd(self) -> KMDClient:
        """Returns an algosdk KMD API client.

        :raises ValueError: If no KMD client is configured
        :return: KMD client instance
        """
        if not self._kmd:
            raise ValueError("Attempt to use Kmd client in AlgoKit instance with no Kmd configured")
        return self._kmd

    def network(self) -> NetworkDetail:
        """Get details about the connected Algorand network.

        :return: Network details including type and genesis information

        :example:
            >>> client_manager = ClientManager(algod_client)
            >>> network_detail = client_manager.network()
        """
        if self._suggested_params is None:
            self._suggested_params = self._algod.suggested_params()
        sp = self._suggested_params
        return NetworkDetail(
            is_testnet=sp.gen in ["testnet-v1.0", "testnet-v1", "testnet"],
            is_mainnet=sp.gen in ["mainnet-v1.0", "mainnet-v1", "mainnet"],
            is_localnet=ClientManager.genesis_id_is_localnet(str(sp.gen)),
            genesis_id=str(sp.gen),
            genesis_hash=sp.gh,
        )

    def is_localnet(self) -> bool:
        """Check if connected to a local network.

        :return: True if connected to a local network
        """
        return self.network().is_localnet

    def is_testnet(self) -> bool:
        """Check if connected to TestNet.

        :return: True if connected to TestNet
        """
        return self.network().is_testnet

    def is_mainnet(self) -> bool:
        """Check if connected to MainNet.

        :return: True if connected to MainNet
        """
        return self.network().is_mainnet

    def get_testnet_dispenser(
        self, auth_token: str | None = None, request_timeout: int | None = None
    ) -> TestNetDispenserApiClient:
        """Get a TestNet dispenser API client.

        :param auth_token: Optional authentication token
        :param request_timeout: Optional request timeout in seconds
        :return: TestNet dispenser client instance
        """
        if request_timeout:
            return TestNetDispenserApiClient(auth_token=auth_token, request_timeout=request_timeout)

        return TestNetDispenserApiClient(auth_token=auth_token)

    def get_app_factory(
        self,
        app_spec: Arc56Contract | ApplicationSpecification | str,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        version: str | None = None,
        compilation_params: AppClientCompilationParams | None = None,
    ) -> AppFactory:
        """Get an application factory for deploying smart contracts.

        :param app_spec: Application specification
        :param app_name: Optional application name
        :param default_sender: Optional default sender address
        :param default_signer: Optional default transaction signer
        :param version: Optional version string
        :param compilation_params: Optional compilation parameters
        :raises ValueError: If no Algorand client is configured
        :return: Application factory instance
        """
        from algokit_utils.applications.app_factory import AppFactory, AppFactoryParams

        if not self._algorand:
            raise ValueError("Attempt to get app factory from a ClientManager without an Algorand client")

        return AppFactory(
            AppFactoryParams(
                algorand=self._algorand,
                app_spec=app_spec,
                app_name=app_name,
                default_sender=default_sender,
                default_signer=default_signer,
                version=version,
                compilation_params=compilation_params,
            )
        )

    def get_app_client_by_id(
        self,
        app_spec: (Arc56Contract | ApplicationSpecification | str),
        app_id: int,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
        """Get an application client for an existing application by ID.

        :param app_spec: Application specification
        :param app_id: Application ID
        :param app_name: Optional application name
        :param default_sender: Optional default sender address
        :param default_signer: Optional default transaction signer
        :param approval_source_map: Optional approval program source map
        :param clear_source_map: Optional clear program source map
        :raises ValueError: If no Algorand client is configured
        :return: Application client instance
        """
        from algokit_utils.applications.app_client import AppClient, AppClientParams

        if not self._algorand:
            raise ValueError("Attempt to get app client from a ClientManager without an Algorand client")

        return AppClient(
            AppClientParams(
                app_spec=app_spec,
                algorand=self._algorand,
                app_id=app_id,
                app_name=app_name,
                default_sender=default_sender,
                default_signer=default_signer,
                approval_source_map=approval_source_map,
                clear_source_map=clear_source_map,
            )
        )

    def get_app_client_by_network(
        self,
        app_spec: (Arc56Contract | ApplicationSpecification | str),
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
        """Get an application client for an existing application by network.

        :param app_spec: Application specification
        :param app_name: Optional application name
        :param default_sender: Optional default sender address
        :param default_signer: Optional default transaction signer
        :param approval_source_map: Optional approval program source map
        :param clear_source_map: Optional clear program source map
        :raises ValueError: If no Algorand client is configured
        :return: Application client instance
        """
        from algokit_utils.applications.app_client import AppClient

        if not self._algorand:
            raise ValueError("Attempt to get app client from a ClientManager without an Algorand client")

        return AppClient.from_network(
            app_spec=app_spec,
            app_name=app_name,
            default_sender=default_sender,
            default_signer=default_signer,
            approval_source_map=approval_source_map,
            clear_source_map=clear_source_map,
            algorand=self._algorand,
        )

    def get_app_client_by_creator_and_name(
        self,
        creator_address: str,
        app_name: str,
        app_spec: Arc56Contract | ApplicationSpecification | str,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: ApplicationLookup | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
        """Get an application client by creator address and name.

        :param creator_address: Creator address
        :param app_name: Application name
        :param app_spec: Application specification
        :param default_sender: Optional default sender address
        :param default_signer: Optional default transaction signer
        :param ignore_cache: Optional flag to ignore cache
        :param app_lookup_cache: Optional app lookup cache
        :param approval_source_map: Optional approval program source map
        :param clear_source_map: Optional clear program source map
        :return: Application client instance
        """
        from algokit_utils.applications.app_client import AppClient

        return AppClient.from_creator_and_name(
            creator_address=creator_address,
            app_name=app_name,
            default_sender=default_sender,
            default_signer=default_signer,
            ignore_cache=ignore_cache,
            app_lookup_cache=app_lookup_cache,
            app_spec=app_spec,
            approval_source_map=approval_source_map,
            clear_source_map=clear_source_map,
            algorand=self._algorand,
        )

    @staticmethod
    def get_algod_client(config: AlgoClientNetworkConfig) -> AlgodClient:
        """Get an Algod client from config or environment.

        :param config: Optional client configuration
        :return: Algod client instance
        """
        headers = {"X-Algo-API-Token": config.token or ""}
        return AlgodClient(
            algod_token=config.token or "",
            algod_address=config.full_url(),
            headers=headers,
        )

    @staticmethod
    def get_algod_client_from_environment() -> AlgodClient:
        """Get an Algod client from environment variables.

        :return: Algod client instance
        """
        return ClientManager.get_algod_client(ClientManager.get_algod_config_from_environment())

    @staticmethod
    def get_kmd_client(config: AlgoClientNetworkConfig) -> KMDClient:
        """Get a KMD client from config or environment.

        :param config: Optional client configuration
        :return: KMD client instance
        """
        return KMDClient(config.token, config.full_url())

    @staticmethod
    def get_kmd_client_from_environment() -> KMDClient:
        """Get a KMD client from environment variables.

        :return: KMD client instance
        """
        return ClientManager.get_kmd_client(ClientManager.get_kmd_config_from_environment())

    @staticmethod
    def get_indexer_client(config: AlgoClientNetworkConfig) -> IndexerClient:
        """Get an Indexer client from config or environment.

        :param config: Optional client configuration
        :return: Indexer client instance
        """
        headers = {"X-Indexer-API-Token": config.token}
        return IndexerClient(
            indexer_token=config.token,
            indexer_address=config.full_url(),
            headers=headers,
        )

    @staticmethod
    def get_indexer_client_from_environment() -> IndexerClient:
        """Get an Indexer client from environment variables.

        :return: Indexer client instance
        """
        return ClientManager.get_indexer_client(ClientManager.get_indexer_config_from_environment())

    @staticmethod
    def genesis_id_is_localnet(genesis_id: str | None) -> bool:
        """Check if a genesis ID indicates a local network.

        :param genesis_id: Genesis ID to check
        :return: True if genesis ID indicates a local network

        :example:
            >>> ClientManager.genesis_id_is_localnet("devnet-v1")
        """
        return genesis_id in ["devnet-v1", "sandnet-v1", "dockernet-v1"]

    def get_typed_app_client_by_creator_and_name(
        self,
        typed_client: type[TypedAppClientT],
        *,
        creator_address: str,
        app_name: str,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: ApplicationLookup | None = None,
    ) -> TypedAppClientT:
        """Get a typed application client by creator address and name.

        :param typed_client: Typed client class
        :param creator_address: Creator address
        :param app_name: Application name
        :param default_sender: Optional default sender address
        :param default_signer: Optional default transaction signer
        :param ignore_cache: Optional flag to ignore cache
        :param app_lookup_cache: Optional app lookup cache
        :raises ValueError: If no Algorand client is configured
        :return: Typed application client instance

        :example:
            >>> client_manager = ClientManager(algod_client)
            >>> typed_app_client = client_manager.get_typed_app_client_by_creator_and_name(
            ...     typed_client=MyAppClient,
            ...     creator_address="creator_address",
            ...     app_name="app_name",
            ... )
        """
        if not self._algorand:
            raise ValueError("Attempt to get app client from a ClientManager without an Algorand client")

        return typed_client.from_creator_and_name(
            creator_address=creator_address,
            app_name=app_name,
            default_sender=default_sender,
            default_signer=default_signer,
            ignore_cache=ignore_cache,
            app_lookup_cache=app_lookup_cache,
            algorand=self._algorand,
        )

    def get_typed_app_client_by_id(
        self,
        typed_client: type[TypedAppClientT],
        *,
        app_id: int,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> TypedAppClientT:
        """Get a typed application client by ID.

        :param typed_client: Typed client class
        :param app_id: Application ID
        :param app_name: Optional application name
        :param default_sender: Optional default sender address
        :param default_signer: Optional default transaction signer
        :param approval_source_map: Optional approval program source map
        :param clear_source_map: Optional clear program source map
        :raises ValueError: If no Algorand client is configured
        :return: Typed application client instance

        :example:
            >>> client_manager = ClientManager(algod_client)
            >>> typed_app_client = client_manager.get_typed_app_client_by_id(
            ...     typed_client=MyAppClient,
            ...     app_id=1234567890,
            ... )
        """
        if not self._algorand:
            raise ValueError("Attempt to get app client from a ClientManager without an Algorand client")

        return typed_client(
            app_id=app_id,
            app_name=app_name,
            default_sender=default_sender,
            default_signer=default_signer,
            approval_source_map=approval_source_map,
            clear_source_map=clear_source_map,
            algorand=self._algorand,
        )

    def get_typed_app_client_by_network(
        self,
        typed_client: type[TypedAppClientT],
        *,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> TypedAppClientT:
        """Returns a new typed client, resolves the app ID for the current network.

        Uses pre-determined network-specific app IDs specified in the ARC-56 app spec.
        If no IDs are in the app spec or the network isn't recognised, an error is thrown.

        :param typed_client: The typed client class to instantiate
        :param app_name: Optional application name
        :param default_sender: Optional default sender address
        :param default_signer: Optional default transaction signer
        :param approval_source_map: Optional approval program source map
        :param clear_source_map: Optional clear program source map
        :raises ValueError: If no Algorand client is configured
        :return: The typed client instance

        :example:
            >>> client_manager = ClientManager(algod_client)
            >>> typed_app_client = client_manager.get_typed_app_client_by_network(
            ...     typed_client=MyAppClient,
            ...     app_name="app_name",
            ... )
        """
        if not self._algorand:
            raise ValueError("Attempt to get app client from a ClientManager without an Algorand client")

        return typed_client.from_network(
            app_name=app_name,
            default_sender=default_sender,
            default_signer=default_signer,
            approval_source_map=approval_source_map,
            clear_source_map=clear_source_map,
            algorand=self._algorand,
        )

    def get_typed_app_factory(
        self,
        typed_factory: type[TypedFactoryT],
        *,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        version: str | None = None,
        compilation_params: AppClientCompilationParams | None = None,
    ) -> TypedFactoryT:
        """Get a typed application factory.

        :param typed_factory: Typed factory class
        :param app_name: Optional application name
        :param default_sender: Optional default sender address
        :param default_signer: Optional default transaction signer
        :param version: Optional version string
        :param compilation_params: Optional compilation parameters
        :raises ValueError: If no Algorand client is configured
        :return: Typed application factory instance

        :example:
            >>> client_manager = ClientManager(algod_client)
            >>> typed_app_factory = client_manager.get_typed_app_factory(
            ...     typed_factory=MyAppFactory,
            ...     app_name="app_name",
            ... )
        """
        if not self._algorand:
            raise ValueError("Attempt to get app factory from a ClientManager without an Algorand client")

        return typed_factory(
            algorand=self._algorand,
            app_name=app_name,
            default_sender=default_sender,
            default_signer=default_signer,
            version=version,
            compilation_params=compilation_params,
        )

    @staticmethod
    def get_config_from_environment_or_localnet() -> AlgoClientConfigs:
        """Retrieve client configuration from environment variables or fallback to localnet defaults.

        If ALGOD_SERVER is set in environment variables, it will use environment configuration,
        otherwise it will use default localnet configuration.

        :return: Configuration for algod, indexer, and optionally kmd

        :example:
            >>> client_manager = ClientManager(algod_client)
            >>> config = client_manager.get_config_from_environment_or_localnet()
        """
        algod_server = os.getenv("ALGOD_SERVER")

        if algod_server:
            # Use environment configuration
            algod_config = ClientManager.get_algod_config_from_environment()

            # Only include indexer if INDEXER_SERVER is set
            indexer_config = (
                ClientManager.get_indexer_config_from_environment() if os.getenv("INDEXER_SERVER") else None
            )

            # Include KMD config only for local networks (not mainnet/testnet)
            kmd_config = (
                AlgoClientNetworkConfig(
                    server=algod_config.server, token=algod_config.token, port=os.getenv("KMD_PORT", "4002")
                )
                if not any(net in algod_server.lower() for net in ["mainnet", "testnet"])
                else None
            )
        else:
            # Use localnet defaults
            algod_config = ClientManager.get_default_localnet_config("algod")
            indexer_config = ClientManager.get_default_localnet_config("indexer")
            kmd_config = ClientManager.get_default_localnet_config("kmd")

        return AlgoClientConfigs(
            algod_config=algod_config,
            indexer_config=indexer_config,
            kmd_config=kmd_config,
        )

    @staticmethod
    def get_default_localnet_config(
        config_or_port: Literal["algod", "indexer", "kmd"] | int,
    ) -> AlgoClientNetworkConfig:
        """Get default configuration for local network services.

        :param config_or_port: Service name or port number
        :return: Client configuration for local network

        :example:
            >>> client_manager = ClientManager(algod_client)
            >>> config = client_manager.get_default_localnet_config("algod")
        """
        port = (
            config_or_port
            if isinstance(config_or_port, int)
            else {"algod": 4001, "indexer": 8980, "kmd": 4002}[config_or_port]
        )

        return AlgoClientNetworkConfig(server="http://localhost", token="a" * 64, port=port)

    @staticmethod
    def get_algod_config_from_environment() -> AlgoClientNetworkConfig:
        """Retrieve the algod configuration from environment variables.
        Will raise an error if ALGOD_SERVER environment variable is not set

        :return: Algod client configuration

        :example:
            >>> client_manager = ClientManager(algod_client)
            >>> config = client_manager.get_algod_config_from_environment()
        """
        return _get_config_from_environment("ALGOD")

    @staticmethod
    def get_indexer_config_from_environment() -> AlgoClientNetworkConfig:
        """Retrieve the indexer configuration from environment variables.
        Will raise an error if INDEXER_SERVER environment variable is not set

        :return: Indexer client configuration

        :example:
            >>> client_manager = ClientManager(algod_client)
            >>> config = client_manager.get_indexer_config_from_environment()
        """
        return _get_config_from_environment("INDEXER")

    @staticmethod
    def get_kmd_config_from_environment() -> AlgoClientNetworkConfig:
        """Retrieve the kmd configuration from environment variables.

        :return: KMD client configuration

        :example:
            >>> client_manager = ClientManager(algod_client)
            >>> config = client_manager.get_kmd_config_from_environment()
        """
        return _get_config_from_environment("KMD")

    @staticmethod
    def get_algonode_config(
        network: Literal["testnet", "mainnet"], config: Literal["algod", "indexer"]
    ) -> AlgoClientNetworkConfig:
        """Returns the Algorand configuration to point to the free tier of the AlgoNode service.

        :param network: Which network to connect to - TestNet or MainNet
        :param config: Which algod config to return - Algod or Indexer
        :return: Configuration for the specified network and service

        :example:
            >>> client_manager = ClientManager(algod_client)
            >>> config = client_manager.get_algonode_config("testnet", "algod")
        """
        service_type = "api" if config == "algod" else "idx"
        return AlgoClientNetworkConfig(
            server=f"https://{network}-{service_type}.algonode.cloud",
            port=443,
            token="",
        )
