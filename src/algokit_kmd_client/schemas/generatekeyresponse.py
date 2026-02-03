from pydantic import BaseModel, ConfigDict, Field


class GenerateKeyResponseSchema(BaseModel):
    """GenerateKeyResponse is the response to `POST /v1/key`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(default=None, alias="address")
