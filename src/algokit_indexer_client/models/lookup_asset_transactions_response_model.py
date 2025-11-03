# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .transaction import Transaction


@dataclass(slots=True)
class LookupAssetTransactionsResponseModel:
    current_round: int = field(
        metadata=wire("current-round"),
    )
    transactions: list[Transaction] = field(
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
