import os
from dataclasses import dataclass
from typing import Literal
from urllib import parse

import algosdk
from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

# from algokit_utils.applications.app_factory import AppFactory, AppFactoryParams
from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.applications.app_factory import AppFactory, AppFactoryParams
from algokit_utils.applications.app_manager import TealTemplateParams
from algokit_utils.clients.dispenser_api_client import TestNetDispenserApiClient
from algokit_utils.models.application import Arc56Contract
from algokit_utils.models.network import AlgoClientConfig, AlgoClientConfigs
from algokit_utils.protocols.application import AlgorandClientProtocol


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
    is_test_net: bool
    is_main_net: bool
    is_local_net: bool
    genesis_id: str
    genesis_hash: str


def genesis_id_is_localnet(genesis_id: str) -> bool:
    return genesis_id in ["devnet-v1", "sandnet-v1", "dockernet-v1"]


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
    def __init__(self, clients_or_configs: AlgoClientConfigs | AlgoSdkClients, algorand_client: AlgorandClientProtocol):
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
        sp = self.algod.suggested_params()  # TODO: cache it
        return NetworkDetail(
            is_test_net=sp.gen in ["testnet-v1.0", "testnet-v1", "testnet"],
            is_main_net=sp.gen in ["mainnet-v1.0", "mainnet-v1", "mainnet"],
            is_local_net=ClientManager.genesis_id_is_local_net(str(sp.gen)),
            genesis_id=str(sp.gen),
            genesis_hash=sp.gh,
        )

    def is_local_net(self) -> bool:
        return self.network().is_local_net

    def is_test_net(self) -> bool:
        return self.network().is_test_net

    def is_main_net(self) -> bool:
        return self.network().is_main_net

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
    ) -> AppFactory:
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

    @staticmethod
    def get_algod_client(config: AlgoClientConfig | None = None) -> AlgodClient:
        """Returns an {py:class}`algosdk.v2client.algod.AlgodClient` from `config` or environment

        If no configuration provided will use environment variables `ALGOD_SERVER`, `ALGOD_PORT` and `ALGOD_TOKEN`"""
        config = config or _get_config_from_environment("ALGOD")
        headers = {"X-Algo-API-Token": config.token or ""}
        return AlgodClient(config.token or "", config.server, headers)

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

        If no configuration provided will use environment variables `INDEXER_SERVER`, `INDEXER_PORT` and `INDEXER_TOKEN`"""
        config = config or _get_config_from_environment("INDEXER")
        headers = {"X-Indexer-API-Token": config.token}
        return IndexerClient(config.token, config.server, headers)

    @staticmethod
    def get_indexer_client_from_environment() -> IndexerClient:
        return ClientManager.get_indexer_client(ClientManager.get_indexer_config_from_environment())

    @staticmethod
    def genesis_id_is_local_net(genesis_id: str) -> bool:
        return genesis_id_is_localnet(genesis_id)

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
                ClientManager.get_kmd_config_from_environment()
                if not any(net in algod_server.lower() for net in ["mainnet", "testnet"])
                else None
            )
        else:
            # Use localnet defaults
            algod_config = ClientManager.get_default_local_net_config("algod")
            indexer_config = ClientManager.get_default_local_net_config("indexer")
            kmd_config = ClientManager.get_default_local_net_config("kmd")

        return AlgoClientConfigs(
            algod_config=algod_config,
            indexer_config=indexer_config,
            kmd_config=kmd_config,
        )

    @staticmethod
    def get_default_local_net_config(config_or_port: Literal["algod", "indexer", "kmd"] | int) -> AlgoClientConfig:
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
            server=f"https://{network}-{service_type}.algonode.cloud/",
            port=443,
        )
