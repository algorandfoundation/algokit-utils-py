from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DebugSettingsProfSchema(BaseModel):
    """algod mutex and blocking profiling state."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    block_rate: int | None = Field(default=None, ge=0, le=18446744073709551615, alias="block-rate")
    mutex_rate: int | None = Field(default=None, ge=0, le=18446744073709551615, alias="mutex-rate")
