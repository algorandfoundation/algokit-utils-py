# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._account import Account


@dataclass(slots=True)
class AccountResponse:
    account: Account = field(
        metadata=nested("account", lambda: Account, required=True),
    )
    current_round: int = field(
        default=0,
        metadata=wire("current-round"),
    )
