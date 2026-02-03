from pydantic import BaseModel, ConfigDict, Field


class ApplicationLogDataSchema(BaseModel):
    """Stores the global information associated with an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txid: str = Field(default=None, alias="txid")
    logs: list[str] = Field(default=None, alias="logs")
