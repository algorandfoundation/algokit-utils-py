from pydantic import BaseModel, ConfigDict, Field


class ApplicationSchema(BaseModel):
    """Application index and its parameters"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id_: int = Field(alias="id")
    params: "ApplicationParamsSchema" = Field(alias="params")
