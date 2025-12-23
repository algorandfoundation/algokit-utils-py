import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import nacl.signing
from typing_extensions import Never, Self

from algokit_algo25 import seed_from_mnemonic
from algokit_algod_client import models as algod_models
from algokit_common.serde import to_wire
from algokit_transact.logicsig import LogicSig
from algokit_transact.signer import (
    AddressWithSigners,
    AddressWithTransactionSigner,
    TransactionSigner,
    generate_address_with_signers,
)
from algokit_utils.accounts.kmd_account_manager import KmdAccountManager
from algokit_utils.clients.client_manager import ClientManager
from algokit_utils.clients.dispenser_api_client import TestNetDispenserApiClient
from algokit_utils.config import config
from algokit_utils.models.account import (
    DISPENSER_ACCOUNT_NAME,
    LogicSigAccount,
    MultisigAccount,
    MultisigMetadata,
)
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.models.transaction import SendParams
from algokit_utils.transactions.transaction_composer import (
    PaymentParams,
    SendTransactionComposerResults,
    TransactionComposer,
    TransactionComposerParams,
)
from algokit_utils.transactions.transaction_sender import SendSingleTransactionResult

__all__ = [
    "AccountInformation",
    "AccountManager",
    "EnsureFundedFromTestnetDispenserApiResult",
    "EnsureFundedResult",
]


@dataclass(frozen=True, kw_only=True)
class _CommonEnsureFundedParams:
    """
    Common parameters for ensure funded responses.
    """

    transaction_id: str
    """The transaction ID of the funded transaction"""
    amount_funded: AlgoAmount
    """The amount of Algos funded"""


@dataclass(frozen=True, kw_only=True)
class EnsureFundedResult(SendSingleTransactionResult, _CommonEnsureFundedParams):
    """
    Result from performing an ensure funded call.
    """


@dataclass(frozen=True, kw_only=True)
class EnsureFundedFromTestnetDispenserApiResult(_CommonEnsureFundedParams):
    """
    Result from performing an ensure funded call using TestNet dispenser API.
    """


@dataclass(frozen=True, kw_only=True)
class AccountInformation:
    """
    Information about an Algorand account's current status, balance and other properties.

    See `https://dev.algorand.co/reference/rest-apis/algod/#account` for detailed field descriptions.
    """

    address: str
    """The account's address"""
    amount: AlgoAmount
    """The account's current balance"""
    amount_without_pending_rewards: AlgoAmount
    """The account's balance without the pending rewards"""
    min_balance: AlgoAmount
    """The account's minimum required balance"""
    pending_rewards: AlgoAmount
    """The amount of pending rewards"""
    rewards: AlgoAmount
    """The amount of rewards earned"""
    round: int
    """The round for which this information is relevant"""
    status: str
    """The account's status (e.g., 'Offline', 'Online')"""
    total_apps_opted_in: int | None = None
    """Number of applications this account has opted into"""
    total_assets_opted_in: int | None = None
    """Number of assets this account has opted into"""
    total_box_bytes: int | None = None
    """Total number of box bytes used by this account"""
    total_boxes: int | None = None
    """Total number of boxes used by this account"""
    total_created_apps: int | None = None
    """Number of applications created by this account"""
    total_created_assets: int | None = None
    """Number of assets created by this account"""
    apps_local_state: list[dict] | None = None
    """Local state of applications this account has opted into"""
    apps_total_extra_pages: int | None = None
    """Number of extra pages allocated to applications"""
    apps_total_schema: dict | None = None
    """Total schema for all applications"""
    assets: list[dict] | None = None
    """Assets held by this account"""
    auth_addr: str | None = None
    """If rekeyed, the authorized address"""
    closed_at_round: int | None = None
    """Round when this account was closed"""
    created_apps: list[dict] | None = None
    """Applications created by this account"""
    created_assets: list[dict] | None = None
    """Assets created by this account"""
    created_at_round: int | None = None
    """Round when this account was created"""
    deleted: bool | None = None
    """Whether this account is deleted"""
    incentive_eligible: bool | None = None
    """Whether this account is eligible for incentives"""
    last_heartbeat: int | None = None
    """Last heartbeat round for this account"""
    last_proposed: int | None = None
    """Last round this account proposed a block"""
    participation: dict | None = None
    """Participation information for this account"""
    reward_base: int | None = None
    """Base reward for this account"""
    sig_type: str | None = None
    """Signature type for this account"""


# Type alias for accounts that can be stored in the account manager
StoredAccountType = AddressWithSigners | LogicSigAccount | MultisigAccount


class AccountManager:
    """
    Creates and keeps track of signing accounts that can sign transactions for a sending address.

    This class provides functionality to create, track, and manage various types of accounts including
    mnemonic-based, rekeyed, multisig, and logic signature accounts.

    :param client_manager: The ClientManager client to use for algod and kmd clients

    :example:
        >>> account_manager = AccountManager(client_manager)
    """

    def __init__(self, client_manager: ClientManager):
        self._client_manager = client_manager
        self._kmd_account_manager = KmdAccountManager(client_manager)
        self._accounts: dict[str, StoredAccountType | AddressWithTransactionSigner] = {}
        self._default_signer: TransactionSigner | None = None

    @property
    def kmd(self) -> KmdAccountManager:
        """
        KMD account manager that allows you to easily get and create accounts using KMD.

        :return KmdAccountManager: The 'KmdAccountManager' instance
        :example:
            >>> kmd_manager = account_manager.kmd
        """
        return self._kmd_account_manager

    def _signer_account(self, account: StoredAccountType) -> AddressWithSigners:
        """
        Register account and return AddressWithSigners.

        Records the given account against its address for later retrieval and returns
        an AddressWithSigners object.

        :param account: The account to register (AddressWithSigners, LogicSigAccount, or MultisigAccount)
        :returns: AddressWithSigners for the account
        """
        # Get the address from the account
        addr = account.addr

        # Store the account
        self._accounts[addr] = account

        # If it's already AddressWithSigners, return it directly
        if isinstance(account, AddressWithSigners):
            return account

        return AddressWithSigners(
            addr=addr,
            signer=account.signer,
            delegated_lsig_signer=_placeholder_lsig_signer,
            program_data_signer=_placeholder_program_data_signer,
            bytes_signer=_placeholder_bytes_signer,
            mx_bytes_signer=_placeholder_mx_bytes_signer,
        )

    def set_default_signer(self, signer: TransactionSigner | AddressWithTransactionSigner) -> Self:
        """
        Sets the default signer to use if no other signer is specified.

        If this isn't set and a transaction needs signing for a given sender
        then an error will be thrown from `get_signer` / `get_account`.

        :param signer: A `TransactionSigner` signer to use.
        :returns: The `AccountManager` so method calls can be chained

        :example:
            >>> signer_account = account_manager.random()
            >>> account_manager.set_default_signer(signer_account)
        """
        # Check if signer is an AddressWithTransactionSigner (has .signer property) or is just a callable
        if isinstance(signer, AddressWithTransactionSigner):
            self._default_signer = signer.signer
        else:
            self._default_signer = signer
        return self

    def set_signer(self, sender: str, signer: TransactionSigner) -> Self:
        """
        Tracks the given `TransactionSigner` against the given sender address for later signing.

        :param sender: The sender address to use this signer for
        :param signer: The `TransactionSigner` to sign transactions with for the given sender
        :returns: The `AccountManager` instance for method chaining

        :example:
            >>> account_manager.set_signer("SENDERADDRESS", transaction_signer)
        """

        self._accounts[sender] = AddressWithSigners(
            addr=sender,
            signer=signer,
            delegated_lsig_signer=_placeholder_lsig_signer,
            program_data_signer=_placeholder_program_data_signer,
            bytes_signer=_placeholder_bytes_signer,
            mx_bytes_signer=_placeholder_mx_bytes_signer,
        )
        return self

    def set_signers(self, *, another_account_manager: "AccountManager", overwrite_existing: bool = True) -> Self:
        """
        Merges the given `AccountManager` into this one.

        :param another_account_manager: The `AccountManager` to merge into this one
        :param overwrite_existing: Whether to overwrite existing signers in this manager
        :returns: The `AccountManager` instance for method chaining

        :example:
            >>> accountManager2.set_signers(accountManager1)
        """
        self._accounts = (
            {**self._accounts, **another_account_manager._accounts}  # noqa: SLF001
            if overwrite_existing
            else {**another_account_manager._accounts, **self._accounts}  # noqa: SLF001
        )
        return self

    def set_signer_from_account(
        self,
        *args: AddressWithTransactionSigner,
        **kwargs: AddressWithTransactionSigner,
    ) -> Self:
        """
        Tracks the given account for later signing.

        Note: If you are generating accounts via the various methods on `AccountManager`
        (like `random`, `from_mnemonic`, `logic_sig`, etc.) then they automatically get tracked.

        The method accepts either a positional argument or a keyword argument named 'account' or 'signer'.
        The 'signer' parameter is deprecated and will show a warning when used.

        :param *args: Variable positional arguments. The first argument should be a AddressWithTransactionSigner.
        :param **kwargs: Variable keyword arguments. Can include 'account' or 'signer' (deprecated) as
            AddressWithTransactionSigner.
        :returns: The `AccountManager` instance for method chaining
        :raises ValueError: If no account or signer argument is provided

        :example:
            >>> account_manager = AccountManager(client_manager)
            >>> # Using positional argument
            >>> account_manager.set_signer_from_account(
            ...     AddressWithSigners(...)
            ... )
            >>> # Using keyword argument 'account'
            >>> account_manager.set_signer_from_account(
            ...     account=LogicSigAccount(AlgosdkLogicSigAccount(program, args))
            ... )
            >>> # Using deprecated keyword argument 'signer'
            >>> account_manager.set_signer_from_account(
            ...     signer=MultisigAccount(multisig_params, [account1, account2])
            ... )
        """
        # Extract the account from either positional args or keyword args
        if args:
            account_obj = args[0]
        elif "account" in kwargs:
            account_obj = kwargs["account"]
        elif "signer" in kwargs:
            account_obj = kwargs["signer"]
        else:
            raise ValueError("Missing required argument: either 'account' or 'signer'")

        self._accounts[account_obj.addr] = account_obj
        return self

    def get_signer(self, sender: str | AddressWithTransactionSigner) -> TransactionSigner:
        """
        Returns the `TransactionSigner` for the given sender address.

        If no signer has been registered for that address then the default signer is used if registered.

        :param sender: The sender address or account
        :returns: The `TransactionSigner`
        :raises ValueError: If no signer is found and no default signer is set
        :raises TypeError: If a registered signer has an unexpected type

        :example:
            >>> signer = account_manager.get_signer("SENDERADDRESS")
        """
        signer_or_account = self._accounts.get(self._get_address(sender)) or self._default_signer
        if not signer_or_account:
            raise ValueError(f"No signer found for address {sender}")
        # Check for AddressWithSigners first (uses .addr and .signer, not .address)
        if isinstance(signer_or_account, AddressWithSigners):
            return signer_or_account.signer
        if isinstance(signer_or_account, AddressWithTransactionSigner):
            return signer_or_account.signer
        # Assume it's a TransactionSigner callable
        if callable(signer_or_account):
            return signer_or_account
        raise TypeError(f"Unexpected signer type {type(signer_or_account)}")

    def get_account(self, sender: str) -> StoredAccountType | AddressWithTransactionSigner:
        """
        Returns the registered account for the given sender address.

        :param sender: The sender address
        :returns: The registered account (AddressWithSigners, LogicSigAccount, MultisigAccount,
            or AddressWithTransactionSigner)
        :raises ValueError: If no account is found for the address

        :example:
            >>> sender = account_manager.random().addr
            >>> # ...
            >>> # Returns the account for `sender` that has previously been registered
            >>> account = account_manager.get_account(sender)
        """
        account = self._accounts.get(sender)
        if not account:
            raise ValueError(f"No account found for address {sender}")
        return account

    def get_information(self, sender: str | AddressWithTransactionSigner) -> AccountInformation:
        """
        Returns the given sender account's current status, balance and spendable amounts.

        See `<https://dev.algorand.co/reference/rest-apis/algod/#account>`_
        for response data schema details.

        :param sender: The address or account compliant with `AddressWithTransactionSigner` protocol to look up
        :returns: The account information

        :example:
            >>> address = "XBYLS2E6YI6XXL5BWCAMOA4GTWHXWENZMX5UHXMRNWWUQ7BXCY5WC5TEPA"
            >>> account_info = account_manager.get_information(address)
        """
        account_info = self._client_manager.algod.account_information(self._get_address(sender))
        return self._build_account_information(account_info)

    def _build_account_information(self, account_info: algod_models.Account) -> AccountInformation:
        """Convert a typed algod account model into an AccountInformation dataclass."""
        return AccountInformation(
            address=account_info.address,
            amount=AlgoAmount.from_micro_algo(account_info.amount),
            amount_without_pending_rewards=AlgoAmount.from_micro_algo(account_info.amount_without_pending_rewards),
            min_balance=AlgoAmount.from_micro_algo(account_info.min_balance),
            pending_rewards=AlgoAmount.from_micro_algo(account_info.pending_rewards),
            rewards=AlgoAmount.from_micro_algo(account_info.rewards),
            round=account_info.round_,
            status=account_info.status,
            total_apps_opted_in=account_info.total_apps_opted_in,
            total_assets_opted_in=account_info.total_assets_opted_in,
            total_box_bytes=getattr(account_info, "total_box_bytes", None),
            total_boxes=getattr(account_info, "total_boxes", None),
            total_created_apps=account_info.total_created_apps,
            total_created_assets=account_info.total_created_assets,
            apps_local_state=[to_wire(app) for app in account_info.apps_local_state]
            if account_info.apps_local_state
            else None,
            apps_total_extra_pages=account_info.apps_total_extra_pages,
            apps_total_schema=to_wire(account_info.apps_total_schema) if account_info.apps_total_schema else None,
            assets=[to_wire(asset) for asset in account_info.assets] if account_info.assets else None,
            auth_addr=account_info.auth_addr,
            closed_at_round=getattr(account_info, "closed_at_round", None),
            created_apps=[to_wire(app) for app in account_info.created_apps] if account_info.created_apps else None,
            created_assets=[to_wire(asset) for asset in account_info.created_assets]
            if account_info.created_assets
            else None,
        )

    def from_mnemonic(self, *, mnemonic: str, sender: str | None = None) -> AddressWithSigners:
        """
        Tracks and returns an Algorand account with secret key loaded by taking the mnemonic secret.

        :param mnemonic: The mnemonic secret representing the private key of an account
        :param sender: Optional address to use as the sender (for rekeyed accounts)
        :returns: The account as AddressWithSigners

        .. warning::
            Be careful how the mnemonic is handled. Never commit it into source control and ideally load it
            from the environment (ideally via a secret storage service) rather than the file system.

        :example:
            >>> account = account_manager.from_mnemonic("mnemonic secret ...")
        """
        seed = seed_from_mnemonic(mnemonic)
        signing_key = nacl.signing.SigningKey(seed)
        public_key = signing_key.verify_key.encode()

        def raw_signer(bytes_to_sign: bytes) -> bytes:
            return signing_key.sign(bytes_to_sign).signature

        account = generate_address_with_signers(
            ed25519_pubkey=public_key,
            raw_ed25519_signer=raw_signer,
            sending_address=sender,
        )
        return self._signer_account(account)

    def from_environment(self, name: str, fund_with: AlgoAmount | None = None) -> AddressWithSigners:
        """
        Tracks and returns an Algorand account with private key loaded by convention from environment variables.

        This allows you to write code that will work seamlessly in production and local development (LocalNet)
        without manual config locally (including when you reset the LocalNet).

        :param name: The name identifier of the account
        :param fund_with: Optional amount to fund the account with when it gets created
            (when targeting LocalNet)
        :returns: The account as AddressWithSigners
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
            >>> # with an account that is automatically funded with the specified amount from the LocalNet dispenser
        """
        account_mnemonic = os.getenv(f"{name.upper()}_MNEMONIC")
        sender = os.getenv(f"{name.upper()}_SENDER")

        if account_mnemonic:
            return self.from_mnemonic(mnemonic=account_mnemonic, sender=sender)

        if self._client_manager.is_localnet():
            kmd_account = self._kmd_account_manager.get_or_create_wallet_account(name, fund_with)
            return self._signer_account(kmd_account)

        raise ValueError(f"Missing environment variable {name.upper()}_MNEMONIC when looking for account {name}")

    def from_kmd(
        self, name: str, predicate: Callable[[dict[str, Any]], bool] | None = None, sender: str | None = None
    ) -> AddressWithSigners:
        """
        Tracks and returns an Algorand account with private key loaded from the given KMD wallet.

        :param name: The name of the wallet to retrieve an account from
        :param predicate: Optional filter to use to find the account
        :param sender: Optional sender address to use this signer for (aka a rekeyed account)
        :returns: The account as AddressWithSigners
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

        return self._signer_account(kmd_account)

    def logicsig(self, program: bytes, args: Sequence[bytes] = ()) -> AddressWithSigners:
        """
        Tracks and returns an account that represents a logic signature.

        :param program: The bytes that make up the compiled logic signature
        :param args: Optional (binary) arguments to pass into the logic signature
        :returns: An AddressWithSigners wrapper for the logic signature account

        :example:
            >>> account = account_manager.logicsig(program, [b"arg1", b"arg2"])
        """
        logic_sig = LogicSigAccount(logic=program, args=args)
        return self._signer_account(logic_sig)

    def multisig(self, metadata: MultisigMetadata, sub_signers: Sequence[AddressWithSigners]) -> AddressWithSigners:
        """
        Tracks and returns an account that supports partial or full multisig signing.

        :param metadata: The metadata for the multisig account
        :param sub_signers: The signers that are currently present
        :returns: An AddressWithSigners wrapper for the multisig account

        :example:
            >>> account = account_manager.multi_sig(
            ...     version=1,
            ...     threshold=1,
            ...     addrs=["ADDRESS1...", "ADDRESS2..."],
            ...     sub_signers=[account1, account2]
            ... )
        """
        msig_account = MultisigAccount(metadata, sub_signers)
        return self._signer_account(msig_account)

    def random(self) -> AddressWithSigners:
        """
        Tracks and returns a new, random Algorand account.

        :returns: The account as AddressWithSigners

        :example:
            >>> account = account_manager.random()
        """
        # Generate random keypair using nacl
        keypair = nacl.signing.SigningKey.generate()
        public_key = keypair.verify_key.encode()

        def raw_signer(bytes_to_sign: bytes) -> bytes:
            return keypair.sign(bytes_to_sign).signature

        account = generate_address_with_signers(
            ed25519_pubkey=public_key,
            raw_ed25519_signer=raw_signer,
        )
        return self._signer_account(account)

    def localnet_dispenser(self) -> AddressWithSigners:
        """
        Returns an Algorand account with private key loaded for the default LocalNet dispenser account.

        This account can be used to fund other accounts.

        :returns: The account as AddressWithSigners

        :example:
            >>> account = account_manager.localnet_dispenser()
        """
        kmd_account = self._kmd_account_manager.get_localnet_dispenser_account()
        return self._signer_account(kmd_account)

    def dispenser_from_environment(self) -> AddressWithSigners:
        """
        Returns an account (with private key loaded) that can act as a dispenser from environment variables.

        If environment variables are not present, returns the default LocalNet dispenser account.

        :returns: The account as AddressWithSigners

        :example:
            >>> account = account_manager.dispenser_from_environment()
        """
        name = os.getenv(f"{DISPENSER_ACCOUNT_NAME}_MNEMONIC")
        if name:
            return self.from_environment(DISPENSER_ACCOUNT_NAME)
        return self.localnet_dispenser()

    def rekeyed(self, *, sender: str, account: AddressWithTransactionSigner | AddressWithSigners) -> AddressWithSigners:
        """
        Tracks and returns an Algorand account that is a rekeyed version of the given account to a new sender.

        :param sender: The address to use as the sender
        :param account: The account to use as the signer for this new rekeyed account
        :returns: The rekeyed account as AddressWithSigners

        :example:
            >>> account = account.from_mnemonic("mnemonic secret ...")
            >>> rekeyed_account = account_manager.rekeyed(account, "SENDERADDRESS...")
        """

        rekeyed_account = AddressWithSigners(
            addr=sender,
            signer=account.signer,
            delegated_lsig_signer=_placeholder_lsig_signer,
            program_data_signer=_placeholder_program_data_signer,
            bytes_signer=_placeholder_bytes_signer,
            mx_bytes_signer=_placeholder_mx_bytes_signer,
        )

        self._accounts[sender] = rekeyed_account
        return rekeyed_account

    def rekey_account(  # noqa: PLR0913
        self,
        account: str,
        rekey_to: str | AddressWithTransactionSigner,
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
    ) -> SendTransactionComposerResults:
        """
        Rekey an account to a new address.

        :param account: The account to rekey
        :param rekey_to: The address or account to rekey to
        :param signer: Optional transaction signer
        :param note: Optional transaction note
        :param lease: Optional transaction lease
        :param static_fee: Optional static fee
        :param extra_fee: Optional extra fee
        :param max_fee: Optional max fee
        :param validity_window: Optional validity window
        :param first_valid_round: Optional first valid round
        :param last_valid_round: Optional last valid round
        :param suppress_log: Optional flag to suppress logging
        :returns: The result of the transaction and the transaction that was sent

        .. warning::
            Please be careful with this function and be sure to read the
            `official rekey guidance <https://dev.algorand.co/concepts/accounts/rekeying>`_.

        :example:
            >>> # Basic example (with string addresses):
            >>> algorand.account.rekey_account("ACCOUNTADDRESS", "NEWADDRESS")
            >>> # Basic example (with signer accounts):
            >>> algorand.account.rekey_account(account1, newSignerAccount)
            >>> # Advanced example:
            >>> algorand.account.rekey_account(
            ...     account="ACCOUNTADDRESS",
            ...     rekey_to="NEWADDRESS",
            ...     lease='lease',
            ...     note='note',
            ...     first_valid_round=1000,
            ...     validity_window=10,
            ...     extra_fee=AlgoAmount.from_micro_algo(1000),
            ...     static_fee=AlgoAmount.from_micro_algo(1000),
            ...     max_fee=AlgoAmount.from_micro_algo(3000),
            ...     suppress_log=True,
            ... )
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
                )
            )
            .send()
        )

        # If rekey_to is a signing account, set it as the signer for this account
        if isinstance(rekey_to, AddressWithTransactionSigner | AddressWithSigners):
            self.rekeyed(sender=account, account=rekey_to)

        if not suppress_log:
            config.logger.info(f"Rekeyed {sender_address} to {rekey_address} via transaction {result.tx_ids[-1]}")

        return result

    def ensure_funded(  # noqa: PLR0913
        self,
        account_to_fund: str | AddressWithTransactionSigner | AddressWithSigners,
        dispenser_account: str | AddressWithTransactionSigner | AddressWithSigners,
        min_spending_balance: AlgoAmount,
        min_funding_increment: AlgoAmount | None = None,
        # Sender params
        send_params: SendParams | None = None,
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
    ) -> EnsureFundedResult | None:
        """
        Funds a given account using a dispenser account as a funding source.

        Ensures the given account has a certain amount of Algo free to spend (accounting for
        Algo locked in minimum balance requirement).

        See `<https://dev.algorand.co/concepts/smart-contracts/costs-constraints#mbr>`_ for details.

        :param account_to_fund: The account to fund
        :param dispenser_account: The account to use as a dispenser funding source
        :param min_spending_balance: The minimum balance of Algo that the account
            should have available to spend
        :param min_funding_increment: Optional minimum funding increment
        :param send_params: Parameters for the send operation, defaults to None
        :param signer: Optional transaction signer
        :param rekey_to: Optional rekey address
        :param note: Optional transaction note
        :param lease: Optional transaction lease
        :param static_fee: Optional static fee
        :param extra_fee: Optional extra fee
        :param max_fee: Optional maximum fee
        :param validity_window: Optional validity window
        :param first_valid_round: Optional first valid round
        :param last_valid_round: Optional last valid round
        :returns: The result of executing the dispensing transaction and the `amountFunded` if funds were needed,
            or None if no funds were needed

        :example:
            >>> # Basic example:
            >>> algorand.account.ensure_funded("ACCOUNTADDRESS", "DISPENSERADDRESS", AlgoAmount.from_algo(1))
            >>> # With configuration:
            >>> algorand.account.ensure_funded(
            ...     "ACCOUNTADDRESS",
            ...     "DISPENSERADDRESS",
            ...     AlgoAmount.from_algo(1),
            ...     min_funding_increment=AlgoAmount.from_algo(2),
            ...     fee=AlgoAmount.from_micro_algo(1000),
            ...     suppress_log=True
            ... )
        """
        account_to_fund_addr = self._get_address(account_to_fund)
        dispenser_account_addr = self._get_address(dispenser_account)
        amount_funded = self._get_ensure_funded_amount(
            account_to_fund_addr, min_spending_balance, min_funding_increment
        )

        if not amount_funded:
            return None

        result = (
            self._get_composer()
            .add_payment(
                PaymentParams(
                    sender=dispenser_account_addr,
                    receiver=account_to_fund_addr,
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
            .send(send_params)
        )

        base_result = SendSingleTransactionResult.from_composer_result(result)
        return EnsureFundedResult(
            **vars(base_result),
            transaction_id=base_result.tx_id or result.tx_ids[0],
            amount_funded=amount_funded,
        )

    def ensure_funded_from_environment(  # noqa: PLR0913
        self,
        account_to_fund: str | AddressWithTransactionSigner | AddressWithSigners,
        min_spending_balance: AlgoAmount,
        *,  # Force remaining params to be keyword-only
        min_funding_increment: AlgoAmount | None = None,
        # SendParams
        send_params: SendParams | None = None,
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
    ) -> EnsureFundedResult | None:
        """
        Ensure an account is funded from a dispenser account configured in environment.

        Uses a dispenser account retrieved from the environment, per the `dispenser_from_environment` method,
        as a funding source such that the given account has a certain amount of Algo free to spend
        (accounting for Algo locked in minimum balance requirement).

        See `<https://dev.algorand.co/concepts/smart-contracts/costs-constraints#mbr>`_ for details.

        :param account_to_fund: The account to fund
        :param min_spending_balance: The minimum balance of Algo that the account should have available to
            spend
        :param min_funding_increment: Optional minimum funding increment
        :param send_params: Parameters for the send operation, defaults to None
        :param signer: Optional transaction signer
        :param rekey_to: Optional rekey address
        :param note: Optional transaction note
        :param lease: Optional transaction lease
        :param static_fee: Optional static fee
        :param extra_fee: Optional extra fee
        :param max_fee: Optional maximum fee
        :param validity_window: Optional validity window
        :param first_valid_round: Optional first valid round
        :param last_valid_round: Optional last valid round
        :returns: The result of executing the dispensing transaction and the `amountFunded` if funds were needed, or
            None if no funds were needed

        .. note::
            The dispenser account is retrieved from the account mnemonic stored in
            process.env.DISPENSER_MNEMONIC and optionally process.env.DISPENSER_SENDER
            if it's a rekeyed account, or against default LocalNet if no environment variables present.

        :example:
            >>> # Basic example:
            >>> algorand.account.ensure_funded_from_environment("ACCOUNTADDRESS", AlgoAmount.from_algo(1))
            >>> # With configuration:
            >>> algorand.account.ensure_funded_from_environment(
            ...     "ACCOUNTADDRESS",
            ...     AlgoAmount.from_algo(1),
            ...     min_funding_increment=AlgoAmount.from_algo(2),
            ...     fee=AlgoAmount.from_micro_algo(1000),
            ...     suppress_log=True
            ... )
        """
        account_to_fund_addr = self._get_address(account_to_fund)
        dispenser_account = self.dispenser_from_environment()

        amount_funded = self._get_ensure_funded_amount(
            account_to_fund_addr, min_spending_balance, min_funding_increment
        )

        if not amount_funded:
            return None

        result = (
            self._get_composer()
            .add_payment(
                PaymentParams(
                    sender=dispenser_account.addr,
                    receiver=account_to_fund_addr,
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
            .send(send_params)
        )

        base_result = SendSingleTransactionResult.from_composer_result(result)
        return EnsureFundedResult(
            **vars(base_result),
            transaction_id=base_result.tx_id or result.tx_ids[0],
            amount_funded=amount_funded,
        )

    def ensure_funded_from_testnet_dispenser_api(
        self,
        account_to_fund: str | AddressWithTransactionSigner,
        dispenser_client: TestNetDispenserApiClient,
        min_spending_balance: AlgoAmount,
        *,
        min_funding_increment: AlgoAmount | None = None,
    ) -> EnsureFundedFromTestnetDispenserApiResult | None:
        """
        Ensure an account is funded using the TestNet Dispenser API.

        Uses the TestNet Dispenser API as a funding source such that the account has a certain amount
        of Algo free to spend (accounting for Algo locked in minimum balance requirement).

        See `<https://dev.algorand.co/concepts/smart-contracts/costs-constraints#mbr>`_ for details.

        :param account_to_fund: The account to fund
        :param dispenser_client: The TestNet dispenser funding client
        :param min_spending_balance: The minimum balance of Algo that the account should have
            available to spend
        :param min_funding_increment: Optional minimum funding increment
        :returns: The result of executing the dispensing transaction and the `amountFunded` if funds were needed, or
            None if no funds were needed
        :raises ValueError: If attempting to fund on non-TestNet network

        :example:
            >>> # Basic example:
            >>> account_manager.ensure_funded_from_testnet_dispenser_api(
            ...     "ACCOUNTADDRESS",
            ...     algorand.client.get_testnet_dispenser_from_environment(),
            ...     AlgoAmount.from_algo(1)
            ... )
            >>> # With configuration:
            >>> account_manager.ensure_funded_from_testnet_dispenser_api(
            ...     "ACCOUNTADDRESS",
            ...     algorand.client.get_testnet_dispenser_from_environment(),
            ...     AlgoAmount.from_algo(1),
            ...     min_funding_increment=AlgoAmount.from_algo(2)
            ... )
        """
        account_to_fund_addr = self._get_address(account_to_fund)

        if not self._client_manager.is_testnet():
            raise ValueError("Attempt to fund using TestNet dispenser API on non TestNet network.")

        amount_funded = self._get_ensure_funded_amount(
            account_to_fund_addr, min_spending_balance, min_funding_increment
        )

        if not amount_funded:
            return None

        result = dispenser_client.fund(address=account_to_fund_addr, amount=amount_funded.micro_algo)

        return EnsureFundedFromTestnetDispenserApiResult(
            transaction_id=result.tx_id,
            amount_funded=AlgoAmount.from_micro_algo(result.amount),
        )

    def _get_address(self, sender: str | AddressWithTransactionSigner | AddressWithSigners) -> str:
        # Check isinstance first for proper type narrowing
        if isinstance(sender, str):
            return sender
        # Both AddressWithSigners and AddressWithTransactionSigner now use 'addr'
        return sender.addr

    def _get_composer(
        self, get_suggested_params: Callable[[], algod_models.SuggestedParams] | None = None
    ) -> TransactionComposer:
        get_suggested_params = get_suggested_params or self._client_manager.algod.suggested_params

        return TransactionComposer(
            TransactionComposerParams(
                algod=self._client_manager.algod,
                get_signer=self.get_signer,
                get_suggested_params=get_suggested_params,
            )
        )

    def _calculate_fund_amount(
        self,
        min_spending_balance: int,
        current_spending_balance: AlgoAmount,
        min_funding_increment: int,
    ) -> int | None:
        if min_spending_balance > current_spending_balance:
            min_fund_amount = (min_spending_balance - current_spending_balance).micro_algo
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


# For LogicSigAccount and MultisigAccount, create an AddressWithSigners wrapper
# These accounts have a .signer property but may not have all the other signers
# We create placeholder signers for the other capabilities
def _placeholder_bytes_signer(_: bytes) -> Never:
    raise NotImplementedError("bytes_signer not available for this account type")


def _placeholder_lsig_signer(_: LogicSigAccount, __: MultisigAccount | None = None) -> Never:
    raise NotImplementedError("delegated_lsig_signer not available for this account type")


def _placeholder_program_data_signer(_: LogicSig, __: bytes) -> Never:
    raise NotImplementedError("program_data_signer not available for this account type")


def _placeholder_mx_bytes_signer(_: bytes) -> Never:
    raise NotImplementedError("mx_bytes_signer not available for this account type")
