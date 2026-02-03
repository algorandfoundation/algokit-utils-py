from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class EvalDeltaSchema(BaseModel):
    """Represents a TEAL value delta."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    action: int = Field(default=None, alias="action")
    bytes: str | None = Field(default=None, alias="bytes")
    uint: int | None = Field(default=None, alias="uint")
