from pydantic import BaseModel, ConfigDict, Field


class CatchpointStartResponseSchema(BaseModel):
    """An catchpoint start response."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    catchup_message: str = Field(default=None, alias="catchup-message")
