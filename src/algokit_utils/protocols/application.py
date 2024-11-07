from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from typing_extensions import runtime_checkable

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient
    from algosdk.v2client.indexer import IndexerClient

    from algokit_utils.applications.app_manager import AppManager
    from algokit_utils.clients.client_manager import ClientManager
    from algokit_utils.transactions.transaction_composer import TransactionComposer
    from algokit_utils.transactions.transaction_creator import AlgorandClientTransactionCreator
    from algokit_utils.transactions.transaction_sender import AlgorandClientTransactionSender


@dataclass
class NetworkDetails:
    genesis_id: str
    genesis_hash: str
    network_name: str


@runtime_checkable
class AlgorandClientProtocol(Protocol):
    @property
    def app(self) -> AppManager: ...

    @property
    def app_deployer(self) -> AppManager: ...

    @property
    def send(self) -> AlgorandClientTransactionSender: ...

    @property
    def create_transaction(self) -> AlgorandClientTransactionCreator: ...

    def new_group(self) -> TransactionComposer: ...

    @property
    def client(self) -> ClientManager: ...


@runtime_checkable
class ClientManagerProtocol(Protocol):
    @property
    def algod(self) -> AlgodClient: ...

    @property
    def indexer(self) -> IndexerClient | None: ...

    async def network(self) -> NetworkDetails: ...

    async def is_local_net(self) -> bool: ...

    async def is_test_net(self) -> bool: ...

    async def is_main_net(self) -> bool: ...
