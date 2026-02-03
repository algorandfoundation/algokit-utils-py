from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ApplicationParamsSchema(BaseModel):
    """Stores the global information associated with an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    creator: str | None = Field(default=None, alias="creator")
    approval_program: str | None = Field(default=None, alias="approval-program")
    clear_state_program: str | None = Field(default=None, alias="clear-state-program")
    extra_program_pages: int | None = Field(default=None, ge=0, le=3, alias="extra-program-pages")
    local_state_schema: "ApplicationStateSchemaSchema | None" = Field(default=None, alias="local-state-schema")
    global_state_schema: "ApplicationStateSchemaSchema | None" = Field(default=None, alias="global-state-schema")
    global_state: "TealKeyValueStoreSchema | None" = Field(default=None, alias="global-state")
    version: int | None = Field(default=None, alias="version")
