from pydantic import BaseModel, ConfigDict, Field


class SignProgramResponseSchema(BaseModel):
    """SignProgramResponse is the response to `POST /v1/data/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    sig: str = Field(default=None, alias="sig")
