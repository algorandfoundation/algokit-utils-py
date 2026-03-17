from pydantic import BaseModel, ConfigDict, Field


class BlockRewardsSchema(BaseModel):
    """Fields relating to rewards,"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    fee_sink: str = Field(alias="fee-sink")
    rewards_calculation_round: int = Field(alias="rewards-calculation-round")
    rewards_level: int = Field(alias="rewards-level")
    rewards_pool: str = Field(alias="rewards-pool")
    rewards_rate: int = Field(alias="rewards-rate")
    rewards_residue: int = Field(alias="rewards-residue")
