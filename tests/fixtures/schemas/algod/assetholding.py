from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class AssetHoldingSchema(BaseModel):
    """Describes an asset held by an account.

    Definition:
    data/basics/userBalance.go : AssetHolding"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    amount: int = Field(default=None, ge=0, le=18446744073709551615, alias="amount")
    asset_id: int = Field(default=None, alias="asset-id")
    is_frozen: bool = Field(default=None, alias="is-frozen")
