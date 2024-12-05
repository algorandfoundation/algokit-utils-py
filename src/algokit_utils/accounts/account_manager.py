from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from algosdk.account import generate_account
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner
from algosdk.transaction import SuggestedParams
from typing_extensions import Self

from algokit_utils.account import get_dispenser_account, get_kmd_wallet_account, get_localnet_default_account
from algokit_utils.clients.client_manager import ClientManager
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import PaymentParams, TransactionComposer
from algokit_utils.transactions.transaction_sender import SendSingleTransactionResult


@dataclass(frozen=True, kw_only=True)
class AddressAndSigner:
    address: str
    signer: TransactionSigner


@dataclass(frozen=True, kw_only=True)
class EnsureFundedResponse(SendSingleTransactionResult):
    transaction_id: str
    amount_funded: AlgoAmount


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
        (sk, addr) = generate_account()
        signer = AccountTransactionSigner(sk)

        self.set_signer(str(addr), signer)

        return AddressAndSigner(address=str(addr), signer=signer)

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

    def ensure_funded(  # noqa: PLR0913
        self,
        account_fo_fund: str,
        dispenser_account: str,
        min_spending_balance: AlgoAmount,
        min_funding_increment: AlgoAmount,
        # Sender params
        max_rounds_to_wait: int | None = None,
        suppress_log: bool | None = None,
        populate_app_call_resources: bool | None = None,
        # Common txn params
        signer: TransactionSigner | None = None,
        rekey_to: str | None = None,
        note: bytes | None = None,
        lease: bytes | None = None,
        static_fee: AlgoAmount | None = None,
        extra_fee: AlgoAmount | None = None,
        max_fee: AlgoAmount | None = None,
        validity_window: int | None = None,
        first_valid_round: int | None = None,
        last_valid_round: int | None = None,
    ) -> EnsureFundedResponse | None:
        amount_funded = self._get_ensure_funded_amount(account_fo_fund, min_spending_balance, min_funding_increment)

        if not amount_funded:
            return None

        result = (
            self._get_composer()
            .add_payment(
                PaymentParams(
                    sender=dispenser_account,
                    receiver=account_fo_fund,
                    amount=amount_funded,
                    signer=signer,
                    rekey_to=rekey_to,
                    note=note,
                    lease=lease,
                    static_fee=static_fee,
                    extra_fee=extra_fee,
                    max_fee=max_fee,
                    validity_window=validity_window,
                    first_valid_round=first_valid_round,
                    last_valid_round=last_valid_round,
                )
            )
            .send(
                max_rounds_to_wait=max_rounds_to_wait,
                suppress_log=suppress_log,
                populate_app_call_resources=populate_app_call_resources,
            )
        )

        return EnsureFundedResponse(
            returns=result.returns,
            transactions=result.transactions,
            confirmations=result.confirmations,
            tx_ids=result.tx_ids,
            group_id=result.group_id,
            transaction_id=result.tx_ids[0],
            confirmation=result.confirmations[0],
            transaction=result.transactions[0],
            amount_funded=amount_funded,
        )

    def _get_composer(self, get_suggested_params: Callable[[], SuggestedParams] | None = None) -> TransactionComposer:
        if get_suggested_params is None:

            def _get_suggested_params() -> SuggestedParams:
                return self._client_manager.algod.suggested_params()

            get_suggested_params = _get_suggested_params

        return TransactionComposer(
            algod=self._client_manager.algod, get_signer=self.get_signer, get_suggested_params=get_suggested_params
        )

    def _calculate_fund_amount(
        self,
        min_spending_balance: int,
        current_spending_balance: int,
        min_funding_increment: int,
    ) -> int | None:
        if min_spending_balance > current_spending_balance:
            min_fund_amount = min_spending_balance - current_spending_balance
            return max(min_fund_amount, min_funding_increment)
        return None

    def _get_ensure_funded_amount(
        self,
        sender: str,
        min_spending_balance: AlgoAmount,
        min_funding_increment: AlgoAmount | None = None,
    ) -> AlgoAmount | None:
        account_info = self.get_information(sender)
        current_spending_balance = account_info["amount"] - account_info["min-balance"]

        min_increment = min_funding_increment.micro_algo if min_funding_increment else 0
        amount_funded = self._calculate_fund_amount(
            min_spending_balance.micro_algo, current_spending_balance, min_increment
        )

        return AlgoAmount.from_micro_algo(amount_funded) if amount_funded is not None else None
