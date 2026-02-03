from pydantic import BaseModel, ConfigDict, Field


class CatchpointAbortResponseSchema(BaseModel):
    """An catchpoint abort response."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    catchup_message: str = Field(default=None, alias="catchup-message")
