from pydantic import BaseModel, ConfigDict, Field


class WalletHandleSchema(BaseModel):
    """WalletHandle includes the wallet the handle corresponds to
    and the number of number of seconds to expiration"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    expires_seconds: int = Field(default=None, alias="expires_seconds")
    wallet: "WalletSchema" = Field(default=None, alias="wallet")
