import copy
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from algokit_utils.beta.account_manager import AccountManager
from algokit_utils.beta.client_manager import AlgoSdkClients, ClientManager
from algokit_utils.beta.composer import (
    AlgokitComposer,
    AppCallParams,
    AssetConfigParams,
    AssetCreateParams,
    AssetDestroyParams,
    AssetFreezeParams,
    AssetOptInParams,
    AssetTransferParams,
    MethodCallParams,
    OnlineKeyRegParams,
    PayParams,
)
from algokit_utils.network_clients import (
    AlgoClientConfigs,
    get_algod_client,
    get_algonode_config,
    get_default_localnet_config,
    get_indexer_client,
    get_kmd_client,
)
from algosdk.atomic_transaction_composer import AtomicTransactionResponse, TransactionSigner
from algosdk.transaction import SuggestedParams, Transaction, wait_for_confirmation
from typing_extensions import Self

__all__ = [
    "AlgorandClient",
    "AssetCreateParams",
    "AssetOptInParams",
    "MethodCallParams",
    "PayParams",
    "AssetFreezeParams",
    "AssetConfigParams",
    "AssetDestroyParams",
    "AppCallParams",
    "OnlineKeyRegParams",
    "AssetTransferParams",
]


@dataclass
class AlgorandClientSendMethods:
    """
    Methods used to send a transaction to the network and wait for confirmation
    """

    payment: Callable[[PayParams], dict[str, Any]]
    asset_create: Callable[[AssetCreateParams], dict[str, Any]]
    asset_config: Callable[[AssetConfigParams], dict[str, Any]]
    asset_freeze: Callable[[AssetFreezeParams], dict[str, Any]]
    asset_destroy: Callable[[AssetDestroyParams], dict[str, Any]]
    asset_transfer: Callable[[AssetTransferParams], dict[str, Any]]
    app_call: Callable[[AppCallParams], dict[str, Any]]
    online_key_reg: Callable[[OnlineKeyRegParams], dict[str, Any]]
    method_call: Callable[[MethodCallParams], dict[str, Any]]
    asset_opt_in: Callable[[AssetOptInParams], dict[str, Any]]


@dataclass
class AlgorandClientTransactionMethods:
    """
    Methods used to form a transaction without signing or sending to the network
    """

    payment: Callable[[PayParams], Transaction]
    asset_create: Callable[[AssetCreateParams], Transaction]
    asset_config: Callable[[AssetConfigParams], Transaction]
    asset_freeze: Callable[[AssetFreezeParams], Transaction]
    asset_destroy: Callable[[AssetDestroyParams], Transaction]
    asset_transfer: Callable[[AssetTransferParams], Transaction]
    app_call: Callable[[AppCallParams], Transaction]
    online_key_reg: Callable[[OnlineKeyRegParams], Transaction]
    method_call: Callable[[MethodCallParams], list[Transaction]]
    asset_opt_in: Callable[[AssetOptInParams], Transaction]


class AlgorandClient:
    """A client that brokers easy access to Algorand functionality."""

    def __init__(self, config: AlgoClientConfigs | AlgoSdkClients):
        self._client_manager: ClientManager = ClientManager(config)
        self._account_manager: AccountManager = AccountManager(self._client_manager)

        self._cached_suggested_params: SuggestedParams | None = None
        self._cached_suggested_params_expiry: float | None = None
        self._cached_suggested_params_timeout: int = 3_000  # three seconds

        self._default_validity_window: int = 10

    def _unwrap_single_send_result(self, results: AtomicTransactionResponse) -> dict[str, Any]:
        return {
            "confirmation": wait_for_confirmation(self._client_manager.algod, results.tx_ids[0]),
            "tx_id": results.tx_ids[0],
        }

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

    @property
    def client(self) -> ClientManager:
        """Get clients, including algosdk clients and app clients."""
        return self._client_manager

    @property
    def account(self) -> AccountManager:
        """Get or create accounts that can sign transactions."""
        return self._account_manager

    def new_group(self) -> AlgokitComposer:
        """Start a new `AlgokitComposer` transaction group"""
        return AlgokitComposer(
            algod=self.client.algod,
            get_signer=lambda addr: self.account.get_signer(addr),
            get_suggested_params=self.get_suggested_params,
            default_validity_window=self._default_validity_window,
        )

    @property
    def send(self) -> AlgorandClientSendMethods:
        """Methods for sending a transaction and waiting for confirmation"""
        return AlgorandClientSendMethods(
            payment=lambda params: self._unwrap_single_send_result(self.new_group().add_payment(params).execute()),
            asset_create=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_create(params).execute()
            ),
            asset_config=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_config(params).execute()
            ),
            asset_freeze=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_freeze(params).execute()
            ),
            asset_destroy=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_destroy(params).execute()
            ),
            asset_transfer=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_transfer(params).execute()
            ),
            app_call=lambda params: self._unwrap_single_send_result(self.new_group().add_app_call(params).execute()),
            online_key_reg=lambda params: self._unwrap_single_send_result(
                self.new_group().add_online_key_reg(params).execute()
            ),
            method_call=lambda params: self._unwrap_single_send_result(
                self.new_group().add_method_call(params).execute()
            ),
            asset_opt_in=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_opt_in(params).execute()
            ),
        )

    @property
    def transactions(self) -> AlgorandClientTransactionMethods:
        """Methods for building transactions"""

        return AlgorandClientTransactionMethods(
            payment=lambda params: self.new_group().add_payment(params).build_group()[0].txn,
            asset_create=lambda params: self.new_group().add_asset_create(params).build_group()[0].txn,
            asset_config=lambda params: self.new_group().add_asset_config(params).build_group()[0].txn,
            asset_freeze=lambda params: self.new_group().add_asset_freeze(params).build_group()[0].txn,
            asset_destroy=lambda params: self.new_group().add_asset_destroy(params).build_group()[0].txn,
            asset_transfer=lambda params: self.new_group().add_asset_transfer(params).build_group()[0].txn,
            app_call=lambda params: self.new_group().add_app_call(params).build_group()[0].txn,
            online_key_reg=lambda params: self.new_group().add_online_key_reg(params).build_group()[0].txn,
            method_call=lambda params: [txn.txn for txn in self.new_group().add_method_call(params).build_group()],
            asset_opt_in=lambda params: self.new_group().add_asset_opt_in(params).build_group()[0].txn,
        )

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
