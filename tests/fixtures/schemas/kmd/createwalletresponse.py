from pydantic import BaseModel, ConfigDict, Field


class CreateWalletResponseSchema(BaseModel):
    """CreateWalletResponse is the response to `POST /v1/wallet`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet: "WalletSchema" = Field(alias="wallet")
