from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class BlockTxidsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    blockTxids: list[str] = Field(default=None, alias="blockTxids")
