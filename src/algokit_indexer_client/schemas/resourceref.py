from pydantic import BaseModel, ConfigDict, Field


class ResourceRefSchema(BaseModel):
    """ResourceRef names a single resource. Only one of the fields should be set."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str | None = Field(default=None, alias="address")
    application_id: int | None = Field(default=None, alias="application-id")
    asset_id: int | None = Field(default=None, alias="asset-id")
    box: "BoxReferenceSchema | None" = Field(default=None, alias="box")
    holding: "HoldingRefSchema | None" = Field(default=None, alias="holding")
    local: "LocalsRefSchema | None" = Field(default=None, alias="local")
