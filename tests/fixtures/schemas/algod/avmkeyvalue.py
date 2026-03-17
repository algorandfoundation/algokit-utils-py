from pydantic import BaseModel, ConfigDict, Field


class AvmKeyValueSchema(BaseModel):
    """Represents an AVM key-value pair in an application store."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    key: str = Field(alias="key")
    value: "AvmValueSchema" = Field(alias="value")
