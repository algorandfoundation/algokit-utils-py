from pydantic import BaseModel, ConfigDict, Field


class ApplicationKVStorageSchema(BaseModel):
    """An application's global/local/box state."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    kvs: "list[AvmKeyValueSchema]" = Field(default=None, alias="kvs")
    account: str | None = Field(default=None, alias="account")
