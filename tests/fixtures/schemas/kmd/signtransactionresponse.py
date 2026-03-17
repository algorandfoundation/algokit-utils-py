from pydantic import BaseModel, ConfigDict, Field


class SignTransactionResponseSchema(BaseModel):
    """SignTransactionResponse is the response to `POST /v1/transaction/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    signed_transaction: str = Field(alias="signed_transaction")
