from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class AccountParticipationSchema(BaseModel):
    """AccountParticipation describes the parameters used by this account in consensus protocol."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    selection_participation_key: str = Field(default=None, alias="selection-participation-key")
    vote_first_valid: int = Field(default=None, alias="vote-first-valid")
    vote_key_dilution: int = Field(default=None, alias="vote-key-dilution")
    vote_last_valid: int = Field(default=None, alias="vote-last-valid")
    vote_participation_key: str = Field(default=None, alias="vote-participation-key")
    state_proof_key: str | None = Field(default=None, alias="state-proof-key")
