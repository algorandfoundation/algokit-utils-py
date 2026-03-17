from pydantic import BaseModel, ConfigDict, Field


class InitWalletHandleTokenRequestSchema(BaseModel):
    """The request for `POST /v1/wallet/init`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_id: str = Field(alias="wallet_id")
    wallet_password: str = Field(alias="wallet_password")
