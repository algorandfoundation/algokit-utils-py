from pydantic import BaseModel, ConfigDict, Field


class AppCallLogsSchema(BaseModel):
    """The logged messages from an app call along with the app ID and outer transaction ID. Logs appear in the same order that they were emitted."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    logs: list[str] = Field(alias="logs")
    app_id: int = Field(alias="application-index")
    tx_id: str = Field(alias="txId")
