from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ImportKeyResponseSchema(BaseModel):
    """ImportKeyResponse is the response to `POST /v1/key/import`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(default=None, alias="address")
