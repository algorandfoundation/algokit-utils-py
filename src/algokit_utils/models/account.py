import dataclasses

import algosdk
import algosdk.atomic_transaction_composer
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner
from algosdk.transaction import Multisig, MultisigTransaction

DISPENSER_ACCOUNT_NAME = "DISPENSER"


__all__ = [
    "Account",
    "MultiSigAccount",
    "MultisigMetadata",
]


@dataclasses.dataclass(kw_only=True)
class Account:
    """Holds the private_key and address for an account"""

    private_key: str
    """Base64 encoded private key"""
    address: str = dataclasses.field(default="")
    """Address for this account"""

    def __post_init__(self) -> None:
        if not self.address:
            self.address = str(algosdk.account.address_from_private_key(self.private_key))

    @property
    def public_key(self) -> bytes:
        """The public key for this account"""
        public_key = algosdk.encoding.decode_address(self.address)
        assert isinstance(public_key, bytes)
        return public_key

    @property
    def signer(self) -> AccountTransactionSigner:
        """An AccountTransactionSigner for this account"""
        return AccountTransactionSigner(self.private_key)

    @staticmethod
    def new_account() -> "Account":
        private_key, address = algosdk.account.generate_account()
        return Account(private_key=private_key)


@dataclasses.dataclass(kw_only=True)
class MultisigMetadata:
    version: int
    threshold: int
    addresses: list[str]


@dataclasses.dataclass(kw_only=True)
class MultiSigAccount:
    """Account wrapper that supports partial or full multisig signing."""

    _params: MultisigMetadata
    _signing_accounts: list[Account]
    _addr: str
    _signer: TransactionSigner
    _multisig: Multisig

    def __init__(self, multisig_params: MultisigMetadata, signing_accounts: list[Account]) -> None:
        """Initialize a new multisig account.

        Args:
            multisig_params: The parameters for the multisig account
            signing_accounts: The list of accounts that can sign
        """
        self._params = multisig_params
        self._signing_accounts = signing_accounts
        self._multisig = Multisig(multisig_params.version, multisig_params.threshold, multisig_params.addresses)
        self._addr = str(self._multisig.address())
        self._signer = algosdk.atomic_transaction_composer.MultisigTransactionSigner(
            self._multisig,
            [account.private_key for account in signing_accounts],
        )

    @property
    def params(self) -> MultisigMetadata:
        """The parameters for the multisig account."""
        return self._params

    @property
    def signing_accounts(self) -> list[Account]:
        """The list of accounts that are present to sign."""
        return self._signing_accounts

    @property
    def address(self) -> str:
        """The address of the multisig account."""
        return self._addr

    @property
    def signer(self) -> TransactionSigner:
        """The transaction signer for this multisig account."""
        return self._signer

    def sign(self, transaction: algosdk.transaction.Transaction) -> MultisigTransaction:
        """Sign the given transaction.

        Args:
            transaction: Either a transaction object or a raw, partially signed transaction

        Returns:
            The transaction signed by the present signers
        """
        msig_txn = MultisigTransaction(
            transaction,
            self._multisig,
        )
        for signer in self._signing_accounts:
            msig_txn.sign(signer.private_key)

        return msig_txn
