from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ScratchChangeSchema(BaseModel):
    """A write operation into a scratch slot."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    slot: int = Field(default=None, alias="slot")
    new_value: "AvmValueSchema" = Field(default=None, alias="new-value")
