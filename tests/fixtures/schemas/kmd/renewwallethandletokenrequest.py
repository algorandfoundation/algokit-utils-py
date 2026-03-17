from pydantic import BaseModel, ConfigDict, Field


class RenewWalletHandleTokenRequestSchema(BaseModel):
    """The request for `POST /v1/wallet/renew`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(alias="wallet_handle_token")
