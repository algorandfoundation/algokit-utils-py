from pydantic import BaseModel, ConfigDict, Field


class StateProofSchema(BaseModel):
    """Represents a state proof and its corresponding message"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    Message: "StateProofMessageSchema" = Field(default=None, alias="Message")
    StateProof: str = Field(default=None, alias="StateProof")
