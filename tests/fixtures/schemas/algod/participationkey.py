from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ParticipationKeySchema(BaseModel):
    """Represents a participation key used by the node."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: str = Field(default=None, alias="id")
    address: str = Field(default=None, alias="address")
    effective_first_valid: int | None = Field(default=None, alias="effective-first-valid")
    effective_last_valid: int | None = Field(default=None, alias="effective-last-valid")
    last_vote: int | None = Field(default=None, alias="last-vote")
    last_block_proposal: int | None = Field(default=None, alias="last-block-proposal")
    last_state_proof: int | None = Field(default=None, alias="last-state-proof")
    key: "AccountParticipationSchema" = Field(default=None, alias="key")
