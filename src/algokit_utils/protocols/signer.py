from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from algokit_transact.models.transaction import Transaction

__all__ = [
    "BytesSigner",
    "LsigSigner",
    "MxBytesSigner",
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
    """Raw bytes signer (ed25519 signature over input)."""

    def __call__(self, data: bytes) -> bytes: ...


@runtime_checkable
class ProgramDataSigner(Protocol):
    """Signs data with 'ProgData' + program_address prefix."""

    def __call__(self, data: bytes, program_address: bytes) -> bytes: ...


@runtime_checkable
class LsigSigner(Protocol):
    """Signs LogicSig programs for delegation.

    Without msig_address: signs "Program" + program
    With msig_address: signs "MsigProgram" + msig_address + program
    """

    def __call__(self, program: bytes, msig_address: bytes | None = None) -> bytes: ...


@runtime_checkable
class MxBytesSigner(Protocol):
    """Signs arbitrary bytes with "MX" domain prefix."""

    def __call__(self, data: bytes) -> bytes: ...
