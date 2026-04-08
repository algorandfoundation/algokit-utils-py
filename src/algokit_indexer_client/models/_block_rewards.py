# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BlockRewards:
    """
    Fields relating to rewards,
    """

    fee_sink: str = field(
        default="",
        metadata=wire("fee-sink"),
    )
    rewards_calculation_round: int = field(
        default=0,
        metadata=wire("rewards-calculation-round"),
    )
    rewards_level: int = field(
        default=0,
        metadata=wire("rewards-level"),
    )
    rewards_pool: str = field(
        default="",
        metadata=wire("rewards-pool"),
    )
    rewards_rate: int = field(
        default=0,
        metadata=wire("rewards-rate"),
    )
    rewards_residue: int = field(
        default=0,
        metadata=wire("rewards-residue"),
    )
