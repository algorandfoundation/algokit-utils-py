from pydantic import BaseModel, ConfigDict, Field


class StateProofParticipantSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    verifier: "StateProofVerifierSchema | None" = Field(default=None, alias="verifier")
    weight: int | None = Field(default=None, alias="weight")
