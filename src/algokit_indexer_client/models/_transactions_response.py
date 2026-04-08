# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from ._transaction import Transaction


@dataclass(slots=True)
class TransactionsResponse:
    current_round: int = field(
        default=0,
        metadata=wire("current-round"),
    )
    transactions: list[Transaction] = field(
        default_factory=list,
        metadata=wire(
            "transactions",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Transaction, raw),
        ),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
