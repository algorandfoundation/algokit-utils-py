from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .account import Account


@dataclass(slots=True)
class SearchForAccountsResponseModel:
    accounts: list[Account] = field(
        metadata=wire(
            "accounts",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Account, raw),
        ),
    )
    current_round: int = field(
        metadata=wire("current-round"),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
