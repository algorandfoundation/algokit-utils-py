from pydantic import BaseModel, ConfigDict, Field


class AssetSchema(BaseModel):
    """Specifies both the unique identifier and the parameters for an asset"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    index: int = Field(alias="index")
    params: "AssetParamsSchema" = Field(alias="params")
