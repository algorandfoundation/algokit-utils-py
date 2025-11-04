# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._transaction import Transaction


@dataclass(slots=True)
class LookupTransactionResponseModel:
    current_round: int = field(
        metadata=wire("current-round"),
    )
    transaction: Transaction = field(
        metadata=nested("transaction", lambda: Transaction),
    )
