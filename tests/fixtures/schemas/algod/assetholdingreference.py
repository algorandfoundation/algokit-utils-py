from pydantic import BaseModel, ConfigDict, Field


class AssetHoldingReferenceSchema(BaseModel):
    """References an asset held by an account."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    account: str = Field(alias="account")
    asset: int = Field(alias="asset")
