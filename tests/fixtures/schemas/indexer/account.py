from pydantic import BaseModel, ConfigDict, Field


class AccountSchema(BaseModel):
    """Account information at a given round.

    Definition:
    data/basics/userBalance.go : AccountData
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    amount: int = Field(alias="amount")
    min_balance: int = Field(alias="min-balance")
    amount_without_pending_rewards: int = Field(alias="amount-without-pending-rewards")
    apps_local_state: "list[ApplicationLocalStateSchema] | None" = Field(default=None, alias="apps-local-state")
    apps_total_schema: "ApplicationStateSchemaSchema | None" = Field(default=None, alias="apps-total-schema")
    apps_total_extra_pages: int | None = Field(default=None, alias="apps-total-extra-pages")
    assets: "list[AssetHoldingSchema] | None" = Field(default=None, alias="assets")
    created_apps: "list[ApplicationSchema] | None" = Field(default=None, alias="created-apps")
    created_assets: "list[AssetSchema] | None" = Field(default=None, alias="created-assets")
    participation: "AccountParticipationSchema | None" = Field(default=None, alias="participation")
    incentive_eligible: bool | None = Field(default=None, alias="incentive-eligible")
    pending_rewards: int = Field(alias="pending-rewards")
    reward_base: int | None = Field(default=None, alias="reward-base")
    rewards: int = Field(alias="rewards")
    round_: int = Field(alias="round")
    status: str = Field(alias="status")
    sig_type: str | None = Field(default=None, alias="sig-type")
    total_apps_opted_in: int = Field(alias="total-apps-opted-in")
    total_assets_opted_in: int = Field(alias="total-assets-opted-in")
    total_box_bytes: int = Field(alias="total-box-bytes")
    total_boxes: int = Field(alias="total-boxes")
    total_created_apps: int = Field(alias="total-created-apps")
    total_created_assets: int = Field(alias="total-created-assets")
    auth_addr: str | None = Field(default=None, alias="auth-addr")
    last_proposed: int | None = Field(default=None, alias="last-proposed")
    last_heartbeat: int | None = Field(default=None, alias="last-heartbeat")
    deleted: bool | None = Field(default=None, alias="deleted")
    created_at_round: int | None = Field(default=None, alias="created-at-round")
    closed_at_round: int | None = Field(default=None, alias="closed-at-round")
