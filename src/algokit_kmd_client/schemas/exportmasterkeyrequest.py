from pydantic import BaseModel, ConfigDict, Field


class ExportMasterKeyRequestSchema(BaseModel):
    """The request for `POST /v1/master-key/export`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(default=None, alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")
