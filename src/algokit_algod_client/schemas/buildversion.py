from pydantic import BaseModel, ConfigDict, Field


class BuildVersionSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    branch: str = Field(default=None, alias="branch")
    build_number: int = Field(default=None, alias="build_number")
    channel: str = Field(default=None, alias="channel")
    commit_hash: str = Field(default=None, alias="commit_hash")
    major: int = Field(default=None, alias="major")
    minor: int = Field(default=None, alias="minor")
