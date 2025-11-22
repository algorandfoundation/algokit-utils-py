from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from algokit_transact.models.transaction import Transaction

__all__ = ["TransactionSigner"]


@runtime_checkable
class TransactionSigner(Protocol):
    """Signature for AlgoKit-native transaction signers."""

    def __call__(self, txn_group: Sequence[Transaction], indexes_to_sign: Sequence[int]) -> Sequence[bytes]:
        """Sign the transactions at the specified indexes within the provided group."""
        ...
