from pydantic import BaseModel, ConfigDict, Field


class ApplicationLocalStateSchema(BaseModel):
    """Stores local state associated with an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: int = Field(alias="id")
    deleted: bool | None = Field(default=None, alias="deleted")
    opted_in_at_round: int | None = Field(default=None, alias="opted-in-at-round")
    closed_out_at_round: int | None = Field(default=None, alias="closed-out-at-round")
    schema_: "ApplicationStateSchemaSchema" = Field(alias="schema")
    key_value: "TealKeyValueStoreSchema | None" = Field(default=None, alias="key-value")
