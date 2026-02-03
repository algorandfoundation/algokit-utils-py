from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class SimulateTraceConfigSchema(BaseModel):
    """An object that configures simulation execution trace."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    enable: bool | None = Field(default=None, alias="enable")
    stack_change: bool | None = Field(default=None, alias="stack-change")
    scratch_change: bool | None = Field(default=None, alias="scratch-change")
    state_change: bool | None = Field(default=None, alias="state-change")
