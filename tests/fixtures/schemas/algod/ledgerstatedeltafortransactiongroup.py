from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class LedgerStateDeltaForTransactionGroupSchema(BaseModel):
    """Contains a ledger delta for a single transaction group"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    Delta: "LedgerStateDeltaSchema" = Field(default=None, alias="Delta")
    Ids: list[str] = Field(default=None, alias="Ids")
