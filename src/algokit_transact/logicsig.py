import dataclasses
from collections.abc import Sequence
from functools import cached_property
from typing import TYPE_CHECKING

from algokit_common import address_from_public_key, public_key_from_address, sha512_256
from algokit_transact import decode_logic_signature
from algokit_transact.codec.signed import encode_signed_transaction
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction
from algokit_transact.ops.validate import validate_signed_transaction
from algokit_transact.signing.logic_signature import LogicSigSignature
from algokit_transact.signing.types import MultisigSignature
from algokit_transact.signing.validation import sanity_check_program

if TYPE_CHECKING:
    from algokit_transact.signer import (
        AddressWithDelegatedLsigSigner,
        ProgramDataSigner,
        TransactionSigner,
    )

_MULTISIG_DOMAIN_SEPARATOR = b"MultisigAddr"
_PROG_DATA_TAG = b"ProgData"
_PROGRAM_TAG = b"Program"
_MX_TAG = b"MX"
_MSIG_PROGRAM_TAG = b"MsigProgram"


@dataclasses.dataclass(frozen=True)
class DelegatedLsigResult:
    addr: str
    sig: bytes | None = None
    lmsig: MultisigSignature | None = None

    def __post_init__(self) -> None:
        # invalid to have neither or both defined
        if bool(self.sig) == bool(self.lmsig):
            raise ValueError("Must provide either a signature or a multi signature")


@dataclasses.dataclass(kw_only=True)
class LogicSig:
    logic: bytes
    """The LogicSig program bytes."""
    args: Sequence[bytes] = dataclasses.field(default=())
    """The arguments to pass to the LogicSig program."""
    _address: str | None = None

    def __post_init__(self) -> None:
        sanity_check_program(self.logic)

    @staticmethod
    def from_signature(signature: LogicSigSignature) -> "LogicSig":
        return LogicSig(logic=signature.logic, args=signature.args or ())

    @staticmethod
    def from_bytes(encoded_lsig: bytes) -> "LogicSig":
        signature = decode_logic_signature(encoded_lsig)
        return LogicSig.from_signature(signature)

    @cached_property
    def address(self) -> str:
        """The LogicSig account address (delegated address or escrow address)."""
        return self._address or address_from_public_key(sha512_256(_PROGRAM_TAG + self.logic))

    @property
    def addr(self) -> str:
        """Alias for address property (matching TypeScript's get addr())."""
        return self.address

    def bytes_to_sign_for_delegation(self, msig_address: str | None = None) -> bytes:
        if msig_address:
            return _MSIG_PROGRAM_TAG + public_key_from_address(msig_address) + self.logic
        else:
            return _PROGRAM_TAG + self.logic

    def sign_program_data(self, data: bytes, signer: "ProgramDataSigner") -> bytes:
        return signer(self, data)

    def program_data_to_sign(self, data: bytes) -> bytes:
        return _PROG_DATA_TAG + public_key_from_address(self.address) + data

    def account(self) -> "LogicSigAccount":
        return LogicSigAccount(logic=self.logic, args=self.args)

    def delegated_account(self, delegator: str) -> "LogicSigAccount":
        return LogicSigAccount(logic=self.logic, args=self.args, _address=delegator)


@dataclasses.dataclass(kw_only=True)
class LogicSigAccount(LogicSig):
    """Account wrapper for LogicSig signing. Supports delegation including secretless signing."""

    sig: bytes | None = None
    msig: MultisigSignature | None = None
    lmsig: MultisigSignature | None = None

    @staticmethod
    def from_signature(signature: LogicSigSignature, delgator: str | None = None) -> "LogicSigAccount":
        from algokit_transact.multisig import MultisigAccount

        if msig := (signature.lmsig or signature.msig):
            msig_addr = MultisigAccount.from_signature(msig).addr
            if delgator and delgator != msig_addr:
                raise ValueError("Provided delegator address does not match multisig address")

            return LogicSigAccount(
                logic=signature.logic,
                args=signature.args or (),
                _address=msig_addr,
                lmsig=signature.lmsig,
                msig=signature.msig,
            )

        if (signature.sig or delgator) is None:
            raise ValueError("Delegated address must be provided when logic sig has a signature")

        return LogicSigAccount(logic=signature.logic, args=signature.args or (), _address=delgator, sig=signature.sig)

    @staticmethod
    def from_bytes(encoded_lsig: bytes, delegator: str | None = None) -> "LogicSigAccount":
        decoded = decode_logic_signature(encoded_lsig)
        return LogicSigAccount.from_signature(decoded, delegator)

    @property
    def is_delegated(self) -> bool:
        """Whether this LogicSig is delegated to an account."""
        return self.sig is not None or self.lmsig is not None

    @property
    def signer(self) -> "TransactionSigner":
        """Transaction signer callable."""
        program = self.logic
        args = list(self.args) or None
        signature = self.sig
        multisig_sig = self.lmsig
        lsig_address = self.address

        def signer(txn_group: Sequence[Transaction], indexes_to_sign: Sequence[int]) -> list[bytes]:
            blobs: list[bytes] = []
            for index in indexes_to_sign:
                txn = txn_group[index]
                logic_sig = LogicSigSignature(
                    logic=program,
                    args=args,
                    sig=signature,
                    lmsig=multisig_sig,
                )
                auth_addr = lsig_address if txn.sender != lsig_address else None

                signed = SignedTransaction(
                    txn=txn,
                    sig=None,
                    msig=None,
                    lsig=logic_sig,
                    auth_address=auth_addr,
                )
                validate_signed_transaction(signed)
                blobs.append(encode_signed_transaction(signed))
            return blobs

        return signer

    def sign_for_delegation(self, signer: "AddressWithDelegatedLsigSigner") -> None:
        result = signer.delegated_lsig_signer(self, None)

        if result.addr != self.address:
            raise ValueError(
                f"Delegator address from signer does not match expected delegator address."
                f" Expected: {self.addr}, got: {result.addr}",
            )

        if result.sig:
            self.sig = result.sig
        elif result.lmsig:
            self.lmsig = result.lmsig
        else:
            raise ValueError("Delegated lsig signer must return either a sig or lmsig")
