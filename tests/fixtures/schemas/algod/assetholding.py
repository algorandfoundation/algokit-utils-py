from pydantic import BaseModel, ConfigDict, Field


class AssetHoldingSchema(BaseModel):
    """Describes an asset held by an account.

    Definition:
    data/basics/userBalance.go : AssetHolding"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    amount: int = Field(ge=0, le=18446744073709551615, alias="amount")
    asset_id: int = Field(alias="asset-id")
    is_frozen: bool = Field(alias="is-frozen")
