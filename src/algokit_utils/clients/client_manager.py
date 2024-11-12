from dataclasses import dataclass

import algosdk
from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from algokit_utils.clients.dispenser_api_client import TestNetDispenserApiClient
from algokit_utils.network_clients import (
    AlgoClientConfigs,
    get_algod_client,
    get_indexer_client,
    get_kmd_client,
)


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


@dataclass(kw_only=True)
class NetworkDetail:
    is_test_net: bool
    is_main_net: bool
    is_local_net: bool
    genesis_id: str
    genesis_hash: str


def genesis_id_is_localnet(genesis_id: str) -> bool:
    return genesis_id in ["devnet-v1", "sandnet-v1", "dockernet-v1"]


class ClientManager:
    def __init__(self, clients_or_configs: AlgoClientConfigs | AlgoSdkClients):
        if isinstance(clients_or_configs, AlgoSdkClients):
            _clients = clients_or_configs
        elif isinstance(clients_or_configs, AlgoClientConfigs):
            _clients = AlgoSdkClients(
                algod=get_algod_client(clients_or_configs.algod_config),
                indexer=get_indexer_client(clients_or_configs.indexer_config)
                if clients_or_configs.indexer_config
                else None,
                kmd=get_kmd_client(clients_or_configs.kmd_config) if clients_or_configs.kmd_config else None,
            )
        self._algod = _clients.algod
        self._indexer = _clients.indexer
        self._kmd = _clients.kmd

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

    def get_testnet_dispenser(
        self, auth_token: str | None = None, request_timeout: int | None = None
    ) -> TestNetDispenserApiClient:
        if request_timeout:
            return TestNetDispenserApiClient(auth_token=auth_token, request_timeout=request_timeout)

        return TestNetDispenserApiClient(auth_token=auth_token)

    @staticmethod
    def genesis_id_is_local_net(genesis_id: str) -> bool:
        return genesis_id_is_localnet(genesis_id)
