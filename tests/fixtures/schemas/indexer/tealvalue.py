from pydantic import BaseModel, ConfigDict, Field


class TealValueSchema(BaseModel):
    """Represents a TEAL value."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    type: int = Field(alias="type")
    bytes: str = Field(alias="bytes")
    uint: int = Field(alias="uint")
