from pydantic import BaseModel, ConfigDict, Field


class TransactionGroupLedgerStateDeltasForRoundResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    Deltas: "list[LedgerStateDeltaForTransactionGroupSchema]" = Field(alias="Deltas")
