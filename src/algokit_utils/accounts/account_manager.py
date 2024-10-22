from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from algosdk.account import generate_account
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner
from typing_extensions import Self

from algokit_utils.account import get_dispenser_account, get_kmd_wallet_account, get_localnet_default_account
from algokit_utils.clients.client_manager import ClientManager


@dataclass
class AddressAndSigner:
    address: str
    signer: TransactionSigner


class AccountManager:
    """Creates and keeps track of addresses and signers"""

    def __init__(self, client_manager: ClientManager):
        """
        Create a new account manager.

        :param client_manager: The ClientManager client to use for algod and kmd clients
        """
        self._client_manager = client_manager
        self._accounts = dict[str, TransactionSigner]()
        self._default_signer: TransactionSigner | None = None

    def set_default_signer(self, signer: TransactionSigner) -> Self:
        """
        Sets the default signer to use if no other signer is specified.

        :param signer: The signer to use, either a `TransactionSigner` or a `TransactionSignerAccount`
        :return: The `AccountManager` so method calls can be chained
        """
        self._default_signer = signer
        return self

    def set_signer(self, sender: str, signer: TransactionSigner) -> Self:
        """
        Tracks the given account for later signing.

        :param sender: The sender address to use this signer for
        :param signer: The signer to sign transactions with for the given sender
        :return: The AccountCreator instance for method chaining
        """
        self._accounts[sender] = signer
        return self

    def get_signer(self, sender: str) -> TransactionSigner:
        """
        Returns the `TransactionSigner` for the given sender address.

        If no signer has been registered for that address then the default signer is used if registered.

        :param sender: The sender address
        :return: The `TransactionSigner` or throws an error if not found
        """
        signer = self._accounts.get(sender, None) or self._default_signer
        if not signer:
            raise ValueError(f"No signer found for address {sender}")
        return signer

    def get_information(self, sender: str) -> dict[str, Any]:
        """
        Returns the given sender account's current status, balance and spendable amounts.

        Example:
            address = "XBYLS2E6YI6XXL5BWCAMOA4GTWHXWENZMX5UHXMRNWWUQ7BXCY5WC5TEPA"
            account_info = account.get_information(address)

        `Response data schema details <https://developer.algorand.org/docs/rest-apis/algod/#get-v2accountsaddress>`_

        :param sender: The address of the sender/account to look up
        :return: The account information
        """
        info = self._client_manager.algod.account_info(sender)
        assert isinstance(info, dict)
        return info

    def get_asset_information(self, sender: str, asset_id: int) -> dict[str, Any]:
        info = self._client_manager.algod.account_asset_info(sender, asset_id)
        assert isinstance(info, dict)
        return info

    def from_kmd(
        self,
        name: str,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
    ) -> AddressAndSigner:
        account = get_kmd_wallet_account(
            name=name, predicate=predicate, client=self._client_manager.algod, kmd_client=self._client_manager.kmd
        )
        if not account:
            raise ValueError(f"Unable to find KMD account {name}{' with predicate' if predicate else ''}")

        self.set_signer(account.address, account.signer)
        return AddressAndSigner(address=account.address, signer=account.signer)

    def random(self) -> AddressAndSigner:
        """
        Tracks and returns a new, random Algorand account with secret key loaded.

        Example:
            account = account.random()

        :return: The account
        """
        (sk, addr) = generate_account()  # type: ignore[no-untyped-call]
        signer = AccountTransactionSigner(sk)

        self.set_signer(addr, signer)

        return AddressAndSigner(address=addr, signer=signer)

    def dispenser(self) -> AddressAndSigner:
        """
        Returns an account (with private key loaded) that can act as a dispenser.

        Example:
            account = account.dispenser()

        If running on LocalNet then it will return the default dispenser account automatically,
        otherwise it will load the account mnemonic stored in os.environ['DISPENSER_MNEMONIC'].

        :return: The account
        """
        acct = get_dispenser_account(self._client_manager.algod)

        self.set_signer(acct.address, acct.signer)

        return AddressAndSigner(address=acct.address, signer=acct.signer)

    def localnet_dispenser(self) -> AddressAndSigner:
        acct = get_localnet_default_account(self._client_manager.algod)
        self.set_signer(acct.address, acct.signer)
        return AddressAndSigner(address=acct.address, signer=acct.signer)
