from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class WalletInfoRequestSchema(BaseModel):
    """The request for `POST /v1/wallet/info`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(default=None, alias="wallet_handle_token")
