from pydantic import BaseModel, ConfigDict, Field


class AvmValueSchema(BaseModel):
    """Represents an AVM value."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    type: int = Field(default=None, alias="type")
    bytes: str | None = Field(default=None, alias="bytes")
    uint: int | None = Field(default=None, ge=0, le=18446744073709551615, alias="uint")
