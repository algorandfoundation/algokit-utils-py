from pydantic import BaseModel, ConfigDict, Field


class AccountStateDeltaSchema(BaseModel):
    """Application state delta."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    delta: "StateDeltaSchema" = Field(alias="delta")
