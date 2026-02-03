from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class AccountApplicationResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    round: int = Field(default=None, alias="round")
    app_local_state: "ApplicationLocalStateSchema | None" = Field(default=None, alias="app-local-state")
    created_app: "ApplicationParamsSchema | None" = Field(default=None, alias="created-app")
