from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DryrunResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txns: "list[DryrunTxnResultSchema]" = Field(default=None, alias="txns")
    error: str = Field(default=None, alias="error")
    protocol_version: str = Field(default=None, alias="protocol-version")
