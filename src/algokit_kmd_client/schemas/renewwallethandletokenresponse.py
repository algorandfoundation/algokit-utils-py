from pydantic import BaseModel, ConfigDict, Field


class RenewWalletHandleTokenResponseSchema(BaseModel):
    """RenewWalletHandleTokenResponse is the response to `POST /v1/wallet/renew`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle: "WalletHandleSchema" = Field(default=None, alias="wallet_handle")
