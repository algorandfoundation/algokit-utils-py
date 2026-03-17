from pydantic import BaseModel, ConfigDict, Field


class SimulateUnnamedResourcesAccessedSchema(BaseModel):
    """These are resources that were accessed by this group that would normally have caused failure, but were allowed in simulation. Depending on where this object is in the response, the unnamed resources it contains may or may not qualify for group resource sharing. If this is a field in SimulateTransactionGroupResult, the resources do qualify, but if this is a field in SimulateTransactionResult, they do not qualify. In order to make this group valid for actual submission, resources that qualify for group sharing can be made available by any transaction of the group; otherwise, resources must be placed in the same transaction which accessed them."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    accounts: list[str] | None = Field(default=None, alias="accounts")
    assets: list[int] | None = Field(default=None, alias="assets")
    apps: list[int] | None = Field(default=None, alias="apps")
    boxes: "list[BoxReferenceSchema] | None" = Field(default=None, alias="boxes")
    extra_box_refs: int | None = Field(default=None, alias="extra-box-refs")
    asset_holdings: "list[AssetHoldingReferenceSchema] | None" = Field(default=None, alias="asset-holdings")
    app_locals: "list[ApplicationLocalReferenceSchema] | None" = Field(default=None, alias="app-locals")
