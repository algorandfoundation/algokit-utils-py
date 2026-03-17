from pydantic import BaseModel, ConfigDict, Field


class PostTransactionsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    tx_id: str = Field(alias="txId")
