from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ApplicationLocalReferenceSchema(BaseModel):
    """References an account's local state for an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    account: str = Field(default=None, alias="account")
    app: int = Field(default=None, alias="app")
