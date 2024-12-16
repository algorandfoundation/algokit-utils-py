import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from algosdk import mnemonic
from algosdk.atomic_transaction_composer import LogicSigTransactionSigner, TransactionSigner
from algosdk.mnemonic import to_private_key
from algosdk.transaction import LogicSigAccount, SuggestedParams
from typing_extensions import Self

from algokit_utils.accounts.kmd_account_manager import KmdAccountManager
from algokit_utils.clients.client_manager import ClientManager
from algokit_utils.clients.dispenser_api_client import DispenserAssetName, TestNetDispenserApiClient
from algokit_utils.config import config
from algokit_utils.models.account import DISPENSER_ACCOUNT_NAME, Account, MultiSigAccount, MultisigMetadata
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import (
    PaymentParams,
    SendAtomicTransactionComposerResults,
    TransactionComposer,
)
from algokit_utils.transactions.transaction_sender import SendSingleTransactionResult

logger = config.logger


@dataclass(frozen=True, kw_only=True)
class _CommonEnsureFundedParams:
    transaction_id: str
    amount_funded: AlgoAmount


@dataclass(frozen=True, kw_only=True)
class EnsureFundedResponse(SendSingleTransactionResult, _CommonEnsureFundedParams):
    pass


@dataclass(frozen=True, kw_only=True)
class EnsureFundedFromTestnetDispenserApiResponse(_CommonEnsureFundedParams):
    pass


class AccountManager:
    """Creates and keeps track of addresses and signers"""

    def __init__(self, client_manager: ClientManager):
        """
        Create a new account manager.

        :param client_manager: The ClientManager client to use for algod and kmd clients
        """
        self._client_manager = client_manager
        self._kmd_account_manager = KmdAccountManager(client_manager)
        self._signers = dict[str, TransactionSigner]()
        self._default_signer: TransactionSigner | None = None

    def set_default_signer(self, signer: TransactionSigner) -> Self:
        """
        Sets the default signer to use if no other signer is specified.

        :param signer: The signer to use
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
        self._signers[sender] = signer
        return self

    def get_account(self, sender: str) -> Account:
        account = self._signers.get(sender)
        if not account:
            raise ValueError(f"No account found for address {sender}")
        if not isinstance(account, Account):
            raise ValueError(f"Account {sender} is not a regular account")
        return account

    def get_logic_sig_account(self, sender: str) -> LogicSigAccount:
        account = self._signers.get(sender)
        if not account:
            raise ValueError(f"No account found for address {sender}")
        if not isinstance(account, LogicSigAccount):
            raise ValueError(f"Account {sender} is not a logic sig account")
        return account

    def get_signer(self, sender: str | Account | LogicSigAccount) -> TransactionSigner:
        """
        Returns the `TransactionSigner` for the given sender address.

        If no signer has been registered for that address then the default signer is used if registered.

        :param sender: The sender address
        :return: The `TransactionSigner` or throws an error if not found
        """
        signer = self._signers.get(self._get_address(sender))
        if not signer:
            raise ValueError(f"No signer found for address {sender}")
        return signer

    def get_information(self, sender: str | Account) -> dict[str, Any]:
        """
        Returns the given sender account's current status, balance and spendable amounts.

        :param sender: The address of the sender/account to look up
        :return: The account information
        """
        info = self._client_manager.algod.account_info(self._get_address(sender))
        assert isinstance(info, dict)
        return info

    def _register_account(self, private_key: str) -> Account:
        """Helper method to create and register an account with its signer.

        Args:
            private_key: The private key for the account

        Returns:
            The registered Account instance
        """
        account = Account(private_key=private_key)
        self._signers[account.address] = account.signer
        return account

    def _register_logic_sig(self, program: bytes, args: list[bytes] | None = None) -> LogicSigAccount:
        logic_sig = LogicSigAccount(program, args)
        self._signers[logic_sig.address()] = LogicSigTransactionSigner(logic_sig)
        return logic_sig

    def _register_multi_sig(
        self, version: int, threshold: int, addrs: list[str], signing_accounts: list[Account]
    ) -> MultiSigAccount:
        msig_account = MultiSigAccount(
            MultisigMetadata(version=version, threshold=threshold, addresses=addrs),
            signing_accounts,
        )
        self._signers[str(msig_account.address)] = msig_account.signer
        return msig_account

    def from_mnemonic(self, mnemonic: str) -> Account:
        private_key = to_private_key(mnemonic)
        return self._register_account(private_key)

    def from_environment(self, name: str, fund_with: AlgoAmount | None = None) -> Account:
        account_mnemonic = os.getenv(f"{name.upper()}_MNEMONIC")

        if account_mnemonic:
            private_key = mnemonic.to_private_key(account_mnemonic)
            return self._register_account(private_key)

        if self._client_manager.is_local_net():
            kmd_account = self._kmd_account_manager.get_or_create_wallet_account(name, fund_with)
            return self._register_account(kmd_account.private_key)

        raise ValueError(f"Missing environment variable {name.upper()}_MNEMONIC when looking for account {name}")

    def from_kmd(
        self, name: str, predicate: Callable[[dict[str, Any]], bool] | None = None, sender: str | None = None
    ) -> Account:
        kmd_account = self._kmd_account_manager.get_wallet_account(name, predicate, sender)
        if not kmd_account:
            raise ValueError(f"Unable to find KMD account {name}{' with predicate' if predicate else ''}")

        return self._register_account(kmd_account.private_key)

    def logic_sig(self, program: bytes, args: list[bytes] | None = None) -> LogicSigAccount:
        return self._register_logic_sig(program, args)

    def multi_sig(
        self, version: int, threshold: int, addrs: list[str], signing_accounts: list[Account]
    ) -> MultiSigAccount:
        return self._register_multi_sig(version, threshold, addrs, signing_accounts)

    def random(self) -> Account:
        """
        Tracks and returns a new, random Algorand account.

        :return: The account
        """
        account = Account.new_account()
        return self._register_account(account.private_key)

    def localnet_dispenser(self) -> Account:
        kmd_account = self._kmd_account_manager.get_localnet_dispenser_account()
        return self._register_account(kmd_account.private_key)

    def dispenser_from_environment(self) -> Account:
        name = os.getenv(f"{DISPENSER_ACCOUNT_NAME}_MNEMONIC")
        if name:
            return self.from_environment(DISPENSER_ACCOUNT_NAME)
        return self.localnet_dispenser()

    def rekeyed(self, sender: Account | str, account: Account) -> Account:
        sender_address = sender.address if isinstance(sender, Account) else sender
        self._signers[sender_address] = account.signer
        return Account(address=sender_address, private_key=account.private_key)

    def rekey_account(  # noqa: PLR0913
        self,
        account: str | Account,
        rekey_to: str | Account,
        *,
        # Common transaction parameters
        signer: TransactionSigner | None = None,
        note: bytes | None = None,
        lease: bytes | None = None,
        static_fee: AlgoAmount | None = None,
        extra_fee: AlgoAmount | None = None,
        max_fee: AlgoAmount | None = None,
        validity_window: int | None = None,
        first_valid_round: int | None = None,
        last_valid_round: int | None = None,
        suppress_log: bool | None = None,
    ) -> SendAtomicTransactionComposerResults:
        """Rekey an account to a new address.

        Args:
            account: The account to rekey
            rekey_to: The address or account to rekey to
            signer: Optional transaction signer
            note: Optional transaction note
            lease: Optional transaction lease
            static_fee: Optional static fee
            extra_fee: Optional extra fee
            max_fee: Optional max fee
            validity_window: Optional validity window
            first_valid_round: Optional first valid round
            last_valid_round: Optional last valid round
            suppress_log: Optional flag to suppress logging

        Returns:
            The transaction result
        """
        sender_address = self._get_address(account)
        rekey_address = self._get_address(rekey_to)

        result = (
            self._get_composer()
            .add_payment(
                PaymentParams(
                    sender=sender_address,
                    receiver=sender_address,
                    amount=AlgoAmount.from_micro_algo(0),
                    rekey_to=rekey_address,
                    signer=signer,
                    note=note,
                    lease=lease,
                    static_fee=static_fee,
                    extra_fee=extra_fee,
                    max_fee=max_fee,
                    validity_window=validity_window,
                    first_valid_round=first_valid_round,
                    last_valid_round=last_valid_round,
                    suppress_log=suppress_log,
                )
            )
            .send()
        )

        # If rekey_to is a signing account, set it as the signer for this account
        if isinstance(rekey_to, Account):
            self.rekeyed(account, rekey_to)

        if not suppress_log:
            logger.info(f"Rekeyed {sender_address} to {rekey_address} via transaction {result.tx_ids[-1]}")

        return result

    def ensure_funded(  # noqa: PLR0913
        self,
        account_to_fund: str | Account,
        dispenser_account: str | Account,
        min_spending_balance: AlgoAmount,
        min_funding_increment: AlgoAmount | None = None,
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
        account_to_fund = self._get_address(account_to_fund)
        dispenser_account = self._get_address(dispenser_account)
        amount_funded = self._get_ensure_funded_amount(account_to_fund, min_spending_balance, min_funding_increment)

        if not amount_funded:
            return None

        result = (
            self._get_composer()
            .add_payment(
                PaymentParams(
                    sender=dispenser_account,
                    receiver=account_to_fund,
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

    def ensure_funded_from_environment(  # noqa: PLR0913
        self,
        account_to_fund: str | Account,
        min_spending_balance: AlgoAmount,
        *,  # Force remaining params to be keyword-only
        min_funding_increment: AlgoAmount | None = None,
        # SendParams
        max_rounds_to_wait: int | None = None,
        suppress_log: bool | None = None,
        populate_app_call_resources: bool | None = None,
        # Common transaction params (omitting sender)
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
        """Ensure an account is funded from a dispenser account configured in environment.

        Args:
            account_to_fund: Address of account to fund
            min_spending_balance: Minimum spending balance to ensure
            min_funding_increment: Optional minimum funding increment
            max_rounds_to_wait: Optional maximum rounds to wait for transaction
            suppress_log: Optional flag to suppress logging
            populate_app_call_resources: Optional flag to populate app call resources
            signer: Optional transaction signer
            rekey_to: Optional rekey address
            note: Optional transaction note
            lease: Optional transaction lease
            static_fee: Optional static fee
            extra_fee: Optional extra fee
            max_fee: Optional maximum fee
            validity_window: Optional validity window
            first_valid_round: Optional first valid round
            last_valid_round: Optional last valid round

        Returns:
            EnsureFundedResponse if funding was needed, None otherwise
        """
        account_to_fund = self._get_address(account_to_fund)
        dispenser_account = self.dispenser_from_environment()

        amount_funded = self._get_ensure_funded_amount(account_to_fund, min_spending_balance, min_funding_increment)

        if not amount_funded:
            return None

        result = (
            self._get_composer()
            .add_payment(
                PaymentParams(
                    sender=dispenser_account.address,
                    receiver=account_to_fund,
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

    def ensure_funded_from_testnet_dispenser_api(
        self,
        account_to_fund: str | Account,
        dispenser_client: TestNetDispenserApiClient,
        min_spending_balance: AlgoAmount,
        *,  # Force remaining params to be keyword-only
        min_funding_increment: AlgoAmount | None = None,
    ) -> EnsureFundedFromTestnetDispenserApiResponse | None:
        """Ensure an account is funded using the TestNet Dispenser API.

        Args:
            account_to_fund: Address of account to fund
            dispenser_client: Instance of TestNetDispenserApiClient to use for funding
            min_spending_balance: Minimum spending balance to ensure
            min_funding_increment: Optional minimum funding increment

        Returns:
            EnsureFundedResponse if funding was needed, None otherwise

        Raises:
            ValueError: If attempting to fund on non-TestNet network
        """
        account_to_fund = self._get_address(account_to_fund)

        if not self._client_manager.is_test_net():
            raise ValueError("Attempt to fund using TestNet dispenser API on non TestNet network.")

        amount_funded = self._get_ensure_funded_amount(account_to_fund, min_spending_balance, min_funding_increment)

        if not amount_funded:
            return None

        result = dispenser_client.fund(
            address=account_to_fund,
            amount=amount_funded.micro_algo,
            asset_id=DispenserAssetName.ALGO,
        )

        return EnsureFundedFromTestnetDispenserApiResponse(
            transaction_id=result.tx_id,
            amount_funded=AlgoAmount.from_micro_algo(result.amount),
        )

    def _get_address(self, sender: str | Account | LogicSigAccount) -> str:
        match sender:
            case Account():
                return sender.address
            case LogicSigAccount():
                return sender.address()
            case str():
                return sender
            case _:
                raise ValueError(f"Unknown sender type: {type(sender)}")

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
