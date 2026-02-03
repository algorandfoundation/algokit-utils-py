from pydantic import BaseModel, ConfigDict


class TxTypeSchema(BaseModel):
    """TxType is the type of the transaction written to the ledger"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, extra="allow")
