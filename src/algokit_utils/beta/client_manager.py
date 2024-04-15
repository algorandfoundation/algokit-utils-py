import algosdk
from algokit_utils.dispenser_api import TestNetDispenserApiClient
from algokit_utils.network_clients import AlgoClientConfigs, get_algod_client, get_indexer_client, get_kmd_client
from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient


class AlgoSdkClients:
    """
    Clients from algosdk that interact with the official Algorand APIs.

    Attributes:
        algod (AlgodClient): Algod client, see https://developer.algorand.org/docs/rest-apis/algod/
        indexer (Optional[IndexerClient]): Optional indexer client, see https://developer.algorand.org/docs/rest-apis/indexer/
        kmd (Optional[KMDClient]): Optional KMD client, see https://developer.algorand.org/docs/rest-apis/kmd/
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


class ClientManager:
    """
    Exposes access to various API clients.

    Args:
        clients_or_config (Union[AlgoConfig, AlgoSdkClients]): algosdk clients or config for interacting with the official Algorand APIs.
    """

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
    def kmd(self) -> KMDClient:
        """Returns an algosdk KMD API client or raises an error if it's not been provided."""
        if not self._kmd:
            raise ValueError("Attempt to use Kmd client in AlgoKit instance with no Kmd configured")
        return self._kmd

    def get_testnet_dispenser(
        self, auth_token: str | None = None, request_timeout: int | None = None
    ) -> TestNetDispenserApiClient:
        if request_timeout:
            return TestNetDispenserApiClient(auth_token=auth_token, request_timeout=request_timeout)

        return TestNetDispenserApiClient(auth_token=auth_token)
