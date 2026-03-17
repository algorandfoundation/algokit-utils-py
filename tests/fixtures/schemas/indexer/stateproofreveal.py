from pydantic import BaseModel, ConfigDict, Field


class StateProofRevealSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    position: int | None = Field(default=None, alias="position")
    sig_slot: "StateProofSigSlotSchema | None" = Field(default=None, alias="sig-slot")
    participant: "StateProofParticipantSchema | None" = Field(default=None, alias="participant")
