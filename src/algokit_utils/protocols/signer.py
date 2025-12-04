from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from algokit_transact.models.transaction import Transaction

__all__ = [
    "BytesSigner",
    "LsigSigner",
    "ProgramDataSigner",
    "TransactionSigner",
]


@runtime_checkable
class TransactionSigner(Protocol):
    """Signature for AlgoKit-native transaction signers."""

    def __call__(self, txn_group: Sequence[Transaction], indexes_to_sign: Sequence[int]) -> Sequence[bytes]:
        """Sign the transactions at the specified indexes within the provided group."""
        ...


@runtime_checkable
class BytesSigner(Protocol):
    """
    Protocol for a raw bytes signer.

    Signs arbitrary bytes (typically an ed25519 signature over the input).
    This is the lowest-level signer interface, used to build higher-level signers.

    Example:
        def my_bytes_signer(data: bytes) -> bytes:
            # Sign using KMS, hardware wallet, etc.
            return signature_bytes
    """

    def __call__(self, data: bytes) -> bytes:
        """Sign the given bytes and return the signature."""
        ...


@runtime_checkable
class ProgramDataSigner(Protocol):
    """
    Protocol for signing program data (LogicSig data).

    Signs data prefixed with the "ProgData" domain separator.
    Used for delegated LogicSig signatures where the signature
    covers the program hash concatenated with the transaction data.

    Example:
        def my_program_data_signer(data: bytes) -> bytes:
            # Sign: b"ProgData" + data
            return signature_bytes
    """

    def __call__(self, data: bytes) -> bytes:
        """Sign the given program data and return the signature."""
        ...


@runtime_checkable
class LsigSigner(Protocol):
    """
    Protocol for signing LogicSig programs.

    Signs the program itself prefixed with the "Program" domain separator.
    Used when delegating a LogicSig to an account (single-sig delegation).

    Example:
        def my_lsig_signer(program: bytes) -> bytes:
            # Sign: b"Program" + program
            return signature_bytes
    """

    def __call__(self, program: bytes) -> bytes:
        """Sign the given LogicSig program and return the signature."""
        ...
