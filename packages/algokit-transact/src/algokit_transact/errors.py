class AlgokitTransactError(Exception):
    """Base error for algokit-transact."""


class TransactionValidationError(AlgokitTransactError):
    """Raised when a transaction fails validation."""
