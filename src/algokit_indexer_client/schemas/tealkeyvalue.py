from pydantic import BaseModel, ConfigDict, Field


class TealKeyValueSchema(BaseModel):
    """Represents a key-value pair in an application store."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    key: str = Field(default=None, alias="key")
    value: "TealValueSchema" = Field(default=None, alias="value")
