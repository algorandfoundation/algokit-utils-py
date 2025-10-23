from __future__ import annotations

from .errors import TransactionValidationError
from .types import Transaction


def validate_transaction(transaction: Transaction) -> None:
    if not transaction.sender:
        raise TransactionValidationError("Transaction sender is required")

    type_fields = [
        transaction.payment,
        transaction.asset_transfer,
        transaction.asset_config,
        transaction.app_call,
        transaction.key_registration,
        transaction.asset_freeze,
    ]
    set_count = sum(1 for f in type_fields if f is not None)
    if set_count == 0:
        raise TransactionValidationError("No transaction type specific field is set")
    if set_count > 1:
        raise TransactionValidationError("Multiple transaction type specific fields set")
