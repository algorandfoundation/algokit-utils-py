from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PendingTransactionResponseSchema(BaseModel):
    """Details about a pending transaction. If the transaction was recently confirmed, includes confirmation details like the round and reward details."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    asset_id: int | None = Field(default=None, alias="asset-index")
    app_id: int | None = Field(default=None, alias="application-index")
    close_rewards: int | None = Field(default=None, alias="close-rewards")
    closing_amount: int | None = Field(default=None, alias="closing-amount")
    asset_closing_amount: int | None = Field(default=None, alias="asset-closing-amount")
    confirmed_round: int | None = Field(default=None, alias="confirmed-round")
    pool_error: str = Field(alias="pool-error")
    receiver_rewards: int | None = Field(default=None, alias="receiver-rewards")
    sender_rewards: int | None = Field(default=None, alias="sender-rewards")
    local_state_delta: "list[AccountStateDeltaSchema] | None" = Field(default=None, alias="local-state-delta")
    global_state_delta: "StateDeltaSchema | None" = Field(default=None, alias="global-state-delta")
    logs: list[str] | None = Field(default=None, alias="logs")
    inner_txns: "list[PendingTransactionResponseSchema] | None" = Field(default=None, alias="inner-txns")
    txn: dict[str, Any] = Field(alias="txn")
