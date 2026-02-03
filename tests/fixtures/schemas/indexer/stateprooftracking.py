from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class StateProofTrackingSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    type: int | None = Field(default=None, alias="type")
    voters_commitment: str | None = Field(default=None, alias="voters-commitment")
    online_total_weight: int | None = Field(default=None, alias="online-total-weight")
    next_round: int | None = Field(default=None, alias="next-round")
