import base64
import dataclasses
from typing import Any, cast

import algokit_algosdk as algosdk
from algokit_algosdk import encoding
from algokit_algosdk.logicsig import LogicSigAccount as AlgoKitLogicSigAccount
from algokit_algosdk.multisig import Multisig as AlgoKitMultisig
from algokit_algosdk.signer import (
    make_basic_account_transaction_signer,
    make_logic_sig_transaction_signer,
    make_multisig_transaction_signer,
)
from algokit_algosdk.transaction import Multisig as TxMultisig
from algokit_algosdk.transaction import MultisigTransaction
from algokit_transact.models.transaction import Transaction as AlgokitTransaction
from algokit_utils.protocols.signer import TransactionSigner

AlgosdkLogicSigAccount = AlgoKitLogicSigAccount
Multisig = AlgoKitMultisig

__all__ = [
    "DISPENSER_ACCOUNT_NAME",
    "LogicSigAccount",
    "MultiSigAccount",
    "MultisigMetadata",
    "SigningAccount",
    "TransactionSignerAccount",
]


DISPENSER_ACCOUNT_NAME = "DISPENSER"


@dataclasses.dataclass(kw_only=True)
class TransactionSignerAccount:
    """A basic transaction signer account."""

    address: str
    signer: TransactionSigner

    def __post_init__(self) -> None:
        if not isinstance(self.address, str):
            raise TypeError("Address must be a string")


@dataclasses.dataclass(kw_only=True)
class SigningAccount:
    """Holds the private key and address for an account.

    Provides access to the account's private key, address, public key and transaction signer.
    """

    private_key: str
    """Base64 encoded private key"""
    address: str = dataclasses.field(default="")
    """Address for this account"""
    _signer: TransactionSigner | None = dataclasses.field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.address:
            self.address = _address_from_private_key(self.private_key)

    @property
    def public_key(self) -> bytes:
        """The public key for this account.

        :return: The public key as bytes
        """
        public_key = encoding.decode_address(self.address)
        assert isinstance(public_key, bytes)
        return public_key

    @property
    def signer(self) -> TransactionSigner:
        """Get the AlgoKit-native transaction signer callable."""
        if not self._signer:
            self._signer = cast(TransactionSigner, make_basic_account_transaction_signer(self.private_key))
        return self._signer


@dataclasses.dataclass(kw_only=True)
class MultisigMetadata:
    """Metadata for a multisig account.

    Contains the version, threshold and addresses for a multisig account.
    """

    version: int
    threshold: int
    addresses: list[str]


@dataclasses.dataclass(kw_only=True)
class MultiSigAccount:
    """Account wrapper that supports partial or full multisig signing.

    Provides functionality to manage and sign transactions for a multisig account.

    :param multisig_params: The parameters for the multisig account
    :param signing_accounts: The list of accounts that can sign
    """

    _params: MultisigMetadata
    _signing_accounts: list[SigningAccount]
    _addr: str
    _signer: TransactionSigner
    _multisig: TxMultisig
    _algokit_multisig: AlgoKitMultisig

    def __init__(self, multisig_params: MultisigMetadata, signing_accounts: list[SigningAccount]) -> None:
        self._params = multisig_params
        self._signing_accounts = signing_accounts
        self._multisig = TxMultisig(  # type: ignore[no-untyped-call]
            multisig_params.version, multisig_params.threshold, multisig_params.addresses
        )
        self._algokit_multisig = AlgoKitMultisig(
            multisig_params.version, multisig_params.threshold, multisig_params.addresses
        )
        self._addr = str(self._multisig.address())  # type: ignore[no-untyped-call]
        self._signer = cast(
            TransactionSigner,
            make_multisig_transaction_signer(
                self._algokit_multisig,
                [account.private_key for account in signing_accounts],
            ),
        )

    @property
    def multisig(self) -> TxMultisig:
        """Get the underlying `algosdk.transaction.Multisig` object instance.

        :return: The `algosdk.transaction.Multisig` object instance
        """
        return self._multisig

    @property
    def params(self) -> MultisigMetadata:
        """Get the parameters for the multisig account.

        :return: The multisig account parameters
        """
        return self._params

    @property
    def signing_accounts(self) -> list[SigningAccount]:
        """Get the list of accounts that are present to sign.

        :return: The list of signing accounts
        """
        return self._signing_accounts

    @property
    def address(self) -> str:
        """Get the address of the multisig account.

        :return: The multisig account address
        """
        return self._addr

    @property
    def signer(self) -> TransactionSigner:
        """Get the AlgoKit-native signer callable for this multisig account."""
        return self._signer

    def sign(self, transaction: AlgokitTransaction) -> MultisigTransaction:
        """Sign the given transaction with all present signers.

        :param transaction: Either a transaction object or a raw, partially signed transaction
        :return: The transaction signed by the present signers
        """
        msig_txn = MultisigTransaction(cast(Any, transaction), self._multisig)
        for signer in self._signing_accounts:
            msig_txn.sign(signer.private_key)  # type: ignore[no-untyped-call]

        return msig_txn


@dataclasses.dataclass(kw_only=True)
class LogicSigAccount:
    """Account wrapper that supports logic sig signing.

    Provides functionality to manage and sign transactions for a logic sig account.
    """

    _signer: TransactionSigner
    _algokit_lsig: AlgoKitLogicSigAccount

    def __init__(self, program: bytes, args: list[bytes] | None) -> None:
        self._algokit_lsig = AlgoKitLogicSigAccount(program, args)
        self._signer = cast(TransactionSigner, make_logic_sig_transaction_signer(self._algokit_lsig))

    @property
    def lsig(self) -> AlgosdkLogicSigAccount:
        """Get the underlying `algosdk.transaction.LogicSigAccount` object instance.

        :return: The `algosdk.transaction.LogicSigAccount` object instance
        """
        return cast(AlgosdkLogicSigAccount, cast(Any, self._signer).lsig)

    @property
    def address(self) -> str:
        """Get the address of the logic sig account.

        If the LogicSig is delegated to another account, this will return the address of that account.

        If the LogicSig is not delegated to another account, this will return an escrow address that is the hash of
        the LogicSig's program code.

        :return: The logic sig account address
        """
        lsig_data = cast(Any, self._algokit_lsig)
        legacy_account = AlgosdkLogicSigAccount(lsig_data.program, lsig_data.args)
        return legacy_account.address()

    @property
    def signer(self) -> TransactionSigner:
        """Get the AlgoKit-native signer callable for this logic sig account."""
        return self._signer

    @property
    def algokit_lsig(self) -> AlgoKitLogicSigAccount:
        """Expose the AlgoKit-native representation."""
        return self._algokit_lsig


def _address_from_private_key(private_key: str) -> str:
    decoded = base64.b64decode(private_key)
    public_key = decoded[algosdk.constants.key_len_bytes :]
    encoded = encoding.encode_address(public_key)
    assert isinstance(encoded, str)
    return encoded
