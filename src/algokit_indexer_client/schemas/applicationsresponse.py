from pydantic import BaseModel, ConfigDict, Field


class ApplicationsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    applications: "list[ApplicationSchema]" = Field(default=None, alias="applications")
    current_round: int = Field(default=None, alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")
