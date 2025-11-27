# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class TransactionPayment:
    """
    Fields for a payment transaction.

    Definition:
    data/transactions/payment.go : PaymentTxnFields
    """

    amount: int = field(
        default=0,
        metadata=wire("amount"),
    )
    receiver: str = field(
        default="",
        metadata=wire("receiver"),
    )
    close_amount: int | None = field(
        default=None,
        metadata=wire("close-amount"),
    )
    close_remainder_to: str | None = field(
        default=None,
        metadata=wire("close-remainder-to"),
    )
