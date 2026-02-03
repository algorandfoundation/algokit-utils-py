from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ErrorResponseSchema(BaseModel):
    """An error response with optional data field."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    data: dict[str, Any] | None = Field(default=None, alias="data")
    message: str = Field(default=None, alias="message")
