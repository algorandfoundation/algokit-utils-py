from pydantic import BaseModel, ConfigDict, Field


class ImportKeyRequestSchema(BaseModel):
    """The request for `POST /v1/key/import`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    private_key: str = Field(alias="private_key")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
