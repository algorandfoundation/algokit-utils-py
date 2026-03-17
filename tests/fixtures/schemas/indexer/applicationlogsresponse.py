from pydantic import BaseModel, ConfigDict, Field


class ApplicationLogsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    application_id: int = Field(alias="application-id")
    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")
    log_data: "list[ApplicationLogDataSchema] | None" = Field(default=None, alias="log-data")
