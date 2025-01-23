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
from algokit_utils.applications.app_client import AppClient, AppClientParams
from algokit_utils.applications.app_deployer import AppLookup
from algokit_utils.applications.app_spec.arc56 import Arc56Contract
from algokit_utils.clients.dispenser_api_client import TestNetDispenserApiClient
from algokit_utils.models.network import AlgoClientConfig, AlgoClientConfigs
from algokit_utils.models.state import TealTemplateParams
from algokit_utils.protocols.typed_clients import TypedAppClientProtocol, TypedAppFactoryProtocol

if TYPE_CHECKING:
    from algokit_utils.algorand import AlgorandClient
    from algokit_utils.applications.app_factory import AppFactory

__all__ = [
    "AlgoSdkClients",
    "ClientManager",
    "NetworkDetail",
]

TypedFactoryT = TypeVar("TypedFactoryT", bound=TypedAppFactoryProtocol)
TypedAppClientT = TypeVar("TypedAppClientT", bound=TypedAppClientProtocol)


class AlgoSdkClients:
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
    is_testnet: bool
    is_mainnet: bool
    is_localnet: bool
    genesis_id: str
    genesis_hash: str


def _get_config_from_environment(environment_prefix: str) -> AlgoClientConfig:
    server = os.getenv(f"{environment_prefix}_SERVER")
    if server is None:
        raise Exception(f"Server environment variable not set: {environment_prefix}_SERVER")
    port = os.getenv(f"{environment_prefix}_PORT")
    if port:
        parsed = parse.urlparse(server)
        server = parsed._replace(netloc=f"{parsed.hostname}:{port}").geturl()
    return AlgoClientConfig(server, os.getenv(f"{environment_prefix}_TOKEN", ""))


class ClientManager:
    def __init__(self, clients_or_configs: AlgoClientConfigs | AlgoSdkClients, algorand_client: "AlgorandClient"):
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
        """Returns an algosdk Algod API client."""
        return self._algod

    @property
    def indexer(self) -> IndexerClient:
        """Returns an algosdk Indexer API client or raises an error if it's not been provided."""
        if not self._indexer:
            raise ValueError("Attempt to use Indexer client in AlgoKit instance with no Indexer configured")
        return self._indexer

    @property
    def indexer_if_present(self) -> IndexerClient | None:
        return self._indexer

    @property
    def kmd(self) -> KMDClient:
        """Returns an algosdk KMD API client or raises an error if it's not been provided."""
        if not self._kmd:
            raise ValueError("Attempt to use Kmd client in AlgoKit instance with no Kmd configured")
        return self._kmd

    def network(self) -> NetworkDetail:
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
        return self.network().is_localnet

    def is_testnet(self) -> bool:
        return self.network().is_testnet

    def is_mainnet(self) -> bool:
        return self.network().is_mainnet

    def get_testnet_dispenser(
        self, auth_token: str | None = None, request_timeout: int | None = None
    ) -> TestNetDispenserApiClient:
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
        updatable: bool | None = None,
        deletable: bool | None = None,
        deploy_time_params: TealTemplateParams | None = None,
    ) -> "AppFactory":
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
                updatable=updatable,
                deletable=deletable,
                deploy_time_params=deploy_time_params,
            )
        )

    def get_app_client_by_id(
        self,
        app_spec: (Arc56Contract | ApplicationSpecification | str),
        app_id: int,
        app_name: str | None = None,
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
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
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
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
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: AppLookup | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
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
    def get_algod_client(config: AlgoClientConfig | None = None) -> AlgodClient:
        """Returns an {py:class}`algosdk.v2client.algod.AlgodClient` from `config` or environment

        If no configuration provided will use environment variables `ALGOD_SERVER`, `ALGOD_PORT` and `ALGOD_TOKEN`"""
        config = config or _get_config_from_environment("ALGOD")
        headers = {"X-Algo-API-Token": config.token or ""}
        return AlgodClient(algod_token=config.token or "", algod_address=config.server, headers=headers)

    @staticmethod
    def get_algod_client_from_environment() -> AlgodClient:
        return ClientManager.get_algod_client(ClientManager.get_algod_config_from_environment())

    @staticmethod
    def get_kmd_client(config: AlgoClientConfig | None = None) -> KMDClient:
        """Returns an {py:class}`algosdk.kmd.KMDClient` from `config` or environment

        If no configuration provided will use environment variables `KMD_SERVER`, `KMD_PORT` and `KMD_TOKEN`"""
        config = config or _get_config_from_environment("KMD")
        return KMDClient(config.token, config.server)

    @staticmethod
    def get_kmd_client_from_environment() -> KMDClient:
        return ClientManager.get_kmd_client(ClientManager.get_kmd_config_from_environment())

    @staticmethod
    def get_indexer_client(config: AlgoClientConfig | None = None) -> IndexerClient:
        """Returns an {py:class}`algosdk.v2client.indexer.IndexerClient` from `config` or environment.

        If no configuration provided will use environment variables `INDEXER_SERVER`, `INDEXER_PORT` and
        `INDEXER_TOKEN`"""
        config = config or _get_config_from_environment("INDEXER")
        headers = {"X-Indexer-API-Token": config.token}
        return IndexerClient(indexer_token=config.token, indexer_address=config.server, headers=headers)

    @staticmethod
    def get_indexer_client_from_environment() -> IndexerClient:
        return ClientManager.get_indexer_client(ClientManager.get_indexer_config_from_environment())

    @staticmethod
    def genesis_id_is_localnet(genesis_id: str) -> bool:
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
        app_lookup_cache: AppLookup | None = None,
    ) -> TypedAppClientT:
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

        Args:
            typed_client: The typed client class to instantiate
            default_sender: Optional default sender address
            default_signer: Optional default transaction signer

        Returns:
            The typed client instance
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
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        version: str | None = None,
        updatable: bool | None = None,
        deletable: bool | None = None,
        deploy_time_params: TealTemplateParams | None = None,
    ) -> TypedFactoryT:
        if not self._algorand:
            raise ValueError("Attempt to get app factory from a ClientManager without an Algorand client")

        return typed_factory(
            algorand=self._algorand,
            app_name=app_name,
            default_sender=default_sender,
            default_signer=default_signer,
            version=version,
            updatable=updatable,
            deletable=deletable,
            deploy_time_params=deploy_time_params,
        )

    @staticmethod
    def get_config_from_environment_or_localnet() -> AlgoClientConfigs:
        """Retrieve client configuration from environment variables or fallback to localnet defaults.

        If ALGOD_SERVER is set in environment variables, it will use environment configuration,
        otherwise it will use default localnet configuration.

        Returns:
            AlgoClientConfigs: Configuration for algod, indexer, and optionally kmd
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
                AlgoClientConfig(
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
    def get_default_localnet_config(config_or_port: Literal["algod", "indexer", "kmd"] | int) -> AlgoClientConfig:
        port = (
            config_or_port
            if isinstance(config_or_port, int)
            else {"algod": 4001, "indexer": 8980, "kmd": 4002}[config_or_port]
        )

        return AlgoClientConfig(server=f"http://localhost:{port}", token="a" * 64)

    @staticmethod
    def get_algod_config_from_environment() -> AlgoClientConfig:
        """Retrieve the algod configuration from environment variables.

        Expects ALGOD_SERVER to be defined in environment variables.
        ALGOD_PORT and ALGOD_TOKEN are optional.

        Raises:
            ValueError: If ALGOD_SERVER environment variable is not set
        """
        return _get_config_from_environment("ALGOD")

    @staticmethod
    def get_indexer_config_from_environment() -> AlgoClientConfig:
        """Retrieve the indexer configuration from environment variables.

        Expects INDEXER_SERVER to be defined in environment variables.
        INDEXER_PORT and INDEXER_TOKEN are optional.

        Raises:
            ValueError: If INDEXER_SERVER environment variable is not set
        """
        return _get_config_from_environment("INDEXER")

    @staticmethod
    def get_kmd_config_from_environment() -> AlgoClientConfig:
        """Retrieve the kmd configuration from environment variables.

        Expects KMD_SERVER to be defined in environment variables.
        KMD_PORT and KMD_TOKEN are optional.
        """
        return _get_config_from_environment("KMD")

    @staticmethod
    def get_algonode_config(
        network: Literal["testnet", "mainnet"], config: Literal["algod", "indexer"]
    ) -> AlgoClientConfig:
        """Returns the Algorand configuration to point to the free tier of the AlgoNode service.

        Args:
            network: Which network to connect to - TestNet or MainNet
            config: Which algod config to return - Algod or Indexer

        Returns:
            AlgoClientConfig: Configuration for the specified network and service
        """
        service_type = "api" if config == "algod" else "idx"
        return AlgoClientConfig(
            server=f"https://{network}-{service_type}.algonode.cloud",
            port=443,
        )
