# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BlockRewards:
    """
    Fields relating to rewards,
    """

    fee_sink: str = field(
        metadata=wire("fee-sink"),
    )
    rewards_calculation_round: int = field(
        metadata=wire("rewards-calculation-round"),
    )
    rewards_level: int = field(
        metadata=wire("rewards-level"),
    )
    rewards_pool: str = field(
        metadata=wire("rewards-pool"),
    )
    rewards_rate: int = field(
        metadata=wire("rewards-rate"),
    )
    rewards_residue: int = field(
        metadata=wire("rewards-residue"),
    )
