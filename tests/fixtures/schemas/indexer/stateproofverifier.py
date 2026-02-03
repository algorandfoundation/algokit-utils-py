from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class StateProofVerifierSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    commitment: str | None = Field(default=None, alias="commitment")
    key_lifetime: int | None = Field(default=None, alias="key-lifetime")
