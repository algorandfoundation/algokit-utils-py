# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class SupplyResponse:
    """
    Supply represents the current supply of MicroAlgos in the system
    """

    current_round: int = field(
        default=0,
        metadata=wire("current_round"),
    )
    online_money: int = field(
        default=0,
        metadata=wire("online-money"),
    )
    total_money: int = field(
        default=0,
        metadata=wire("total-money"),
    )
