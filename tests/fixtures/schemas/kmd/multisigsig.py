from pydantic import BaseModel, ConfigDict, Field


class MultisigSigSchema(BaseModel):
    """MultisigSig is the structure that holds multiple Subsigs"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    subsignatures: "list[MultisigSubsigSchema]" = Field(alias="subsig")
    threshold: int = Field(alias="thr")
    version: int = Field(alias="v")
