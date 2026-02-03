from pydantic import BaseModel, ConfigDict, Field


class DeleteKeyRequestSchema(BaseModel):
    """The request for `DELETE /v1/key`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(default=None, alias="address")
    wallet_handle_token: str = Field(default=None, alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")
