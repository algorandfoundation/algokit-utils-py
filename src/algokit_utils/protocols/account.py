from typing import Protocol, runtime_checkable

from algokit_utils.protocols.signer import (
    BytesSigner,
    LsigSigner,
    MxBytesSigner,
    ProgramDataSigner,
    TransactionSigner,
)

__all__ = ["SignerAccountProtocol", "TransactionSignerAccountProtocol"]


@runtime_checkable
class TransactionSignerAccountProtocol(Protocol):
    """An account that has a transaction signer.
    Implemented by SigningAccount, LogicSigAccount, MultisigAccount and TransactionSignerAccount abstractions.
    """

    @property
    def address(self) -> str:
        """The address of the account."""
        ...

    @property
    def signer(self) -> TransactionSigner:
        """The AlgoKit-native signer callable."""
        ...


@runtime_checkable
class SignerAccountProtocol(Protocol):
    """Account providing multiple signer interfaces for secretless signing."""

    @property
    def address(self) -> str: ...

    @property
    def public_key(self) -> bytes: ...

    @property
    def signer(self) -> TransactionSigner: ...

    @property
    def lsig_signer(self) -> LsigSigner: ...

    @property
    def program_data_signer(self) -> ProgramDataSigner: ...

    @property
    def bytes_signer(self) -> BytesSigner: ...

    @property
    def mx_bytes_signer(self) -> MxBytesSigner: ...
