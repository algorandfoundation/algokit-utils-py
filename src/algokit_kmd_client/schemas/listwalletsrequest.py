from pydantic import BaseModel, ConfigDict


class ListWalletsRequestSchema(BaseModel):
    """APIV1GETWalletsRequest is the request for `GET /v1/wallets`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, extra="allow")
