from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from algokit_utils.applications.app_deployer import AppDeployer
    from algokit_utils.applications.app_manager import AppManager
    from algokit_utils.clients.client_manager import ClientManager
    from algokit_utils.transactions.transaction_composer import TransactionComposer
    from algokit_utils.transactions.transaction_creator import AlgorandClientTransactionCreator
    from algokit_utils.transactions.transaction_sender import AlgorandClientTransactionSender

__all__ = [
    "AlgorandClientProtocol",
]


@dataclass
class _NetworkDetails:
    genesis_id: str
    genesis_hash: str
    network_name: str


@runtime_checkable
class AlgorandClientProtocol(Protocol):
    @property
    def app(self) -> AppManager: ...

    @property
    def app_deployer(self) -> AppDeployer: ...

    @property
    def send(self) -> AlgorandClientTransactionSender: ...

    @property
    def create_transaction(self) -> AlgorandClientTransactionCreator: ...

    def new_group(self) -> TransactionComposer: ...

    @property
    def client(self) -> ClientManager: ...
