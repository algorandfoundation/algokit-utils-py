from pydantic import BaseModel, ConfigDict, Field


class MultisigSigSchema(BaseModel):
    """MultisigSig is the structure that holds multiple Subsigs"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    subsig: "list[MultisigSubsigSchema]" = Field(alias="subsig")
    thr: int = Field(alias="thr")
    v: int = Field(alias="v")
