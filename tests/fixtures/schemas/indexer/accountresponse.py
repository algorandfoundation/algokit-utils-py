from pydantic import BaseModel, ConfigDict, Field


class AccountResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    account: "AccountSchema" = Field(alias="account")
    current_round: int = Field(alias="current-round")
