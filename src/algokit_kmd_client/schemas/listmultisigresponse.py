from pydantic import BaseModel, ConfigDict, Field


class ListMultisigResponseSchema(BaseModel):
    """ListMultisigResponse is the response to `POST /v1/multisig/list`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    addresses: list[str] = Field(default=None, alias="addresses")
