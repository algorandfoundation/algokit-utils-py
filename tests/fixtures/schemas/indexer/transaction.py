from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class TransactionSchema(BaseModel):
    """Contains all fields common to all transactions and serves as an envelope to all transactions type. Represents both regular and inner transactions.

    Definition:
    data/transactions/signedtxn.go : SignedTxn
    data/transactions/transaction.go : Transaction
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    application_transaction: "TransactionApplicationSchema | None" = Field(
        default=None, alias="application-transaction"
    )
    asset_config_transaction: "TransactionAssetConfigSchema | None" = Field(
        default=None, alias="asset-config-transaction"
    )
    asset_freeze_transaction: "TransactionAssetFreezeSchema | None" = Field(
        default=None, alias="asset-freeze-transaction"
    )
    asset_transfer_transaction: "TransactionAssetTransferSchema | None" = Field(
        default=None, alias="asset-transfer-transaction"
    )
    state_proof_transaction: "TransactionStateProofSchema | None" = Field(default=None, alias="state-proof-transaction")
    heartbeat_transaction: "TransactionHeartbeatSchema | None" = Field(default=None, alias="heartbeat-transaction")
    auth_addr: str | None = Field(default=None, alias="auth-addr")
    close_rewards: int | None = Field(default=None, alias="close-rewards")
    closing_amount: int | None = Field(default=None, alias="closing-amount")
    confirmed_round: int | None = Field(default=None, alias="confirmed-round")
    created_application_index: int | None = Field(default=None, alias="created-application-index")
    created_asset_index: int | None = Field(default=None, alias="created-asset-index")
    fee: int = Field(default=None, alias="fee")
    first_valid: int = Field(default=None, alias="first-valid")
    genesis_hash: str | None = Field(default=None, alias="genesis-hash")
    genesis_id: str | None = Field(default=None, alias="genesis-id")
    group: str | None = Field(default=None, alias="group")
    id: str | None = Field(default=None, alias="id")
    intra_round_offset: int | None = Field(default=None, alias="intra-round-offset")
    keyreg_transaction: "TransactionKeyregSchema | None" = Field(default=None, alias="keyreg-transaction")
    last_valid: int = Field(default=None, alias="last-valid")
    lease: str | None = Field(default=None, alias="lease")
    note: str | None = Field(default=None, alias="note")
    payment_transaction: "TransactionPaymentSchema | None" = Field(default=None, alias="payment-transaction")
    receiver_rewards: int | None = Field(default=None, alias="receiver-rewards")
    rekey_to: str | None = Field(default=None, alias="rekey-to")
    round_time: int | None = Field(default=None, alias="round-time")
    sender: str = Field(default=None, alias="sender")
    sender_rewards: int | None = Field(default=None, alias="sender-rewards")
    signature: "TransactionSignatureSchema | None" = Field(default=None, alias="signature")
    tx_type: str = Field(default=None, alias="tx-type")
    local_state_delta: "list[AccountStateDeltaSchema] | None" = Field(default=None, alias="local-state-delta")
    global_state_delta: "StateDeltaSchema | None" = Field(default=None, alias="global-state-delta")
    logs: list[str] | None = Field(default=None, alias="logs")
    inner_txns: "list[TransactionSchema] | None" = Field(default=None, alias="inner-txns")
