from pydantic import BaseModel, ConfigDict, Field


class ParticipationUpdatesSchema(BaseModel):
    """Participation account data that needs to be checked/acted on by the network."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    expired_participation_accounts: list[str] = Field(default=None, alias="expired-participation-accounts")
    absent_participation_accounts: list[str] = Field(default=None, alias="absent-participation-accounts")
