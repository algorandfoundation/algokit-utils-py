from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class BlockHashResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    blockHash: str = Field(default=None, alias="blockHash")
