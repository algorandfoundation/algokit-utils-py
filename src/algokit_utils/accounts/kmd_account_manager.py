from collections.abc import Callable
from typing import Any, cast

from algosdk.kmd import KMDClient

from algokit_utils.clients.client_manager import ClientManager
from algokit_utils.config import config
from algokit_utils.models.account import SigningAccount
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import PaymentParams, TransactionComposer

__all__ = ["KmdAccount", "KmdAccountManager"]


class KmdAccount(SigningAccount):
    """Account retrieved from KMD with signing capabilities, extending base Account.

    Provides an account implementation that can be used to sign transactions using keys stored in KMD.

    :param private_key: Base64 encoded private key
    :param address: Optional address override for rekeyed accounts, defaults to None
    """

    def __init__(self, private_key: str, address: str | None = None) -> None:
        super().__init__(private_key=private_key, address=address or "")


class KmdAccountManager:
    """Provides abstractions over KMD that makes it easier to get and manage accounts."""

    _kmd: KMDClient | None

    def __init__(self, client_manager: ClientManager) -> None:
        self._client_manager = client_manager
        try:
            self._kmd = client_manager.kmd
        except ValueError:
            self._kmd = None

    def kmd(self) -> KMDClient:
        """Returns the KMD client, initializing it if needed.

        :raises Exception: If KMD client is not configured and not running against LocalNet
        :return: The KMD client
        """
        if self._kmd is None:
            if self._client_manager.is_localnet():
                kmd_config = ClientManager.get_config_from_environment_or_localnet()
                if not kmd_config.kmd_config:
                    raise Exception("Attempt to use KMD client with no KMD configured")
                self._kmd = ClientManager.get_kmd_client(kmd_config.kmd_config)
                return self._kmd
            raise Exception("Attempt to use KMD client with no KMD configured")
        return self._kmd

    def get_wallet_account(
        self,
        wallet_name: str,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
        sender: str | None = None,
    ) -> KmdAccount | None:
        """Returns an Algorand signing account with private key loaded from the given KMD wallet.

        Retrieves an account from a KMD wallet that matches the given predicate, or a random account
        if no predicate is provided.

        :param wallet_name: The name of the wallet to retrieve an account from
        :param predicate: Optional filter to use to find the account (otherwise gets a random account from the wallet)
        :param sender: Optional sender address to use this signer for (aka a rekeyed account)
        :return: The signing account or None if no matching wallet or account was found
        """

        kmd_client = self.kmd()
        wallets = kmd_client.list_wallets()
        wallet = next((w for w in wallets if w["name"] == wallet_name), None)
        if not wallet:
            return None

        wallet_id = wallet["id"]
        wallet_handle = kmd_client.init_wallet_handle(wallet_id, "")
        addresses = kmd_client.list_keys(wallet_handle)

        matched_address = None
        if predicate:
            for address in addresses:
                account_info = self._client_manager.algod.account_info(address)
                if predicate(cast(dict[str, Any], account_info)):
                    matched_address = address
                    break
        else:
            matched_address = next(iter(addresses), None)

        if not matched_address:
            return None

        private_key = kmd_client.export_key(wallet_handle, "", matched_address)
        return KmdAccount(private_key=private_key, address=sender)

    def get_or_create_wallet_account(self, name: str, fund_with: AlgoAmount | None = None) -> KmdAccount:
        """Gets or creates a funded account in a KMD wallet of the given name.

        Provides idempotent access to accounts from LocalNet without specifying the private key.

        :param name: The name of the wallet to retrieve / create
        :param fund_with: The number of Algos to fund the account with when created
        :return: An Algorand account with private key loaded
        """
        fund_with = fund_with or AlgoAmount.from_algo(1000)

        existing = self.get_wallet_account(name)
        if existing:
            return existing

        kmd_client = self.kmd()
        wallet_id = kmd_client.create_wallet(name, "")["id"]
        wallet_handle = kmd_client.init_wallet_handle(wallet_id, "")
        kmd_client.generate_key(wallet_handle)

        account = self.get_wallet_account(name)
        assert account is not None

        config.logger.info(
            f"LocalNet account '{name}' doesn't yet exist; created account {account.address} "
            f"with keys stored in KMD and funding with {fund_with} ALGO"
        )

        dispenser = self.get_localnet_dispenser_account()
        TransactionComposer(
            algod=self._client_manager.algod,
            get_signer=lambda _: dispenser.signer,
            get_suggested_params=self._client_manager.algod.suggested_params,
        ).add_payment(
            PaymentParams(
                sender=dispenser.address,
                receiver=account.address,
                amount=fund_with,
            )
        ).send()
        return account

    def get_localnet_dispenser_account(self) -> KmdAccount:
        """Returns an Algorand account with private key loaded for the default LocalNet dispenser account.

        Retrieves the default funded account from LocalNet that can be used to fund other accounts.

        :raises Exception: If not running against LocalNet or dispenser account not found
        :return: The default LocalNet dispenser account
        """
        if not self._client_manager.is_localnet():
            raise Exception("Can't get LocalNet dispenser account from non LocalNet network")

        dispenser = self.get_wallet_account(
            "unencrypted-default-wallet",
            lambda a: a["status"] != "Offline" and a["amount"] > 1_000_000_000,  # noqa: PLR2004
        )
        if not dispenser:
            raise Exception("Error retrieving LocalNet dispenser account; couldn't find the default account in KMD")

        return dispenser
