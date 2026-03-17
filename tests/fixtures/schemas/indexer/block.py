from pydantic import BaseModel, ConfigDict, Field


class BlockSchema(BaseModel):
    """Block information.

    Definition:
    data/bookkeeping/block.go : Block"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    proposer: str | None = Field(default=None, alias="proposer")
    fees_collected: int | None = Field(default=None, alias="fees-collected")
    bonus: int | None = Field(default=None, alias="bonus")
    proposer_payout: int | None = Field(default=None, alias="proposer-payout")
    genesis_hash: str = Field(alias="genesis-hash")
    genesis_id: str = Field(alias="genesis-id")
    previous_block_hash: str = Field(alias="previous-block-hash")
    previous_block_hash_512: str | None = Field(default=None, alias="previous-block-hash-512")
    rewards: "BlockRewardsSchema" = Field(alias="rewards")
    round_: int = Field(alias="round")
    seed: str = Field(alias="seed")
    state_proof_tracking: "list[StateProofTrackingSchema] | None" = Field(default=None, alias="state-proof-tracking")
    timestamp: int = Field(alias="timestamp")
    transactions: "list[TransactionSchema]" = Field(alias="transactions")
    transactions_root: str = Field(alias="transactions-root")
    transactions_root_sha256: str | None = Field(default=None, alias="transactions-root-sha256")
    transactions_root_sha512: str | None = Field(default=None, alias="transactions-root-sha512")
    txn_counter: int | None = Field(default=None, alias="txn-counter")
    upgrade_state: "BlockUpgradeStateSchema" = Field(alias="upgrade-state")
    upgrade_vote: "BlockUpgradeVoteSchema | None" = Field(default=None, alias="upgrade-vote")
    participation_updates: "ParticipationUpdatesSchema" = Field(alias="participation-updates")
