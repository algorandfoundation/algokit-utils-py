from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BlockResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    block: dict[str, Any] = Field(default=None, alias="block")
    cert: dict[str, Any] | None = Field(default=None, alias="cert")
