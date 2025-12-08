# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._account import Account
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class AccountsResponse:
    accounts: list[Account] = field(
        default_factory=list,
        metadata=wire(
            "accounts",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Account, raw),
        ),
    )
    current_round: int = field(
        default=0,
        metadata=wire("current-round"),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
