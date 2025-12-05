import base64
import dataclasses
from collections.abc import Sequence
from typing import cast

from typing_extensions import deprecated

import algokit_algosdk as algosdk
from algokit_transact import encode_signed_transaction, encode_transaction
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction as AlgokitTransaction
from algokit_transact.signer import make_basic_account_transaction_signer
from algokit_transact.signing.multisig import (
    address_from_multisig_signature,
    apply_multisig_subsignature,
    new_multisig_signature,
)
from algokit_transact.signing.types import MultisigSignature
from algokit_utils.protocols.account import SignerAccountProtocol
from algokit_utils.protocols.signer import (
    BytesSigner,
    LsigSigner,
    MxBytesSigner,
    ProgramDataSigner,
    TransactionSigner,
)

__all__ = [
    "DISPENSER_ACCOUNT_NAME",
    "LogicSigAccount",
    "MultiSigAccount",
    "MultisigMetadata",
    "SigningAccount",
    "TransactionSignerAccount",
]


DISPENSER_ACCOUNT_NAME = "DISPENSER"


@deprecated("TransactionSignerAccount is deprecated; use TransactionSignerAccountProtocol instead.")
@dataclasses.dataclass(kw_only=True)
class TransactionSignerAccount:
    """A basic transaction signer account.

    .. deprecated::
        Use :class:`~algokit_utils.protocols.account.TransactionSignerAccountProtocol` instead.
    """

    address: str
    signer: TransactionSigner

    def __post_init__(self) -> None:
        if not isinstance(self.address, str):
            raise TypeError("Address must be a string")


@dataclasses.dataclass(kw_only=True)
class SigningAccount:
    """Account with private key. Implements SignerAccountProtocol."""

    private_key: str
    """Base64 encoded private key"""
    address: str = dataclasses.field(default="")
    """Address for this account"""
    _signer: TransactionSigner | None = dataclasses.field(default=None, init=False, repr=False)
    _bytes_signer: BytesSigner | None = dataclasses.field(default=None, init=False, repr=False)
    _lsig_signer: LsigSigner | None = dataclasses.field(default=None, init=False, repr=False)
    _program_data_signer: ProgramDataSigner | None = dataclasses.field(default=None, init=False, repr=False)
    _mx_bytes_signer: MxBytesSigner | None = dataclasses.field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.address:
            self.address = _address_from_private_key(self.private_key)

    @property
    def public_key(self) -> bytes:
        """The public key for this account."""
        public_key = algosdk.encoding.decode_address(self.address)
        assert isinstance(public_key, bytes)
        return public_key

    @property
    def signer(self) -> TransactionSigner:
        """Transaction signer callable."""
        if not self._signer:
            self._signer = cast(
                TransactionSigner,
                make_basic_account_transaction_signer(self.private_key),
            )
        return self._signer

    @property
    def bytes_signer(self) -> BytesSigner:
        """Raw bytes signer."""
        if not self._bytes_signer:
            from nacl.signing import SigningKey

            key_bytes = base64.b64decode(self.private_key)
            signing_key = SigningKey(key_bytes[:32])

            def _sign_bytes(data: bytes) -> bytes:
                return signing_key.sign(data).signature

            self._bytes_signer = _sign_bytes
        return self._bytes_signer

    @property
    def lsig_signer(self) -> LsigSigner:
        """LogicSig program signer."""
        if not self._lsig_signer:
            from algokit_common.constants import MULTISIG_PROGRAM_DOMAIN_SEPARATOR, PROGRAM_DOMAIN_SEPARATOR

            bytes_signer = self.bytes_signer

            def _sign_lsig(program: bytes, msig_address: bytes | None = None) -> bytes:
                if msig_address:
                    return bytes_signer(MULTISIG_PROGRAM_DOMAIN_SEPARATOR.encode() + msig_address + program)
                return bytes_signer(PROGRAM_DOMAIN_SEPARATOR.encode() + program)

            self._lsig_signer = _sign_lsig
        return self._lsig_signer

    @property
    def program_data_signer(self) -> ProgramDataSigner:
        """Program data signer (ProgData prefix)."""
        if not self._program_data_signer:
            from algokit_common.constants import LOGIC_DATA_DOMAIN_SEPARATOR

            bytes_signer = self.bytes_signer

            def _sign_program_data(data: bytes) -> bytes:
                return bytes_signer(LOGIC_DATA_DOMAIN_SEPARATOR.encode() + data)

            self._program_data_signer = _sign_program_data
        return self._program_data_signer

    @property
    def mx_bytes_signer(self) -> MxBytesSigner:
        """MX-prefixed bytes signer."""
        if not self._mx_bytes_signer:
            from algokit_common.constants import MX_BYTES_DOMAIN_SEPARATOR

            bytes_signer = self.bytes_signer

            def _sign_mx_bytes(data: bytes) -> bytes:
                return bytes_signer(MX_BYTES_DOMAIN_SEPARATOR.encode() + data)

            self._mx_bytes_signer = _sign_mx_bytes
        return self._mx_bytes_signer


@dataclasses.dataclass(kw_only=True)
class MultisigMetadata:
    """Metadata for a multisig account."""

    version: int
    threshold: int
    addresses: list[str]


@dataclasses.dataclass(kw_only=True)
class MultiSigAccount:
    """Account wrapper for multisig signing. Supports secretless signing."""

    _params: MultisigMetadata
    _signing_accounts: Sequence[SignerAccountProtocol]
    _addr: str
    _signer: TransactionSigner
    _multisig_signature: MultisigSignature

    def __init__(
        self,
        multisig_params: MultisigMetadata,
        signing_accounts: Sequence[SignerAccountProtocol],
    ) -> None:
        self._params = multisig_params
        self._signing_accounts = signing_accounts
        self._multisig_signature = new_multisig_signature(
            multisig_params.version,
            multisig_params.threshold,
            multisig_params.addresses,
        )
        self._addr = address_from_multisig_signature(self._multisig_signature)
        self._signer = self._create_multisig_signer()

    def _create_multisig_signer(self) -> TransactionSigner:
        address_to_signer: dict[str, BytesSigner] = {
            account.address: account.bytes_signer for account in self._signing_accounts
        }
        msig_address = self._addr
        base_multisig = self._multisig_signature

        def signer(txn_group: Sequence[AlgokitTransaction], indexes_to_sign: Sequence[int]) -> list[bytes]:
            blobs: list[bytes] = []
            for index in indexes_to_sign:
                txn = txn_group[index]
                payload = encode_transaction(txn)

                multisig_sig = base_multisig
                for subsig in base_multisig.subsignatures:
                    if subsig.address in address_to_signer:
                        signature = address_to_signer[subsig.address](payload)
                        multisig_sig = apply_multisig_subsignature(multisig_sig, subsig.address, signature)

                signed = SignedTransaction(
                    transaction=txn,
                    signature=None,
                    multi_signature=multisig_sig,
                    logic_signature=None,
                    auth_address=msig_address if txn.sender != msig_address else None,
                )
                blobs.append(encode_signed_transaction(signed))
            return blobs

        return signer

    @property
    def params(self) -> MultisigMetadata:
        """The multisig account parameters."""
        return self._params

    @property
    def signing_accounts(self) -> Sequence[SignerAccountProtocol]:
        """The list of signing accounts."""
        return self._signing_accounts

    @property
    def address(self) -> str:
        """The multisig account address."""
        return self._addr

    @property
    def signer(self) -> TransactionSigner:
        """Transaction signer callable."""
        return self._signer


@dataclasses.dataclass(kw_only=True)
class LogicSigAccount:
    """Account wrapper for LogicSig signing. Supports delegation including secretless signing."""

    _program: bytes
    _args: list[bytes] | None
    _signature: bytes | None
    _multisig_signature: MultisigSignature | None
    _delegated_address: str | None
    _signer: TransactionSigner | None

    def __init__(self, program: bytes, args: list[bytes] | None = None) -> None:
        self._program = program
        self._args = args
        self._signature = None
        self._multisig_signature = None
        self._delegated_address = None
        self._signer = None

    @property
    def program(self) -> bytes:
        """The LogicSig program bytes."""
        return self._program

    @property
    def args(self) -> list[bytes] | None:
        """The arguments to pass to the LogicSig program."""
        return self._args

    @property
    def is_delegated(self) -> bool:
        """Whether this LogicSig is delegated to an account."""
        return self._signature is not None or self._multisig_signature is not None

    @property
    def address(self) -> str:
        """The LogicSig account address (delegated address or escrow address)."""
        if self._delegated_address is not None:
            return self._delegated_address

        from algokit_common import sha512_256
        from algokit_common.constants import PROGRAM_DOMAIN_SEPARATOR

        program_hash = sha512_256(PROGRAM_DOMAIN_SEPARATOR.encode() + self._program)
        address = algosdk.encoding.encode_address(program_hash)
        assert isinstance(address, str)
        return address

    @property
    def signer(self) -> TransactionSigner:
        """Transaction signer callable."""
        if self._signer is None:
            self._signer = self._create_logic_sig_signer()
        return self._signer

    def _create_logic_sig_signer(self) -> TransactionSigner:
        from algokit_transact.signing.logic_signature import LogicSignature

        program = self._program
        args = list(self._args) if self._args else None
        signature = self._signature
        multisig_sig = self._multisig_signature
        lsig_address = self.address

        def signer(txn_group: Sequence[AlgokitTransaction], indexes_to_sign: Sequence[int]) -> list[bytes]:
            blobs: list[bytes] = []
            for index in indexes_to_sign:
                txn = txn_group[index]
                logic_sig = LogicSignature(
                    logic=program,
                    args=args,
                    signature=signature,
                    multi_signature=multisig_sig,
                )
                auth_addr = lsig_address if txn.sender != lsig_address else None

                signed = SignedTransaction(
                    transaction=txn,
                    signature=None,
                    multi_signature=None,
                    logic_signature=logic_sig,
                    auth_address=auth_addr,
                )
                blobs.append(encode_signed_transaction(signed))
            return blobs

        return signer

    def delegate(self, account: SignerAccountProtocol) -> "LogicSigAccount":
        """Delegate this LogicSig to a single account. Returns self for chaining."""
        self._signature = account.lsig_signer(self._program)
        self._delegated_address = account.address
        self._multisig_signature = None
        self._signer = None
        return self

    def delegate_multisig(
        self,
        multisig_params: MultisigMetadata,
        signing_accounts: Sequence[SignerAccountProtocol],
    ) -> "LogicSigAccount":
        """Delegate this LogicSig to a multisig account. Returns self for chaining."""
        msig = new_multisig_signature(
            multisig_params.version,
            multisig_params.threshold,
            multisig_params.addresses,
        )

        msig_address = address_from_multisig_signature(msig)
        msig_public_key = algosdk.encoding.decode_address(msig_address)
        assert isinstance(msig_public_key, bytes)

        address_to_signer: dict[str, LsigSigner] = {
            account.address: account.lsig_signer for account in signing_accounts
        }

        for subsig in msig.subsignatures:
            if subsig.address in address_to_signer:
                signature = address_to_signer[subsig.address](self._program, msig_public_key)
                msig = apply_multisig_subsignature(msig, subsig.address, signature)

        self._multisig_signature = msig
        self._delegated_address = address_from_multisig_signature(msig)
        self._signature = None
        self._signer = None
        return self


def _address_from_private_key(private_key: str) -> str:
    decoded = base64.b64decode(private_key)
    public_key = decoded[algosdk.constants.key_len_bytes :]
    encoded = algosdk.encoding.encode_address(public_key)
    assert isinstance(encoded, str)
    return encoded
