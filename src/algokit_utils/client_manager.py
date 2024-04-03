from typing import Any, Dict, Optional, Union

import algosdk
from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from algokit_utils import (DISPENSER_REQUEST_TIMEOUT,
                           TestNetDispenserApiClient, get_algod_client,
                           get_indexer_client)
from algokit_utils.network_clients import AlgoClientConfigs, get_kmd_client


class AlgoSdkClients:
    """
    Clients from algosdk that interact with the official Algorand APIs.

    Attributes:
        algod (AlgodClient): Algod client, see https://developer.algorand.org/docs/rest-apis/algod/
        indexer (Optional[IndexerClient]): Optional indexer client, see https://developer.algorand.org/docs/rest-apis/indexer/
        kmd (Optional[KMDClient]): Optional KMD client, see https://developer.algorand.org/docs/rest-apis/kmd/
    """

    def __init__(self, algod: algosdk.v2client.algod.AlgodClient, indexer: Optional[IndexerClient] = None, kmd: Optional[KMDClient] = None):
        self.algod = algod
        self.indexer = indexer
        self.kmd = kmd

class ClientManager:
    """
    Exposes access to various API clients.

    Args:
        clients_or_config (Union[AlgoConfig, AlgoSdkClients]): algosdk clients or config for interacting with the official Algorand APIs.
    """

    def __init__(self, clients_or_configs: Union[AlgoClientConfigs, AlgoSdkClients]):
        if isinstance(clients_or_configs, AlgoSdkClients):
            _clients = clients_or_configs
        elif isinstance(clients_or_configs, AlgoClientConfigs):
            _clients = AlgoSdkClients(
                algod=get_algod_client(clients_or_configs.algod_config),
                indexer=get_indexer_client(clients_or_configs.indexer_config) if clients_or_configs.indexer_config else None,
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

    def get_testnet_dispenser(self, auth_token: str | None = None, request_timeout: int = DISPENSER_REQUEST_TIMEOUT) -> Any:
        """
        Returns a TestNet Dispenser API client.
        Refer to [docs](https://github.com/algorandfoundation/algokit/blob/main/docs/testnet_api.md) on guidance to obtain an access token.

        Args:
            params (Optional[TestNetDispenserApiClientParams]): An object containing parameters for the TestNetDispenserApiClient class.
                Or None if you want the client to load the access token from the environment variable `ALGOKIT_DISPENSER_ACCESS_TOKEN`.

        Returns:
            An instance of the TestNetDispenserApiClient class.
        """
        return TestNetDispenserApiClient(auth_token=auth_token, request_timeout=request_timeout)