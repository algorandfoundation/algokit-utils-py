from typing import Protocol, runtime_checkable

from algokit_utils.protocols.signer import (
    BytesSigner,
    LsigSigner,
    ProgramDataSigner,
    TransactionSigner,
)

__all__ = ["SignerAccountProtocol", "TransactionSignerAccountProtocol"]


@runtime_checkable
class TransactionSignerAccountProtocol(Protocol):
    """An account that has a transaction signer.
    Implemented by SigningAccount, LogicSigAccount, MultiSigAccount and TransactionSignerAccount abstractions.
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
    """
    Protocol for an account that provides multiple signer interfaces.

    This protocol extends the basic TransactionSignerAccountProtocol with
    additional signing capabilities for LogicSig delegation and raw bytes signing.
    It enables secretless signing through KMS, hardware wallets, or other
    external signing mechanisms.

    Implementations of this protocol can be used:
    - As sub-signers in MultisigAccount
    - To delegate LogicSig accounts
    - For any operation requiring account-based signing

    See Also:
        - make_signer_account: Factory function to create SignerAccountProtocol from a BytesSigner
        - SigningAccount: Standard implementation using private keys
    """

    @property
    def address(self) -> str:
        """The address of the account."""
        ...

    @property
    def public_key(self) -> bytes:
        """The public key for this account (32 bytes)."""
        ...

    @property
    def signer(self) -> TransactionSigner:
        """The AlgoKit-native transaction signer callable."""
        ...

    @property
    def lsig_signer(self) -> LsigSigner:
        """
        Signer for LogicSig programs.

        Signs the program prefixed with "Program" domain separator.
        Used for single-sig LogicSig delegation.
        """
        ...

    @property
    def program_data_signer(self) -> ProgramDataSigner:
        """
        Signer for program data (LogicSig data).

        Signs data prefixed with "ProgData" domain separator.
        Used during transaction signing with delegated LogicSigs.
        """
        ...

    @property
    def bytes_signer(self) -> BytesSigner:
        """
        Raw bytes signer.

        Signs arbitrary bytes without domain prefix.
        This is the lowest-level signer interface.
        """
        ...
