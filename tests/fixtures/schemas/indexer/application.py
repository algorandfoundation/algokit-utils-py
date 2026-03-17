from pydantic import BaseModel, ConfigDict, Field


class ApplicationSchema(BaseModel):
    """Application index and its parameters"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id_: int = Field(alias="id")
    deleted: bool | None = Field(default=None, alias="deleted")
    created_at_round: int | None = Field(default=None, alias="created-at-round")
    deleted_at_round: int | None = Field(default=None, alias="deleted-at-round")
    params: "ApplicationParamsSchema" = Field(alias="params")
