from pydantic import BaseModel, ConfigDict, Field


class RenameWalletRequestSchema(BaseModel):
    """The request for `POST /v1/wallet/rename`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_id: str = Field(alias="wallet_id")
    wallet_name: str = Field(alias="wallet_name")
    wallet_password: str = Field(alias="wallet_password")
