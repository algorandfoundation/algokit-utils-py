from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class LocalsRefSchema(BaseModel):
    """LocalsRef names a local state by referring to an Address and App it belongs to."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(default=None, alias="address")
    app: int = Field(default=None, alias="app")
