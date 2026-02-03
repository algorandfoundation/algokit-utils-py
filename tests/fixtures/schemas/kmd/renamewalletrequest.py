from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class RenameWalletRequestSchema(BaseModel):
    """The request for `POST /v1/wallet/rename`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_id: str = Field(default=None, alias="wallet_id")
    wallet_name: str = Field(default=None, alias="wallet_name")
    wallet_password: str = Field(default=None, alias="wallet_password")
