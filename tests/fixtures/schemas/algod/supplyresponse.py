from pydantic import BaseModel, ConfigDict, Field


class SupplyResponseSchema(BaseModel):
    """Supply represents the current supply of MicroAlgos in the system"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    current_round: int = Field(alias="current_round")
    online_money: int = Field(alias="online-money")
    total_money: int = Field(alias="total-money")
