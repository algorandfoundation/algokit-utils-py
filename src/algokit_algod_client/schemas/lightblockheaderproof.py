from pydantic import BaseModel, ConfigDict, Field


class LightBlockHeaderProofSchema(BaseModel):
    """Proof of membership and position of a light block header."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    index: int = Field(default=None, alias="index")
    treedepth: int = Field(default=None, alias="treedepth")
    proof: str = Field(default=None, alias="proof")
