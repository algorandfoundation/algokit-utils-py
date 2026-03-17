from pydantic import BaseModel, ConfigDict, Field


class StateProofMessageSchema(BaseModel):
    """Represents the message that the state proofs are attesting to."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    BlockHeadersCommitment: str = Field(alias="BlockHeadersCommitment")
    VotersCommitment: str = Field(alias="VotersCommitment")
    LnProvenWeight: int = Field(ge=0, le=18446744073709551615, alias="LnProvenWeight")
    FirstAttestedRound: int = Field(alias="FirstAttestedRound")
    LastAttestedRound: int = Field(alias="LastAttestedRound")
