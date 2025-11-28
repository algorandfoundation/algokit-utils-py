# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._transaction import Transaction


@dataclass(slots=True)
class TransactionResponse:
    transaction: Transaction = field(
        metadata=nested("transaction", lambda: Transaction, required=True),
    )
    current_round: int = field(
        default=0,
        metadata=wire("current-round"),
    )
