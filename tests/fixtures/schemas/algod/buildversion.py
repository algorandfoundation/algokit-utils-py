from pydantic import BaseModel, ConfigDict, Field


class BuildVersionSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    branch: str = Field(alias="branch")
    build_number: int = Field(alias="build_number")
    channel: str = Field(alias="channel")
    commit_hash: str = Field(alias="commit_hash")
    major: int = Field(alias="major")
    minor: int = Field(alias="minor")
