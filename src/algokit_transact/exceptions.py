from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from algokit_transact.ops.validate import ValidationIssue


class AlgokitTransactError(Exception):
    """Base error for algokit-transact."""


class TransactionValidationError(AlgokitTransactError):
    """Raised when a transaction fails validation."""

    def __init__(self, message: str, *, issues: "Sequence[ValidationIssue] | None" = None) -> None:
        super().__init__(message)
        self.issues: list[ValidationIssue] = list(issues or [])
