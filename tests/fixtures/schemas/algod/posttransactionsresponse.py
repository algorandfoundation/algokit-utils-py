from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PostTransactionsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txId: str = Field(default=None, alias="txId")
