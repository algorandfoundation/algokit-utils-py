from pydantic import BaseModel, ConfigDict, Field


class ListWalletsResponseSchema(BaseModel):
    """ListWalletsResponse is the response to `GET /v1/wallets`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallets: "list[WalletSchema]" = Field(default=None, alias="wallets")
