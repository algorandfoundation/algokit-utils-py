from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class BoxSchema(BaseModel):
    """Box name and its content."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    round: int = Field(default=None, alias="round")
    name: str = Field(default=None, alias="name")
    value: str = Field(default=None, alias="value")
