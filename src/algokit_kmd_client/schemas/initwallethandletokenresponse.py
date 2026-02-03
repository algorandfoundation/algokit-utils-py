from pydantic import BaseModel, ConfigDict, Field


class InitWalletHandleTokenResponseSchema(BaseModel):
    """InitWalletHandleTokenResponse is the response to `POST /v1/wallet/init`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(default=None, alias="wallet_handle_token")
