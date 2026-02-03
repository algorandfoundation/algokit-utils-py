from pydantic import BaseModel, ConfigDict, Field


class TransactionResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    transaction: "TransactionSchema" = Field(default=None, alias="transaction")
    current_round: int = Field(default=None, alias="current-round")
