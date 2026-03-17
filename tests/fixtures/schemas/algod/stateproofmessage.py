from pydantic import BaseModel, ConfigDict, Field


class StateProofMessageSchema(BaseModel):
    """Represents the message that the state proofs are attesting to."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    block_headers_commitment: str = Field(alias="BlockHeadersCommitment")
    voters_commitment: str = Field(alias="VotersCommitment")
    ln_proven_weight: int = Field(ge=0, le=18446744073709551615, alias="LnProvenWeight")
    first_attested_round: int = Field(alias="FirstAttestedRound")
    last_attested_round: int = Field(alias="LastAttestedRound")
