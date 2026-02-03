from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ListKeysResponseSchema(BaseModel):
    """ListKeysResponse is the response to `POST /v1/key/list`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    addresses: list[str] = Field(default=None, alias="addresses")
