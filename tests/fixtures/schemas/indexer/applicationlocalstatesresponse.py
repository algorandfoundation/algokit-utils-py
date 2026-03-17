from pydantic import BaseModel, ConfigDict, Field


class ApplicationLocalStatesResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    apps_local_states: "list[ApplicationLocalStateSchema]" = Field(alias="apps-local-states")
    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")
