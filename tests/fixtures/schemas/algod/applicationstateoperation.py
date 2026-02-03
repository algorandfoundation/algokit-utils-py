from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ApplicationStateOperationSchema(BaseModel):
    """An operation against an application's global/local/box state."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    operation: str = Field(default=None, alias="operation")
    app_state_type: str = Field(default=None, alias="app-state-type")
    key: str = Field(default=None, alias="key")
    new_value: "AvmValueSchema | None" = Field(default=None, alias="new-value")
    account: str | None = Field(default=None, alias="account")
