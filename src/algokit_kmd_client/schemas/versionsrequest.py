from pydantic import BaseModel, ConfigDict


class VersionsRequestSchema(BaseModel):
    """VersionsRequest is the request for `GET /versions`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, extra="allow")
