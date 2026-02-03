from pydantic import BaseModel, ConfigDict, Field


class AssetHoldingSchema(BaseModel):
    """Describes an asset held by an account.

    Definition:
    data/basics/userBalance.go : AssetHolding"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    amount: int = Field(default=None, alias="amount")
    asset_id: int = Field(default=None, alias="asset-id")
    is_frozen: bool = Field(default=None, alias="is-frozen")
    deleted: bool | None = Field(default=None, alias="deleted")
    opted_in_at_round: int | None = Field(default=None, alias="opted-in-at-round")
    opted_out_at_round: int | None = Field(default=None, alias="opted-out-at-round")
