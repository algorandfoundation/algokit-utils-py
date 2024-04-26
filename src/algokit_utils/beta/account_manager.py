from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from algokit_utils.account import get_dispenser_account, get_kmd_wallet_account, get_localnet_default_account
from algosdk.account import generate_account
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner
from typing_extensions import Self

from .client_manager import ClientManager


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

    # TODO
    # def from_mnemonic(self, mnemonic_secret: str, sender: Optional[str] = None) -> AddrAndSigner:
    #     """
    #     Tracks and returns an Algorand account with secret key loaded (i.e. that can sign transactions) by taking the mnemonic secret.

    #     Example:
    #         account = account.from_mnemonic("mnemonic secret ...")
    #         rekeyed_account = account.from_mnemonic("mnemonic secret ...", "SENDERADDRESS...")

    #     :param mnemonic_secret: The mnemonic secret representing the private key of an account; **Note: Be careful how the mnemonic is handled**,
    #         never commit it into source control and ideally load it from the environment (ideally via a secret storage service) rather than the file system.
    #     :param sender: The optional sender address to use this signer for (aka a rekeyed account)
    #     :return: The account
    #     """
    #     account = mnemonic_account(mnemonic_secret)
    #     return self.signer_account(rekeyed_account(account, sender) if sender else account)

    def from_kmd(
        self,
        name: str,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
    ) -> AddressAndSigner:
        """
        Tracks and returns an Algorand account with private key loaded from the given KMD wallet (identified by name).

        Example (Get default funded account in a LocalNet):
            default_dispenser_account = account.from_kmd('unencrypted-default-wallet',
                lambda a: a['status'] != 'Offline' and a['amount'] > 1_000_000_000
            )

        :param name: The name of the wallet to retrieve an account from
        :param predicate: An optional filter to use to find the account (otherwise it will return a random account from the wallet)
        :return: The account
        """
        account = get_kmd_wallet_account(
            name=name, predicate=predicate, client=self._client_manager.algod, kmd_client=self._client_manager.kmd
        )
        if not account:
            raise ValueError(f"Unable to find KMD account {name}{' with predicate' if predicate else ''}")

        self.set_signer(account.address, account.signer)
        return AddressAndSigner(address=account.address, signer=account.signer)

    # TODO
    # def multisig(
    #     self, multisig_params: algosdk.MultisigMetadata, signing_accounts: Union[algosdk.Account, SigningAccount]
    # ) -> TransactionSignerAccount:
    #     """
    #     Tracks and returns an account that supports partial or full multisig signing.

    #     Example:
    #         account = account.multisig(
    #             {
    #                 "version": 1,
    #                 "threshold": 1,
    #                 "addrs": ["ADDRESS1...", "ADDRESS2..."]
    #             },
    #             account.from_environment('ACCOUNT1')
    #         )

    #     :param multisig_params: The parameters that define the multisig account
    #     :param signing_accounts: The signers that are currently present
    #     :return: A multisig account wrapper
    #     """
    #     return self.signer_account(multisig_account(multisig_params, signing_accounts))

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
        """
        Returns an Algorand account with private key loaded for the default LocalNet dispenser account (that can be used to fund other accounts).

        Example:
            account = account.localnet_dispenser()

        :return: The account
        """
        acct = get_localnet_default_account(self._client_manager.algod)
        self.set_signer(acct.address, acct.signer)
        return AddressAndSigner(address=acct.address, signer=acct.signer)
