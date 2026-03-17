from pydantic import BaseModel, ConfigDict, Field


class TransactionPaymentSchema(BaseModel):
    """Fields for a payment transaction.

    Definition:
    data/transactions/payment.go : PaymentTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    amount: int = Field(alias="amount")
    close_amount: int | None = Field(default=None, alias="close-amount")
    close_remainder_to: str | None = Field(default=None, alias="close-remainder-to")
    receiver: str = Field(alias="receiver")
