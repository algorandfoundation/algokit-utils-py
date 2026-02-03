from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class RenameWalletResponseSchema(BaseModel):
    """RenameWalletResponse is the response to `POST /v1/wallet/rename`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet: "WalletSchema" = Field(default=None, alias="wallet")
