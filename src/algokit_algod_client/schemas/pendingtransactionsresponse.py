from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PendingTransactionsResponseSchema(BaseModel):
    """PendingTransactions is an array of signed transactions exactly as they were submitted."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    top_transactions: list[dict[str, Any]] = Field(default=None, alias="top-transactions")
    total_transactions: int = Field(default=None, alias="total-transactions")
