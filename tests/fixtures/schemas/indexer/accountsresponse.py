from pydantic import BaseModel, ConfigDict, Field


class AccountsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    accounts: "list[AccountSchema]" = Field(alias="accounts")
    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")
