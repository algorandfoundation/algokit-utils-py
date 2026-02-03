from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ExportKeyResponseSchema(BaseModel):
    """ExportKeyResponse is the response to `POST /v1/key/export`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    private_key: str = Field(default=None, alias="private_key")
