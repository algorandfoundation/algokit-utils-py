from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import typing_extensions

if TYPE_CHECKING:
    from algosdk.atomic_transaction_composer import TransactionSigner
    from algosdk.transaction import SuggestedParams

    from algokit_utils.accounts import AccountManager
    from algokit_utils.applications.app_deployer import AppDeployer
    from algokit_utils.applications.app_manager import AppManager
    from algokit_utils.assets.asset_manager import AssetManager
    from algokit_utils.clients.client_manager import ClientManager
    from algokit_utils.transactions.transaction_composer import TransactionComposer
    from algokit_utils.transactions.transaction_creator import AlgorandClientTransactionCreator
    from algokit_utils.transactions.transaction_sender import AlgorandClientTransactionSender

__all__ = [
    "AlgorandClientProtocol",
]


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

    @property
    def client(self) -> ClientManager: ...

    @property
    def account(self) -> AccountManager: ...

    @property
    def asset(self) -> AssetManager: ...

    def set_default_validity_window(self, validity_window: int) -> typing_extensions.Self: ...

    def set_default_signer(self, signer: TransactionSigner) -> typing_extensions.Self: ...

    def set_signer(self, sender: str, signer: TransactionSigner) -> typing_extensions.Self: ...

    def set_suggested_params(
        self, suggested_params: SuggestedParams, until: float | None = None
    ) -> typing_extensions.Self: ...

    def set_suggested_params_timeout(self, timeout: int) -> typing_extensions.Self: ...

    def get_suggested_params(self) -> SuggestedParams: ...

    def new_group(self) -> TransactionComposer: ...
