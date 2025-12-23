import copy
import time

import typing_extensions

from algokit_algod_client import AlgodClient
from algokit_algod_client import models as algod_models
from algokit_indexer_client import IndexerClient
from algokit_kmd_client.client import KmdClient
from algokit_transact.signer import AddressWithTransactionSigner
from algokit_utils.accounts.account_manager import AccountManager
from algokit_utils.applications.app_deployer import AppDeployer
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.assets.asset_manager import AssetManager
from algokit_utils.clients.client_manager import AlgoSdkClients, ClientManager
from algokit_utils.models.network import AlgoClientConfigs, AlgoClientNetworkConfig
from algokit_utils.protocols.signer import TransactionSigner
from algokit_utils.transactions.transaction_composer import (
    ErrorTransformer,
    TransactionComposer,
    TransactionComposerParams,
)
from algokit_utils.transactions.transaction_creator import AlgorandClientTransactionCreator
from algokit_utils.transactions.transaction_sender import AlgorandClientTransactionSender

__all__ = [
    "AlgorandClient",
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
        self._app_deployer: AppDeployer = AppDeployer(
            self._app_manager, self._transaction_sender, self._client_manager.indexer_if_present
        )
        self._transaction_creator = AlgorandClientTransactionCreator(
            new_group=lambda: self.new_group(),
        )

        self._cached_suggested_params: algod_models.SuggestedParams | None = None
        self._cached_suggested_params_expiry: float | None = None
        self._cached_suggested_params_timeout: int = 3_000  # three seconds
        self._default_validity_window: int | None = None
        self._error_transformers: set[ErrorTransformer] = set()

    def set_default_validity_window(self, validity_window: int) -> typing_extensions.Self:
        """
        Sets the default validity window for transactions.

        :param validity_window: The number of rounds between the first and last valid rounds
        :return: The `AlgorandClient` so method calls can be chained
        :example:
            >>> algorand = AlgorandClient.mainnet().set_default_validity_window(1000);
        """
        self._default_validity_window = validity_window
        return self

    def set_default_signer(self, signer: TransactionSigner | AddressWithTransactionSigner) -> typing_extensions.Self:
        """
        Sets the default signer to use if no other signer is specified.

        :param signer: The signer to use, either a `TransactionSigner` or an `AddressWithTransactionSigner`
        :return: The `AlgorandClient` so method calls can be chained
        :example:
            >>> signer = account_manager.random()  # Returns AddressWithSigners
            >>> algorand = AlgorandClient.mainnet().set_default_signer(signer)
        """
        self._account_manager.set_default_signer(signer)
        return self

    def set_signer(self, sender: str, signer: TransactionSigner) -> typing_extensions.Self:
        """
        Tracks the given account for later signing.

        :param sender: The sender address to use this signer for
        :param signer: The signer to sign transactions with for the given sender
        :return: The `AlgorandClient` so method calls can be chained
        :example:
            >>> account = account_manager.random()  # Returns AddressWithSigners
            >>> algorand = AlgorandClient.mainnet().set_signer(account.addr, account.signer)
        """
        self._account_manager.set_signer(sender, signer)
        return self

    def set_signer_from_account(self, signer: AddressWithTransactionSigner) -> typing_extensions.Self:
        """
        Sets the default signer to use if no other signer is specified.

        :param signer: The signer to use, either a `TransactionSigner` or an `AddressWithTransactionSigner`
        :return: The `AlgorandClient` so method calls can be chained
        :example:
            >>> accountManager = AlgorandClient.mainnet()
            >>> accountManager.set_signer_from_account(TransactionSignerAccount(address=..., signer=...))
            >>> accountManager.set_signer_from_account(algosdk.LogicSigAccount(program, args))
            >>> accountManager.set_signer_from_account(account_manager.random())  # AddressWithSigners
            >>> accountManager.set_signer_from_account(MultisigAccount(metadata, sub_signers))
            >>> accountManager.set_signer_from_account(account)
        """
        self._account_manager.set_default_signer(signer)
        return self

    def set_suggested_params_cache(
        self, suggested_params: algod_models.SuggestedParams, until: float | None = None
    ) -> typing_extensions.Self:
        """
        Sets a cache value to use for suggested params.

        :param suggested_params: The suggested params to use
        :param until: A timestamp until which to cache, or if not specified then the timeout is used
        :return: The `AlgorandClient` so method calls can be chained
        :example:
            >>> algorand = AlgorandClient.mainnet().set_suggested_params_cache(suggested_params, time.time() + 3.6e6)
        """
        self._cached_suggested_params = suggested_params
        self._cached_suggested_params_expiry = until or time.time() + self._cached_suggested_params_timeout
        return self

    def set_suggested_params_cache_timeout(self, timeout: int) -> typing_extensions.Self:
        """
        Sets the timeout for caching suggested params.

        :param timeout: The timeout in milliseconds
        :return: The `AlgorandClient` so method calls can be chained
        :example:
            >>> algorand = AlgorandClient.mainnet().set_suggested_params_cache_timeout(10_000)
        """
        self._cached_suggested_params_timeout = timeout
        return self

    def get_suggested_params(self) -> algod_models.SuggestedParams:
        """
        Get suggested params for a transaction (either cached or from algod if the cache is stale or empty)

        :example:
            >>> algorand = AlgorandClient.mainnet().get_suggested_params()
        """
        if self._cached_suggested_params and (
            self._cached_suggested_params_expiry is None or self._cached_suggested_params_expiry > time.time()
        ):
            return copy.deepcopy(self._cached_suggested_params)

        self._cached_suggested_params = self._client_manager.algod.suggested_params()
        self._cached_suggested_params_expiry = time.time() + self._cached_suggested_params_timeout

        return copy.deepcopy(self._cached_suggested_params)

    def register_error_transformer(self, transformer: ErrorTransformer) -> typing_extensions.Self:
        """Register a function that will be used to transform an error caught when simulating or executing
        composed transaction groups made from `new_group`

        :param transformer: The error transformer function
        :return: The AlgorandClient so you can chain method calls
        """
        self._error_transformers.add(transformer)
        return self

    def unregister_error_transformer(self, transformer: ErrorTransformer) -> typing_extensions.Self:
        """Unregister an error transformer function

        :param transformer: The error transformer function to remove
        :return: The AlgorandClient so you can chain method calls
        """
        self._error_transformers.discard(transformer)
        return self

    def new_group(self) -> TransactionComposer:
        """
        Start a new `TransactionComposer` transaction group

        :example:
            >>> composer = AlgorandClient.mainnet().new_group()
            >>> result = composer.add_transaction(payment).send()
        """

        return TransactionComposer(
            TransactionComposerParams(
                algod=self.client.algod,
                get_signer=lambda addr: self.account.get_signer(addr),
                get_suggested_params=self.get_suggested_params,
                default_validity_window=self._default_validity_window,
                app_manager=self._app_manager,
                error_transformers=list(self._error_transformers),
            )
        )

    @property
    def client(self) -> ClientManager:
        """
        Get clients, including algosdk clients and app clients.

        :example:
            >>> clientManager = AlgorandClient.mainnet().client
        """
        return self._client_manager

    @property
    def account(self) -> AccountManager:
        """Get or create accounts that can sign transactions.

        :example:
            >>> accountManager = AlgorandClient.mainnet().account
        """
        return self._account_manager

    @property
    def asset(self) -> AssetManager:
        """
        Get or create assets.

        :example:
            >>> assetManager = AlgorandClient.mainnet().asset
        """
        return self._asset_manager

    @property
    def app(self) -> AppManager:
        """
        Get or create applications.

        :example:
            >>> appManager = AlgorandClient.mainnet().app
        """
        return self._app_manager

    @property
    def app_deployer(self) -> AppDeployer:
        """
        Get or create applications.

        :example:
            >>> appDeployer = AlgorandClient.mainnet().app_deployer
        """
        return self._app_deployer

    @property
    def send(self) -> AlgorandClientTransactionSender:
        """
        Methods for sending a transaction and waiting for confirmation

        :example:
            >>> result = AlgorandClient.mainnet().send.payment(
            >>> PaymentParams(
            >>>  sender="SENDERADDRESS",
            >>>  receiver="RECEIVERADDRESS",
            >>>  amount=AlgoAmount(algo-1)
            >>> ))
        """
        return self._transaction_sender

    @property
    def create_transaction(self) -> AlgorandClientTransactionCreator:
        """
        Methods for building transactions

        :example:
            >>> transaction = AlgorandClient.mainnet().create_transaction.payment(
            >>> PaymentParams(
            >>>  sender="SENDERADDRESS",
            >>>  receiver="RECEIVERADDRESS",
            >>>  amount=AlgoAmount(algo=1)
            >>> ))
        """
        return self._transaction_creator

    @staticmethod
    def default_localnet() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing at default LocalNet ports and API token.

        :return: The `AlgorandClient`

        :example:
            >>> algorand = AlgorandClient.default_localnet()
        """
        return AlgorandClient(
            AlgoClientConfigs(
                algod_config=ClientManager.get_default_localnet_config("algod"),
                indexer_config=ClientManager.get_default_localnet_config("indexer"),
                kmd_config=ClientManager.get_default_localnet_config("kmd"),
            )
        )

    @staticmethod
    def testnet() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing at TestNet using AlgoNode.

        :return: The `AlgorandClient`

        :example:
            >>> algorand = AlgorandClient.testnet()
        """
        return AlgorandClient(
            AlgoClientConfigs(
                algod_config=ClientManager.get_algonode_config("testnet", "algod"),
                indexer_config=ClientManager.get_algonode_config("testnet", "indexer"),
                kmd_config=None,
            )
        )

    @staticmethod
    def mainnet() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing at MainNet using AlgoNode.

        :return: The `AlgorandClient`

        :example:
            >>> algorand = AlgorandClient.mainnet()
        """
        return AlgorandClient(
            AlgoClientConfigs(
                algod_config=ClientManager.get_algonode_config("mainnet", "algod"),
                indexer_config=ClientManager.get_algonode_config("mainnet", "indexer"),
                kmd_config=None,
            )
        )

    @staticmethod
    def from_clients(
        algod: AlgodClient, indexer: IndexerClient | None = None, kmd: KmdClient | None = None
    ) -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing to the given client(s).

        :param algod: The algod client to use
        :param indexer: The indexer client to use
        :param kmd: The kmd client to use
        :return: The `AlgorandClient`

        :example:
            >>> algorand = AlgorandClient.from_clients(algod, indexer, kmd)
        """
        return AlgorandClient(AlgoSdkClients(algod=algod, indexer=indexer, kmd=kmd))

    @staticmethod
    def from_environment() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` loading the configuration from environment variables.

        Retrieve configurations from environment variables when defined or get defaults.

        Expects to be called from a Python environment.

        :return: The `AlgorandClient`

        :example:
            >>> algorand = AlgorandClient.from_environment()
        """
        return AlgorandClient(ClientManager.get_config_from_environment_or_localnet())

    @staticmethod
    def from_config(
        algod_config: AlgoClientNetworkConfig,
        indexer_config: AlgoClientNetworkConfig | None = None,
        kmd_config: AlgoClientNetworkConfig | None = None,
    ) -> "AlgorandClient":
        """
        Returns an `AlgorandClient` from the given config.

        :param algod_config: The config to use for the algod client
        :param indexer_config: The config to use for the indexer client
        :param kmd_config: The config to use for the kmd client
        :return: The `AlgorandClient`

        :example:
            >>> algorand = AlgorandClient.from_config(algod_config, indexer_config, kmd_config)
        """
        return AlgorandClient(
            AlgoClientConfigs(algod_config=algod_config, indexer_config=indexer_config, kmd_config=kmd_config)
        )
