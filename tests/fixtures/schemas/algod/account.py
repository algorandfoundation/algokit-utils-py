from pydantic import BaseModel, ConfigDict, Field


class AccountSchema(BaseModel):
    """Account information at a given round.

    Definition:
    data/basics/userBalance.go : AccountData
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    amount: int = Field(ge=0, le=18446744073709551615, alias="amount")
    min_balance: int = Field(ge=0, le=18446744073709551615, alias="min-balance")
    amount_without_pending_rewards: int = Field(ge=0, le=18446744073709551615, alias="amount-without-pending-rewards")
    apps_local_state: "list[ApplicationLocalStateSchema] | None" = Field(default=None, alias="apps-local-state")
    total_apps_opted_in: int = Field(alias="total-apps-opted-in")
    apps_total_schema: "ApplicationStateSchemaSchema | None" = Field(default=None, alias="apps-total-schema")
    apps_total_extra_pages: int | None = Field(default=None, alias="apps-total-extra-pages")
    assets: "list[AssetHoldingSchema] | None" = Field(default=None, alias="assets")
    total_assets_opted_in: int = Field(alias="total-assets-opted-in")
    created_apps: "list[ApplicationSchema] | None" = Field(default=None, alias="created-apps")
    total_created_apps: int = Field(alias="total-created-apps")
    created_assets: "list[AssetSchema] | None" = Field(default=None, alias="created-assets")
    total_created_assets: int = Field(alias="total-created-assets")
    total_boxes: int | None = Field(default=None, alias="total-boxes")
    total_box_bytes: int | None = Field(default=None, alias="total-box-bytes")
    participation: "AccountParticipationSchema | None" = Field(default=None, alias="participation")
    incentive_eligible: bool | None = Field(default=None, alias="incentive-eligible")
    pending_rewards: int = Field(ge=0, le=18446744073709551615, alias="pending-rewards")
    reward_base: int | None = Field(default=None, ge=0, le=18446744073709551615, alias="reward-base")
    rewards: int = Field(ge=0, le=18446744073709551615, alias="rewards")
    round_: int = Field(alias="round")
    status: str = Field(alias="status")
    sig_type: str | None = Field(default=None, alias="sig-type")
    auth_addr: str | None = Field(default=None, alias="auth-addr")
    last_proposed: int | None = Field(default=None, alias="last-proposed")
    last_heartbeat: int | None = Field(default=None, alias="last-heartbeat")
