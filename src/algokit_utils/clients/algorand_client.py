import copy
import time
from typing import Any

from algosdk.atomic_transaction_composer import AtomicTransactionResponse, TransactionSigner
from algosdk.transaction import SuggestedParams, wait_for_confirmation
from typing_extensions import Self

from algokit_utils.accounts.account_manager import AccountManager
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.assets.asset_manager import AssetManager
from algokit_utils.clients.client_manager import AlgoSdkClients, ClientManager
from algokit_utils.network_clients import (
    AlgoClientConfigs,
    get_algod_client,
    get_algonode_config,
    get_default_localnet_config,
    get_indexer_client,
    get_kmd_client,
)
from algokit_utils.transactions.transaction_composer import (
    AppCallParams,
    AppMethodCallParams,
    AssetConfigParams,
    AssetCreateParams,
    AssetDestroyParams,
    AssetFreezeParams,
    AssetOptInParams,
    AssetTransferParams,
    OnlineKeyRegistrationParams,
    PaymentParams,
    TransactionComposer,
)
from algokit_utils.transactions.transaction_creator import AlgorandClientTransactionCreator
from algokit_utils.transactions.transaction_sender import AlgorandClientTransactionSender

__all__ = [
    "AlgorandClient",
    "AssetCreateParams",
    "AssetOptInParams",
    "AppMethodCallParams",
    "PaymentParams",
    "AssetFreezeParams",
    "AssetConfigParams",
    "AssetDestroyParams",
    "AppCallParams",
    "OnlineKeyRegistrationParams",
    "AssetTransferParams",
]


class AlgorandClient:
    """A client that brokers easy access to Algorand functionality."""

    def __init__(self, config: AlgoClientConfigs | AlgoSdkClients):
        self._client_manager: ClientManager = ClientManager(clients_or_configs=config, algorand_client=self)
        self._account_manager: AccountManager = AccountManager(self._client_manager)
        self._asset_manager: AssetManager = AssetManager(self._client_manager.algod, lambda: self.new_group())
        self._app_manager: AppManager = AppManager(self._client_manager.algod)
        self._transaction_sender = AlgorandClientTransactionSender(
            new_group=lambda: self.new_group(),
            asset_manager=self._asset_manager,
            app_manager=self._app_manager,
            algod_client=self._client_manager.algod,
        )
        self._transaction_creator = AlgorandClientTransactionCreator(
            new_group=lambda: self.new_group(),
        )

        self._cached_suggested_params: SuggestedParams | None = None
        self._cached_suggested_params_expiry: float | None = None
        self._cached_suggested_params_timeout: int = 3_000  # three seconds

        self._default_validity_window: int = 10

    def set_default_validity_window(self, validity_window: int) -> Self:
        """
        Sets the default validity window for transactions.

        :param validity_window: The number of rounds between the first and last valid rounds
        :return: The `AlgorandClient` so method calls can be chained
        """
        self._default_validity_window = validity_window
        return self

    def set_default_signer(self, signer: TransactionSigner) -> Self:
        """
        Sets the default signer to use if no other signer is specified.

        :param signer: The signer to use, either a `TransactionSigner` or a `TransactionSignerAccount`
        :return: The `AlgorandClient` so method calls can be chained
        """
        self._account_manager.set_default_signer(signer)
        return self

    def set_signer(self, sender: str, signer: TransactionSigner) -> Self:
        """
        Tracks the given account for later signing.

        :param sender: The sender address to use this signer for
        :param signer: The signer to sign transactions with for the given sender
        :return: The `AlgorandClient` so method calls can be chained
        """
        self._account_manager.set_signer(sender, signer)
        return self

    def set_suggested_params(self, suggested_params: SuggestedParams, until: float | None = None) -> Self:
        """
        Sets a cache value to use for suggested params.

        :param suggested_params: The suggested params to use
        :param until: A timestamp until which to cache, or if not specified then the timeout is used
        :return: The `AlgorandClient` so method calls can be chained
        """
        self._cached_suggested_params = suggested_params
        self._cached_suggested_params_expiry = until or time.time() + self._cached_suggested_params_timeout
        return self

    def set_suggested_params_timeout(self, timeout: int) -> Self:
        """
        Sets the timeout for caching suggested params.

        :param timeout: The timeout in milliseconds
        :return: The `AlgorandClient` so method calls can be chained
        """
        self._cached_suggested_params_timeout = timeout
        return self

    def get_suggested_params(self) -> SuggestedParams:
        """Get suggested params for a transaction (either cached or from algod if the cache is stale or empty)"""
        if self._cached_suggested_params and (
            self._cached_suggested_params_expiry is None or self._cached_suggested_params_expiry > time.time()
        ):
            return copy.deepcopy(self._cached_suggested_params)

        self._cached_suggested_params = self._client_manager.algod.suggested_params()
        self._cached_suggested_params_expiry = time.time() + self._cached_suggested_params_timeout

        return copy.deepcopy(self._cached_suggested_params)

    def new_group(self) -> TransactionComposer:
        """Start a new `TransactionComposer` transaction group"""
        return TransactionComposer(
            algod=self.client.algod,
            get_signer=lambda addr: self.account.get_signer(addr),
            get_suggested_params=self.get_suggested_params,
            default_validity_window=self._default_validity_window,
        )

    @property
    def client(self) -> ClientManager:
        """Get clients, including algosdk clients and app clients."""
        return self._client_manager

    @property
    def account(self) -> AccountManager:
        """Get or create accounts that can sign transactions."""
        return self._account_manager

    @property
    def asset(self) -> AssetManager:
        """Get or create assets."""
        return self._asset_manager

    @property
    def app(self) -> AppManager:
        return self._app_manager

    @property
    def app_deployer(self) -> AppManager:
        """Get or create applications."""
        return self._app_manager

    @property
    def send(self) -> AlgorandClientTransactionSender:
        """Methods for sending a transaction and waiting for confirmation"""
        return self._transaction_sender

    @property
    def create_transaction(self) -> AlgorandClientTransactionCreator:
        """Methods for building transactions"""
        return self._transaction_creator

    def _unwrap_single_send_result(self, results: AtomicTransactionResponse) -> dict[str, Any]:
        return {
            "confirmation": wait_for_confirmation(self._client_manager.algod, results.tx_ids[0]),
            "tx_id": results.tx_ids[0],
        }

    @staticmethod
    def default_local_net() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing at default LocalNet ports and API token.

        :return: The `AlgorandClient`
        """
        return AlgorandClient(
            AlgoClientConfigs(
                algod_config=get_default_localnet_config("algod"),
                indexer_config=get_default_localnet_config("indexer"),
                kmd_config=get_default_localnet_config("kmd"),
            )
        )

    @staticmethod
    def test_net() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing at TestNet using AlgoNode.

        :return: The `AlgorandClient`
        """
        return AlgorandClient(
            AlgoClientConfigs(
                algod_config=get_algonode_config("testnet", "algod", ""),
                indexer_config=get_algonode_config("testnet", "indexer", ""),
                kmd_config=None,
            )
        )

    @staticmethod
    def main_net() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing at MainNet using AlgoNode.

        :return: The `AlgorandClient`
        """
        return AlgorandClient(
            AlgoClientConfigs(
                algod_config=get_algonode_config("mainnet", "algod", ""),
                indexer_config=get_algonode_config("mainnet", "indexer", ""),
                kmd_config=None,
            )
        )

    @staticmethod
    def from_clients(clients: AlgoSdkClients) -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing to the given client(s).

        :param clients: The clients to use
        :return: The `AlgorandClient`
        """
        return AlgorandClient(clients)

    @staticmethod
    def from_environment() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` loading the configuration from environment variables.

        Retrieve configurations from environment variables when defined or get defaults.

        Expects to be called from a Python environment.

        :return: The `AlgorandClient`
        """
        return AlgorandClient(
            AlgoSdkClients(
                algod=get_algod_client(),
                kmd=get_kmd_client(),
                indexer=get_indexer_client(),
            )
        )

    @staticmethod
    def from_config(config: AlgoClientConfigs) -> "AlgorandClient":
        """
        Returns an `AlgorandClient` from the given config.

        :param config: The config to use
        :return: The `AlgorandClient`
        """
        return AlgorandClient(config)
