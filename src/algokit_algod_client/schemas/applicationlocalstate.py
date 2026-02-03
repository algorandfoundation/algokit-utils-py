from pydantic import BaseModel, ConfigDict, Field


class ApplicationLocalStateSchema(BaseModel):
    """Stores local state associated with an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: int = Field(default=None, alias="id")
    schema_: "ApplicationStateSchemaSchema" = Field(default=None, alias="schema")
    key_value: "TealKeyValueStoreSchema | None" = Field(default=None, alias="key-value")
