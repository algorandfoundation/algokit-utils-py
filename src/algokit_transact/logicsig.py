import dataclasses
from collections.abc import Sequence
from typing import Protocol

from typing_extensions import Self

from algokit_common import address_from_public_key, public_key_from_address, sha512_256
from algokit_common.constants import (
    LOGIC_DATA_DOMAIN_SEPARATOR,
    MULTISIG_PROGRAM_DOMAIN_SEPARATOR,
    PROGRAM_DOMAIN_SEPARATOR,
)
from algokit_transact.codec.signed import encode_signed_transaction
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction as AlgokitTransaction
from algokit_transact.signer import (
    AddressWithSigners,
    DelegatedLsigSigner,
    ProgramDataSigner,
    TransactionSigner,
)
from algokit_transact.signing.logic_signature import LogicSigSignature
from algokit_transact.signing.multisig import (
    address_from_multisig_signature,
    apply_multisig_subsignature,
    new_multisig_signature,
)
from algokit_transact.signing.types import MultisigSignature
from algokit_transact.signing.validation import sanity_check_program

__all__ = [
    "LogicSigAccount",
]


class _MultisigMetadataProtocol(Protocol):
    version: int
    threshold: int
    addrs: list[str]


class _MultisigAccountProtocol(Protocol):
    @property
    def address(self) -> str: ...


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
        sanity_check_program(program)
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

        program_hash = sha512_256(PROGRAM_DOMAIN_SEPARATOR + self._program)
        return address_from_public_key(program_hash)

    @property
    def addr(self) -> str:
        """Alias for address property (matching TypeScript's get addr())."""
        return self.address

    @property
    def signer(self) -> TransactionSigner:
        """Transaction signer callable."""
        if self._signer is None:
            self._signer = self._create_logic_sig_signer()
        return self._signer

    def _create_logic_sig_signer(self) -> TransactionSigner:
        program = self._program
        args = list(self._args) if self._args else None
        signature = self._signature
        multisig_sig = self._multisig_signature
        lsig_address = self.address

        def signer(txn_group: Sequence[AlgokitTransaction], indexes_to_sign: Sequence[int]) -> list[bytes]:
            blobs: list[bytes] = []
            for index in indexes_to_sign:
                txn = txn_group[index]
                logic_sig = LogicSigSignature(
                    logic=program,
                    args=args,
                    sig=signature,
                    msig=multisig_sig,
                )
                auth_addr = lsig_address if txn.sender != lsig_address else None

                signed = SignedTransaction(
                    txn=txn,
                    sig=None,
                    msig=None,
                    lsig=logic_sig,
                    auth_address=auth_addr,
                )
                blobs.append(encode_signed_transaction(signed))
            return blobs

        return signer

    def bytes_to_sign_for_delegation(self, msig: _MultisigAccountProtocol | None = None) -> bytes:
        """Returns bytes to sign for delegation.

        Args:
            msig: Optional multisig account for multisig delegation.

        Returns:
            The bytes that need to be signed for delegation.
        """

        if msig is not None:
            msig_public_key = public_key_from_address(msig.address)
            return MULTISIG_PROGRAM_DOMAIN_SEPARATOR + msig_public_key + self._program
        return PROGRAM_DOMAIN_SEPARATOR + self._program

    def program_data_to_sign(self, data: bytes) -> bytes:
        """Returns bytes to sign for program data.

        Args:
            data: The data to sign.

        Returns:
            The bytes that need to be signed (ProgData + program_address + data).
        """

        program_address = public_key_from_address(self.address)
        return LOGIC_DATA_DOMAIN_SEPARATOR + program_address + data

    def sign_program_data(self, data: bytes, signer: ProgramDataSigner) -> bytes:
        """Signs program data with given signer.

        Args:
            data: The data to sign.
            signer: The program data signer to use.

        Returns:
            The signature bytes.
        """
        program_address = public_key_from_address(self.address)
        return signer(data, program_address)

    def delegate(self, signer: DelegatedLsigSigner, delegating_address: str | None = None) -> Self:
        """Delegate this LogicSig to a single account. Returns self for chaining.

        Args:
            signer: The DelegatedLsigSigner callback to sign the program.
            delegating_address: Optional address of the delegating account.
                If not provided, the address must be set separately or
                the LogicSig will use the escrow address.

        Returns:
            Self for method chaining.
        """
        self._signature = signer(self._program, None)
        self._delegated_address = delegating_address
        self._multisig_signature = None
        self._signer = None
        return self

    def delegate_multisig(
        self,
        multisig_params: _MultisigMetadataProtocol,
        signing_accounts: Sequence[AddressWithSigners],
    ) -> Self:
        """Delegate this LogicSig to a multisig account. Returns self for chaining."""
        msig = new_multisig_signature(
            multisig_params.version,
            multisig_params.threshold,
            multisig_params.addrs,
        )

        msig_address = address_from_multisig_signature(msig)
        msig_public_key = public_key_from_address(msig_address)

        address_to_signer = {account.addr: account.delegated_lsig_signer for account in signing_accounts}

        for subsig in msig.subsigs:
            subsig_addr = address_from_public_key(subsig.public_key)
            if subsig_addr in address_to_signer:
                signature = address_to_signer[subsig_addr](self._program, msig_public_key)
                msig = apply_multisig_subsignature(msig, subsig_addr, signature)

        self._multisig_signature = msig
        self._delegated_address = address_from_multisig_signature(msig)
        self._signature = None
        self._signer = None
        return self
