from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class AssetsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    assets: "list[AssetSchema]" = Field(default=None, alias="assets")
    current_round: int = Field(default=None, alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")
