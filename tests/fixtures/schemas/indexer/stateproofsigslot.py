from pydantic import BaseModel, ConfigDict, Field


class StateProofSigSlotSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    signature: "StateProofSignatureSchema | None" = Field(default=None, alias="signature")
    lower_sig_weight: int | None = Field(default=None, alias="lower-sig-weight")
