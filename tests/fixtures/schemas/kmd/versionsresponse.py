from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class VersionsResponseSchema(BaseModel):
    """VersionsResponse is the response to `GET /versions`
    friendly:VersionsResponse"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    versions: list[str] = Field(default=None, alias="versions")
