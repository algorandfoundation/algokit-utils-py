from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class SignTxnRequestSchema(BaseModel):
    """The request for `POST /v1/transaction/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    public_key: "PublicKeySchema | None" = Field(default=None, alias="public_key")
    transaction: str = Field(default=None, alias="transaction")
    wallet_handle_token: str = Field(default=None, alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")
