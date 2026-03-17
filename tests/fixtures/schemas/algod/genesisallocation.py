from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class GenesisAllocationSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    addr: str = Field(alias="addr")
    comment: str = Field(alias="comment")
    state: dict[str, Any] = Field(alias="state")
