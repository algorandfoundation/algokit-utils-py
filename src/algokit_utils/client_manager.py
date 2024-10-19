import dataclasses
import os
from typing import Literal

from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from algokit_utils.dispenser_api import (
    BaseDispenserApiClientParams,
    TestNetDispenserApiClient,
    TestNetDispenserApiClientParams,
)
from algokit_utils.network_clients import AlgoClientConfig, AlgoConfig, NetworkDetails


@dataclasses.dataclass
class AlgoSdkClients:
    algod: AlgodClient
    indexer: IndexerClient | None = None
    kmd: KMDClient | None = None


class ClientManager:
    def __init__(self, config: AlgoConfig | AlgoSdkClients):
        if isinstance(config, AlgoSdkClients):
            self._algod = config.algod
            self._indexer = config.indexer
            self._kmd = config.kmd
        else:
            self._algod = self.get_algod_client(config.algod_config)
            self._indexer = self.get_indexer_client(config.indexer_config) if config.indexer_config else None
            self._kmd = self.get_kmd_client(config.kmd_config) if config.kmd_config else None

    @property
    def algod(self) -> AlgodClient:
        return self._algod

    @property
    def indexer(self) -> IndexerClient:
        if not self._indexer:
            raise ValueError("Attempt to use Indexer client in AlgoKit instance with no Indexer configured")
        return self._indexer

    @property
    def kmd(self) -> KMDClient:
        if not self._kmd:
            raise ValueError("Attempt to use Kmd client in AlgoKit instance with no Kmd configured")
        return self._kmd

    def network(self) -> NetworkDetails:
        params = self._algod.suggested_params()
        genesis_id = str(params.gen)
        genesis_hash = str(params.gh)
        is_testnet = "testnet" in genesis_id
        is_mainnet = "mainnet" in genesis_id
        is_localnet = self.genesis_id_is_localnet(genesis_id)
        return NetworkDetails(
            genesis_id=genesis_id,
            genesis_hash=genesis_hash,
            is_testnet=is_testnet,
            is_mainnet=is_mainnet,
            is_localnet=is_localnet,
        )

    async def is_localnet(self) -> bool:
        return self.network().is_localnet

    def is_testnet(self) -> bool:
        return self.network().is_testnet

    def is_mainnet(self) -> bool:
        return self.network().is_mainnet

    def get_testnet_dispenser(self, params: TestNetDispenserApiClientParams) -> TestNetDispenserApiClient:
        return TestNetDispenserApiClient(params)

    def get_test_net_dispenser_from_environment(
        self, params: BaseDispenserApiClientParams | None = None
    ) -> TestNetDispenserApiClient:
        if params is None:
            params = BaseDispenserApiClientParams()

        return TestNetDispenserApiClient(
            TestNetDispenserApiClientParams(auth_token="", request_timeout=params.request_timeout)
        )

    # def get_app_factory(self) -> None:
    #     # TODO: implement
    #     pass

    # def get_app_client_by_creator_and_name(self) -> None:
    #     # TODO: implement
    #     pass

    # def get_app_client_by_id(self, params: ClientAppClientParams) -> None:
    #     # TODO: implement
    #     pass

    # async def get_app_client_by_network(self, params: ClientAppClientByNetworkParams) -> None:
    #     # TODO: implement
    #     pass

    # async def get_typed_app_client_by_creator_and_name(
    #     self, typed_client: TypedAppClient, params: ClientTypedAppClientByCreatorAndNameParams
    # ) -> None:
    #     # TODO: implement
    #     pass

    # def get_typed_app_client_by_id(self, typed_client: TypedAppClient, params: ClientTypedAppClientParams) -> None:
    #     # TODO: implement
    #     pass

    # def get_typed_app_client_by_network(
    #     self, typed_client: TypedAppClient, params: ClientTypedAppClientByNetworkParams | None = None
    # ) -> None:
    #     # TODO: implement
    #     pass

    # def get_typed_app_factory(
    #     self, typed_factory: TypedAppFactory, params: ClientTypedAppFactoryParams | None = None
    # ) -> None:
    #     # TODO: implement
    #     pass

    @staticmethod
    def get_config_from_environment_or_localnet() -> AlgoConfig:
        if os.getenv("ALGOD_SERVER"):
            algod_config = ClientManager.get_algod_config_from_environment()
            indexer_config = (
                ClientManager.get_indexer_config_from_environment() if os.getenv("INDEXER_SERVER") else None
            )
            kmd_config = (
                AlgoClientConfig(
                    server=algod_config.server, port=os.getenv("KMD_PORT", "4002"), token=algod_config.token
                )
                if not any(net in algod_config.server for net in ["mainnet", "testnet"])
                else None
            )
        else:
            algod_config = ClientManager.get_default_localnet_config("algod")
            indexer_config = ClientManager.get_default_localnet_config("indexer")
            kmd_config = ClientManager.get_default_localnet_config("kmd")

        return AlgoConfig(algod_config=algod_config, indexer_config=indexer_config, kmd_config=kmd_config)

    @staticmethod
    def get_algod_config_from_environment() -> AlgoClientConfig:
        return ClientManager._get_config_from_environment("ALGOD")

    @staticmethod
    def get_indexer_config_from_environment() -> AlgoClientConfig:
        return ClientManager._get_config_from_environment("INDEXER")

    @staticmethod
    def get_algonode_config(
        network: Literal["testnet", "mainnet"], config: Literal["algod", "indexer"]
    ) -> AlgoClientConfig:
        return AlgoClientConfig(
            server=f"https://{network}-{ 'api' if config == 'algod' else 'idx'}.algonode.cloud/",
            token="",
        )

    @staticmethod
    def get_default_localnet_config(config_type: Literal["algod", "indexer", "kmd"]) -> AlgoClientConfig:
        return AlgoClientConfig(
            server="http://localhost",
            port=4001 if config_type == "algod" else 8980 if config_type == "indexer" else 4002,
            token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )

    @staticmethod
    def get_algod_client(config: AlgoClientConfig) -> AlgodClient:
        headers = {"X-Algo-API-Token": config.token} if config.token else None
        return AlgodClient(config.token or "", config.server, headers)

    @staticmethod
    def get_algod_client_from_environment() -> AlgodClient:
        return ClientManager.get_algod_client(ClientManager.get_algod_config_from_environment())

    @staticmethod
    def get_indexer_client(config: AlgoClientConfig) -> IndexerClient:
        headers = {"X-Indexer-API-Token": config.token} if config.token else None
        return IndexerClient(config.token or "", config.server, headers)  # type: ignore[no-untyped-call]

    @staticmethod
    def get_indexer_client_from_environment() -> IndexerClient:
        return ClientManager.get_indexer_client(ClientManager.get_indexer_config_from_environment())

    @staticmethod
    def get_kmd_client(config: AlgoClientConfig) -> KMDClient:
        return KMDClient(kmd_token=config.token, kmd_address=config.server)  # type: ignore[no-untyped-call]

    @staticmethod
    def get_kmd_client_from_environment() -> KMDClient:
        algod_config = ClientManager.get_algod_config_from_environment()
        algod_config.port = os.getenv("KMD_PORT", "4002")
        return ClientManager.get_kmd_client(algod_config)

    @staticmethod
    def genesis_id_is_localnet(genesis_id: str) -> bool:
        return genesis_id in ["devnet-v1", "sandnet-v1", "dockernet-v1"]

    @staticmethod
    def _get_config_from_environment(environment_prefix: str) -> AlgoClientConfig:
        server = os.getenv(f"{environment_prefix}_SERVER")
        if server is None:
            raise ValueError(f"Server environment variable not set: {environment_prefix}_SERVER")
        port = os.getenv(f"{environment_prefix}_PORT")
        token = os.getenv(f"{environment_prefix}_TOKEN", "")
        return AlgoClientConfig(server=server, port=port, token=token)
