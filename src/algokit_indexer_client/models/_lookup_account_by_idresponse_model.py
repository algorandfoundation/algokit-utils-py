# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._account import Account


@dataclass(slots=True)
class LookupAccountByIdresponseModel:
    account: Account = field(
        metadata=nested("account", lambda: Account),
    )
    current_round: int = field(
        metadata=wire("current-round"),
    )
