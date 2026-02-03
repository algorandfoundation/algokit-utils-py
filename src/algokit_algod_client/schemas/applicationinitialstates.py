from pydantic import BaseModel, ConfigDict, Field


class ApplicationInitialStatesSchema(BaseModel):
    """An application's initial global/local/box states that were accessed during simulation."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: int = Field(default=None, alias="id")
    app_locals: "list[ApplicationKVStorageSchema] | None" = Field(default=None, alias="app-locals")
    app_globals: "ApplicationKVStorageSchema | None" = Field(default=None, alias="app-globals")
    app_boxes: "ApplicationKVStorageSchema | None" = Field(default=None, alias="app-boxes")
