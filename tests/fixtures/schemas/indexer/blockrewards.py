from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class BlockRewardsSchema(BaseModel):
    """Fields relating to rewards,"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    fee_sink: str = Field(default=None, alias="fee-sink")
    rewards_calculation_round: int = Field(default=None, alias="rewards-calculation-round")
    rewards_level: int = Field(default=None, alias="rewards-level")
    rewards_pool: str = Field(default=None, alias="rewards-pool")
    rewards_rate: int = Field(default=None, alias="rewards-rate")
    rewards_residue: int = Field(default=None, alias="rewards-residue")
