from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class StateProofMessageSchema(BaseModel):
    """Represents the message that the state proofs are attesting to."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    BlockHeadersCommitment: str = Field(default=None, alias="BlockHeadersCommitment")
    VotersCommitment: str = Field(default=None, alias="VotersCommitment")
    LnProvenWeight: int = Field(default=None, ge=0, le=18446744073709551615, alias="LnProvenWeight")
    FirstAttestedRound: int = Field(default=None, alias="FirstAttestedRound")
    LastAttestedRound: int = Field(default=None, alias="LastAttestedRound")
