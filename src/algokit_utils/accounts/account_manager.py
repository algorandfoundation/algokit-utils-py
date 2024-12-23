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

__all__ = [
    "AccountInformation",
    "AccountManager",
    "EnsureFundedFromTestnetDispenserApiResponse",
    "EnsureFundedResponse",
]


@dataclass(frozen=True, kw_only=True)
class _CommonEnsureFundedParams:
    """
    Common parameters for ensure funded responses.
    """

    transaction_id: str
    amount_funded: AlgoAmount


@dataclass(frozen=True, kw_only=True)
class EnsureFundedResponse(SendSingleTransactionResult, _CommonEnsureFundedParams):
    """
    Response from performing an ensure funded call.
    """


@dataclass(frozen=True, kw_only=True)
class EnsureFundedFromTestnetDispenserApiResponse(_CommonEnsureFundedParams):
    """
    Response from performing an ensure funded call using TestNet dispenser API.
    """


@dataclass(frozen=True, kw_only=True)
class AccountInformation:
    """
    Information about an Algorand account's current status, balance and other properties.

    See `https://developer.algorand.org/docs/rest-apis/algod/#account` for detailed field descriptions.

    :param str address: The account's address
    :param int amount: The account's current balance in microAlgos
    :param int amount_without_pending_rewards: The account's balance in microAlgos without the pending rewards
    :param int min_balance: The account's minimum required balance in microAlgos
    :param int pending_rewards: The amount of pending rewards in microAlgos
    :param int rewards: The amount of rewards earned in microAlgos
    :param int round: The round for which this information is relevant
    :param str status: The account's status (e.g., 'Offline', 'Online')
    :param int|None total_apps_opted_in: Number of applications this account has opted into
    :param int|None total_assets_opted_in: Number of assets this account has opted into
    :param int|None total_box_bytes: Total number of box bytes used by this account
    :param int|None total_boxes: Total number of boxes used by this account
    :param int|None total_created_apps: Number of applications created by this account
    :param int|None total_created_assets: Number of assets created by this account
    :param list[dict]|None apps_local_state: Local state of applications this account has opted into
    :param int|None apps_total_extra_pages: Number of extra pages allocated to applications
    :param dict|None apps_total_schema: Total schema for all applications
    :param list[dict]|None assets: Assets held by this account
    :param str|None auth_addr: If rekeyed, the authorized address
    :param int|None closed_at_round: Round when this account was closed
    :param list[dict]|None created_apps: Applications created by this account
    :param list[dict]|None created_assets: Assets created by this account
    :param int|None created_at_round: Round when this account was created
    :param bool|None deleted: Whether this account is deleted
    :param bool|None incentive_eligible: Whether this account is eligible for incentives
    :param int|None last_heartbeat: Last heartbeat round for this account
    :param int|None last_proposed: Last round this account proposed a block
    :param dict|None participation: Participation information for this account
    :param int|None reward_base: Base reward for this account
    :param str|None sig_type: Signature type for this account
    """

    address: str
    amount: int
    amount_without_pending_rewards: int
    min_balance: int
    pending_rewards: int
    rewards: int
    round: int
    status: str
    total_apps_opted_in: int | None = None
    total_assets_opted_in: int | None = None
    total_box_bytes: int | None = None
    total_boxes: int | None = None
    total_created_apps: int | None = None
    total_created_assets: int | None = None
    apps_local_state: list[dict] | None = None
    apps_total_extra_pages: int | None = None
    apps_total_schema: dict | None = None
    assets: list[dict] | None = None
    auth_addr: str | None = None
    closed_at_round: int | None = None
    created_apps: list[dict] | None = None
    created_assets: list[dict] | None = None
    created_at_round: int | None = None
    deleted: bool | None = None
    incentive_eligible: bool | None = None
    last_heartbeat: int | None = None
    last_proposed: int | None = None
    participation: dict | None = None
    reward_base: int | None = None
    sig_type: str | None = None


class AccountManager:
    """
    Creates and keeps track of signing accounts that can sign transactions for a sending address.

    This class provides functionality to create, track, and manage various types of accounts including
    mnemonic-based, rekeyed, multisig, and logic signature accounts.
    """

    def __init__(self, client_manager: ClientManager):
        """
        Create a new account manager.

        :param ClientManager client_manager: The ClientManager client to use for algod and kmd clients

        :example:
        >>> account_manager = AccountManager(client_manager)
        """
        self._client_manager = client_manager
        self._kmd_account_manager = KmdAccountManager(client_manager)
        self._signers = dict[str, TransactionSigner]()
        self._default_signer: TransactionSigner | None = None

    def set_default_signer(self, signer: TransactionSigner) -> Self:
        """
        Sets the default signer to use if no other signer is specified.

        If this isn't set and a transaction needs signing for a given sender
        then an error will be thrown from `get_signer` / `get_account`.

        :param TransactionSigner signer: A `TransactionSigner` signer to use.
        :returns: The `AccountManager` so method calls can be chained

        :example:
        >>> signer_account = account_manager.random()
        >>> account_manager.set_default_signer(signer_account.signer)
        >>> # When signing a transaction, if there is no signer registered for the sender
        >>> # then the default signer will be used
        >>> signer = account_manager.get_signer("{SENDERADDRESS}")
        """
        self._default_signer = signer
        return self

    def set_signer(self, sender: str, signer: TransactionSigner) -> Self:
        """
        Tracks the given `TransactionSigner` against the given sender address for later signing.

        :param str sender: The sender address to use this signer for
        :param TransactionSigner signer: The `TransactionSigner` to sign transactions with for the given sender
        :returns: The `AccountManager` instance for method chaining

        :example:
        >>> account_manager.set_signer("SENDERADDRESS", transaction_signer)
        """
        self._signers[sender] = signer
        return self

    def set_signer_from_account(self, account: Account | LogicSigAccount | MultiSigAccount) -> Self:
        """
        Tracks the given account for later signing.

        Note: If you are generating accounts via the various methods on `AccountManager`
        (like `random`, `from_mnemonic`, `logic_sig`, etc.) then they automatically get tracked.

        :param Account|LogicSigAccount|MultiSigAccount account: The account to register
        :returns: The `AccountManager` instance for method chaining

        :example:
        >>> account_manager = AccountManager(client_manager)
        >>> account_manager.set_signer_from_account(Account.new_account())
        >>> account_manager.set_signer_from_account(LogicSigAccount(program, args))
        >>> account_manager.set_signer_from_account(MultiSigAccount(multisig_params, [account1, account2]))
        """
        if isinstance(account, LogicSigAccount):
            addr = account.address()
            self._signers[addr] = LogicSigTransactionSigner(account)
        else:
            addr = account.address
            self._signers[addr] = account.signer
        return self

    def get_signer(self, sender: str | Account | LogicSigAccount) -> TransactionSigner:
        """
        Returns the `TransactionSigner` for the given sender address.

        If no signer has been registered for that address then the default signer is used if registered.

        :param str|Account|LogicSigAccount sender: The sender address or account
        :returns: The `TransactionSigner`
        :raises ValueError: If no signer is found and no default signer is set

        :example:
        >>> signer = account_manager.get_signer("SENDERADDRESS")
        """
        signer = self._signers.get(self._get_address(sender)) or self._default_signer
        if not signer:
            raise ValueError(f"No signer found for address {sender}")
        return signer

    def get_account(self, sender: str) -> Account:
        """
        Returns the `Account` for the given sender address.

        :param str sender: The sender address
        :returns: The `Account`
        :raises ValueError: If no account is found or if the account is not a regular account

        :example:
        >>> sender = account_manager.random()
        >>> # ...
        >>> # Returns the `Account` for `sender` that has previously been registered
        >>> account = account_manager.get_account(sender)
        """
        account = self._signers.get(sender)
        if not account:
            raise ValueError(f"No account found for address {sender}")
        if not isinstance(account, Account):
            raise ValueError(f"Account {sender} is not a regular account")
        return account

    def get_logic_sig_account(self, sender: str) -> LogicSigAccount:
        """
        Returns the `LogicSigAccount` for the given sender address.

        :param str sender: The sender address
        :returns: The `LogicSigAccount`
        :raises ValueError: If no account is found or if the account is not a logic signature account
        """
        account = self._signers.get(sender)
        if not account:
            raise ValueError(f"No account found for address {sender}")
        if not isinstance(account, LogicSigAccount):
            raise ValueError(f"Account {sender} is not a logic sig account")
        return account

    def get_information(self, sender: str | Account) -> AccountInformation:
        """
        Returns the given sender account's current status, balance and spendable amounts.

        See `<https://developer.algorand.org/docs/rest-apis/algod/#get-v2accountsaddress>`_
        for response data schema details.

        :param str|Account sender: The address of the sender/account to look up
        :returns: The account information

        :example:
        >>> address = "XBYLS2E6YI6XXL5BWCAMOA4GTWHXWENZMX5UHXMRNWWUQ7BXCY5WC5TEPA"
        >>> account_info = account_manager.get_information(address)
        """
        info = self._client_manager.algod.account_info(self._get_address(sender))
        assert isinstance(info, dict)
        info = {k.replace("-", "_"): v for k, v in info.items()}
        return AccountInformation(**info)

    def _register_account(self, private_key: str) -> Account:
        """
        Helper method to create and register an account with its signer.

        :param str private_key: The private key for the account
        :returns: The registered Account instance
        """
        account = Account(private_key=private_key)
        self._signers[account.address] = account.signer
        return account

    def _register_logic_sig(self, program: bytes, args: list[bytes] | None = None) -> LogicSigAccount:
        """
        Helper method to create and register a logic signature account.

        :param bytes program: The bytes that make up the compiled logic signature
        :param list[bytes]|None args: The (binary) arguments to pass into the logic signature
        :returns: The registered LogicSigAccount instance
        """
        logic_sig = LogicSigAccount(program, args)
        self._signers[logic_sig.address()] = LogicSigTransactionSigner(logic_sig)
        return logic_sig

    def _register_multi_sig(
        self, version: int, threshold: int, addrs: list[str], signing_accounts: list[Account]
    ) -> MultiSigAccount:
        """
        Helper method to create and register a multisig account.

        :param int version: The version of the multisig account
        :param int threshold: The threshold number of signatures required
        :param list[str] addrs: The list of addresses that can sign
        :param list[Account] signing_accounts: The list of accounts that are present to sign
        :returns: The registered MultisigAccount instance
        """
        msig_account = MultiSigAccount(
            MultisigMetadata(version=version, threshold=threshold, addresses=addrs),
            signing_accounts,
        )
        self._signers[str(msig_account.address)] = msig_account.signer
        return msig_account

    def from_mnemonic(self, mnemonic: str) -> Account:
        """
        Tracks and returns an Algorand account with secret key loaded by taking the mnemonic secret.

        :param str mnemonic: The mnemonic secret representing the private key of an account
        :returns: The account

        .. warning::
            Be careful how the mnemonic is handled. Never commit it into source control and ideally load it
            from the environment (ideally via a secret storage service) rather than the file system.

        :example:
        >>> account = account_manager.from_mnemonic("mnemonic secret ...")
        """
        private_key = to_private_key(mnemonic)
        return self._register_account(private_key)

    def from_environment(self, name: str, fund_with: AlgoAmount | None = None) -> Account:
        """
        Tracks and returns an Algorand account with private key loaded by convention from environment variables.

        This allows you to write code that will work seamlessly in production and local development (LocalNet)
        without manual config locally (including when you reset the LocalNet).

        :param str name: The name identifier of the account
        :param AlgoAmount|None fund_with: Optional amount to fund the account with when it gets created
        (when targeting LocalNet)
        :returns: The account
        :raises ValueError: If environment variable {NAME}_MNEMONIC is missing when looking for account {NAME}

        .. note::
            Convention:
                * **Non-LocalNet:** will load `{NAME}_MNEMONIC` as a mnemonic secret.
                  If `{NAME}_SENDER` is defined then it will use that for the sender address
                  (i.e. to support rekeyed accounts)
                * **LocalNet:** will load the account from a KMD wallet called {NAME} and if that wallet doesn't exist
                  it will create it and fund the account for you

        :example:
        >>> # If you have a mnemonic secret loaded into `MY_ACCOUNT_MNEMONIC` then you can call:
        >>> account = account_manager.from_environment('MY_ACCOUNT')
        >>> # If that code runs against LocalNet then a wallet called `MY_ACCOUNT` will automatically be created
        >>> # with an account that is automatically funded with the specified amount from the default LocalNet dispenser
        """
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
        """
        Tracks and returns an Algorand account with private key loaded from the given KMD wallet.

        :param str name: The name of the wallet to retrieve an account from
        :param Callable[[dict[str, Any]], bool]|None predicate: Optional filter to use to find the account
        :param str|None sender: Optional sender address to use this signer for (aka a rekeyed account)
        :returns: The account
        :raises ValueError: If unable to find KMD account with given name and predicate

        :example:
        >>> # Get default funded account in a LocalNet:
        >>> defaultDispenserAccount = account.from_kmd('unencrypted-default-wallet',
        ...     lambda a: a.status != 'Offline' and a.amount > 1_000_000_000
        ... )
        """
        kmd_account = self._kmd_account_manager.get_wallet_account(name, predicate, sender)
        if not kmd_account:
            raise ValueError(f"Unable to find KMD account {name}{' with predicate' if predicate else ''}")

        return self._register_account(kmd_account.private_key)

    def logic_sig(self, program: bytes, args: list[bytes] | None = None) -> LogicSigAccount:
        """
        Tracks and returns an account that represents a logic signature.

        :param bytes program: The bytes that make up the compiled logic signature
        :param list[bytes]|None args: Optional (binary) arguments to pass into the logic signature
        :returns: A logic signature account wrapper

        :example:
        >>> account = account.logic_sig(program, [new Uint8Array(3, ...)])
        """
        return self._register_logic_sig(program, args)

    def multi_sig(
        self, version: int, threshold: int, addrs: list[str], signing_accounts: list[Account]
    ) -> MultiSigAccount:
        """
        Tracks and returns an account that supports partial or full multisig signing.

        :param int version: The version of the multisig account
        :param int threshold: The threshold number of signatures required
        :param list[str] addrs: The list of addresses that can sign
        :param list[Account] signing_accounts: The signers that are currently present
        :returns: A multisig account wrapper

        :example:
        >>> account = account_manager.multi_sig(
        ...     version=1,
        ...     threshold=1,
        ...     addrs=["ADDRESS1...", "ADDRESS2..."],
        ...     signing_accounts=[account1, account2]
        ... )
        """
        return self._register_multi_sig(version, threshold, addrs, signing_accounts)

    def random(self) -> Account:
        """
        Tracks and returns a new, random Algorand account.

        :returns: The account

        :example:
        >>> account = account_manager.random()
        """
        account = Account.new_account()
        return self._register_account(account.private_key)

    def localnet_dispenser(self) -> Account:
        """
        Returns an Algorand account with private key loaded for the default LocalNet dispenser account.

        This account can be used to fund other accounts.

        :returns: The account

        :example:
        >>> account = account_manager.localnet_dispenser()
        """
        kmd_account = self._kmd_account_manager.get_localnet_dispenser_account()
        return self._register_account(kmd_account.private_key)

    def dispenser_from_environment(self) -> Account:
        """
        Returns an account (with private key loaded) that can act as a dispenser from environment variables.

        If environment variables are not present, returns the default LocalNet dispenser account.

        :returns: The account

        :example:
        >>> account = account_manager.dispenser_from_environment()
        """
        name = os.getenv(f"{DISPENSER_ACCOUNT_NAME}_MNEMONIC")
        if name:
            return self.from_environment(DISPENSER_ACCOUNT_NAME)
        return self.localnet_dispenser()

    def rekeyed(self, sender: Account | str, account: Account) -> Account:
        """
        Tracks and returns an Algorand account that is a rekeyed version of the given account to a new sender.

        :param Account|str sender: The account or address to use as the sender
        :param Account account: The account to use as the signer for this new rekeyed account
        :returns: The rekeyed account

        :example:
        >>> account = account.from_mnemonic("mnemonic secret ...")
        >>> rekeyed_account = account_manager.rekeyed(account, "SENDERADDRESS...")
        """
        sender_address = sender.address if isinstance(sender, Account) else sender
        self._signers[sender_address] = account.signer
        return Account(address=sender_address, private_key=account.private_key)

    def rekey_account(  # noqa: PLR0913
        self,
        account: str | Account,
        rekey_to: str | Account,
        *,  # Common transaction parameters
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
        """
        Rekey an account to a new address.

        :param str|Account account: The account to rekey
        :param str|Account rekey_to: The address or account to rekey to
        :param TransactionSigner|None signer: Optional transaction signer
        :param bytes|None note: Optional transaction note
        :param bytes|None lease: Optional transaction lease
        :param AlgoAmount|None static_fee: Optional static fee
        :param AlgoAmount|None extra_fee: Optional extra fee
        :param AlgoAmount|None max_fee: Optional max fee
        :param int|None validity_window: Optional validity window
        :param int|None first_valid_round: Optional first valid round
        :param int|None last_valid_round: Optional last valid round
        :param bool|None suppress_log: Optional flag to suppress logging
        :returns: The result of the transaction and the transaction that was sent

        .. warning::
            Please be careful with this function and be sure to read the
            `official rekey guidance <https://developer.algorand.org/docs/get-details/accounts/rekey/>`_.

        :example:
        >>> # Basic example (with string addresses):
        >>> algorand.account.rekey_account({account: "ACCOUNTADDRESS", rekey_to: "NEWADDRESS"})
        >>> # Basic example (with signer accounts):
        >>> algorand.account.rekey_account({account: account1, rekey_to: newSignerAccount})
        >>> # Advanced example:
        >>> algorand.account.rekey_account({
        ...     account: "ACCOUNTADDRESS",
        ...     rekey_to: "NEWADDRESS",
        ...     lease: 'lease',
        ...     note: 'note',
        ...     first_valid_round: 1000,
        ...     validity_window: 10,
        ...     extra_fee: AlgoAmount.from_micro_algo(1000),
        ...     static_fee: AlgoAmount.from_micro_algo(1000),
        ...     max_fee: AlgoAmount.from_micro_algo(3000),
        ...     suppress_log: True,
        ... })
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
        """
        Funds a given account using a dispenser account as a funding source.

        Ensures the given account has a certain amount of Algo free to spend (accounting for
        Algo locked in minimum balance requirement).

        See `<https://developer.algorand.org/docs/get-details/accounts/#minimum-balance>`_ for details.

        :param str|Account account_to_fund: The account to fund
        :param str|Account dispenser_account: The account to use as a dispenser funding source
        :param AlgoAmount min_spending_balance: The minimum balance of Algo that the account
        should have available to spend
        :param AlgoAmount|None min_funding_increment: Optional minimum funding increment
        :param int|None max_rounds_to_wait: Optional maximum rounds to wait for transaction
        :param bool|None suppress_log: Optional flag to suppress logging
        :param bool|None populate_app_call_resources: Optional flag to populate app call resources
        :param TransactionSigner|None signer: Optional transaction signer
        :param str|None rekey_to: Optional rekey address
        :param bytes|None note: Optional transaction note
        :param bytes|None lease: Optional transaction lease
        :param AlgoAmount|None static_fee: Optional static fee
        :param AlgoAmount|None extra_fee: Optional extra fee
        :param AlgoAmount|None max_fee: Optional maximum fee
        :param int|None validity_window: Optional validity window
        :param int|None first_valid_round: Optional first valid round
        :param int|None last_valid_round: Optional last valid round
        :returns: The result of executing the dispensing transaction and the `amountFunded` if funds were needed,
        or None if no funds were needed

        :example:
        >>> # Basic example:
        >>> algorand.account.ensure_funded("ACCOUNTADDRESS", "DISPENSERADDRESS", algokit.algo(1))
        >>> # With configuration:
        >>> algorand.account.ensure_funded(
        ...     "ACCOUNTADDRESS",
        ...     "DISPENSERADDRESS",
        ...     algokit.algo(1),
        ...     min_funding_increment=algokit.algo(2),
        ...     fee=AlgoAmount.from_micro_algo(1000),
        ...     suppress_log=True
        ... )
        """
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
        """
        Ensure an account is funded from a dispenser account configured in environment.

        Uses a dispenser account retrieved from the environment, per the `dispenser_from_environment` method,
        as a funding source such that the given account has a certain amount of Algo free to spend
        (accounting for Algo locked in minimum balance requirement).

        See `<https://developer.algorand.org/docs/get-details/accounts/#minimum-balance>`_ for details.

        :param str|Account account_to_fund: The account to fund
        :param AlgoAmount min_spending_balance: The minimum balance of Algo that the account should have available to
        spend
        :param AlgoAmount|None min_funding_increment: Optional minimum funding increment
        :param int|None max_rounds_to_wait: Optional maximum rounds to wait for transaction
        :param bool|None suppress_log: Optional flag to suppress logging
        :param bool|None populate_app_call_resources: Optional flag to populate app call resources
        :param TransactionSigner|None signer: Optional transaction signer
        :param str|None rekey_to: Optional rekey address
        :param bytes|None note: Optional transaction note
        :param bytes|None lease: Optional transaction lease
        :param AlgoAmount|None static_fee: Optional static fee
        :param AlgoAmount|None extra_fee: Optional extra fee
        :param AlgoAmount|None max_fee: Optional maximum fee
        :param int|None validity_window: Optional validity window
        :param int|None first_valid_round: Optional first valid round
        :param int|None last_valid_round: Optional last valid round
        :returns: The result of executing the dispensing transaction and the `amountFunded` if funds were needed, or
        None if no funds were needed

        .. note::
            The dispenser account is retrieved from the account mnemonic stored in
            process.env.DISPENSER_MNEMONIC and optionally process.env.DISPENSER_SENDER
            if it's a rekeyed account, or against default LocalNet if no environment variables present.

        :example:
        >>> # Basic example:
        >>> algorand.account.ensure_funded_from_environment("ACCOUNTADDRESS", algokit.algo(1))
        >>> # With configuration:
        >>> algorand.account.ensure_funded_from_environment(
        ...     "ACCOUNTADDRESS",
        ...     algokit.algo(1),
        ...     min_funding_increment=algokit.algo(2),
        ...     fee=AlgoAmount.from_micro_algo(1000),
        ...     suppress_log=True
        ... )
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
        """
        Ensure an account is funded using the TestNet Dispenser API.

        Uses the TestNet Dispenser API as a funding source such that the account has a certain amount
        of Algo free to spend (accounting for Algo locked in minimum balance requirement).

        See `<https://developer.algorand.org/docs/get-details/accounts/#minimum-balance>`_ for details.

        :param str|Account account_to_fund: The account to fund
        :param TestNetDispenserApiClient dispenser_client: The TestNet dispenser funding client
        :param AlgoAmount min_spending_balance: The minimum balance of Algo that the account should have
        available to spend
        :param AlgoAmount|None min_funding_increment: Optional minimum funding increment
        :returns: The result of executing the dispensing transaction and the `amountFunded` if funds were needed, or
        None if no funds were needed
        :raises ValueError: If attempting to fund on non-TestNet network

        :example:
        >>> # Basic example:
        >>> algorand.account.ensure_funded_from_testnet_dispenser_api(
        ...     "ACCOUNTADDRESS",
        ...     algorand.client.get_testnet_dispenser_from_environment(),
        ...     algokit.algo(1)
        ... )
        >>> # With configuration:
        >>> algorand.account.ensure_funded_from_testnet_dispenser_api(
        ...     "ACCOUNTADDRESS",
        ...     algorand.client.get_testnet_dispenser_from_environment(),
        ...     algokit.algo(1),
        ...     min_funding_increment=algokit.algo(2)
        ... )
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
        current_spending_balance = account_info.amount - account_info.min_balance

        min_increment = min_funding_increment.micro_algo if min_funding_increment else 0
        amount_funded = self._calculate_fund_amount(
            min_spending_balance.micro_algo, current_spending_balance, min_increment
        )

        return AlgoAmount.from_micro_algo(amount_funded) if amount_funded is not None else None
