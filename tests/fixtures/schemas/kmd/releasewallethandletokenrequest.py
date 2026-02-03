from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ReleaseWalletHandleTokenRequestSchema(BaseModel):
    """The request for `POST /v1/wallet/release`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(default=None, alias="wallet_handle_token")
