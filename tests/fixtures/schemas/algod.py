"""Generated Pydantic validation schemas from OpenAPI spec."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel


class AccountParticipationSchema(BaseModel):
    """AccountParticipation describes the parameters used by this account in consensus protocol."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    selection_participation_key: str = Field(alias="selection-participation-key")
    vote_first_valid: int = Field(alias="vote-first-valid")
    vote_key_dilution: int = Field(alias="vote-key-dilution")
    vote_last_valid: int = Field(alias="vote-last-valid")
    vote_participation_key: str = Field(alias="vote-participation-key")
    state_proof_key: str | None = Field(default=None, alias="state-proof-key")


class ApplicationStateSchemaSchema(BaseModel):
    """Specifies maximums on the number of each type that may be stored."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    num_uints: int = Field(ge=0, le=64, alias="num-uint")
    num_byte_slices: int = Field(ge=0, le=64, alias="num-byte-slice")


class TealValueSchema(BaseModel):
    """Represents a TEAL value."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    type_: int = Field(alias="type")
    bytes_: str = Field(alias="bytes")
    uint: int = Field(ge=0, le=18446744073709551615, alias="uint")


class TealKeyValueSchema(BaseModel):
    """Represents a key-value pair in an application store."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    key: str = Field(alias="key")
    value: TealValueSchema = Field(alias="value")


class TealKeyValueStoreSchema(RootModel[list[TealKeyValueSchema]]):
    """Represents a key-value store for use in an application."""


class ApplicationParamsSchema(BaseModel):
    """Stores the global information associated with an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    creator: str = Field(alias="creator")
    approval_program: str = Field(alias="approval-program")
    clear_state_program: str = Field(alias="clear-state-program")
    extra_program_pages: int | None = Field(default=None, ge=0, le=3, alias="extra-program-pages")
    local_state_schema: ApplicationStateSchemaSchema | None = Field(default=None, alias="local-state-schema")
    global_state_schema: ApplicationStateSchemaSchema | None = Field(default=None, alias="global-state-schema")
    global_state: TealKeyValueStoreSchema | None = Field(default=None, alias="global-state")
    version: int | None = Field(default=None, alias="version")


class ApplicationSchema(BaseModel):
    """Application index and its parameters"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id_: int = Field(alias="id")
    params: ApplicationParamsSchema = Field(alias="params")


class ApplicationLocalStateSchema(BaseModel):
    """Stores local state associated with an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id_: int = Field(alias="id")
    schema_: ApplicationStateSchemaSchema = Field(alias="schema")
    key_value: TealKeyValueStoreSchema | None = Field(default=None, alias="key-value")


class AssetParamsSchema(BaseModel):
    """AssetParams specifies the parameters for an asset.

    \\[apar\\] when part of an AssetConfig transaction.

    De..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    clawback: str | None = Field(default=None, alias="clawback")
    creator: str = Field(alias="creator")
    decimals: int = Field(ge=0, le=19, alias="decimals")
    default_frozen: bool | None = Field(default=None, alias="default-frozen")
    freeze: str | None = Field(default=None, alias="freeze")
    manager: str | None = Field(default=None, alias="manager")
    metadata_hash: str | None = Field(default=None, alias="metadata-hash")
    name: str | None = Field(default=None, alias="name")
    name_b64: str | None = Field(default=None, alias="name-b64")
    reserve: str | None = Field(default=None, alias="reserve")
    total: int = Field(ge=0, le=18446744073709551615, alias="total")
    unit_name: str | None = Field(default=None, alias="unit-name")
    unit_name_b64: str | None = Field(default=None, alias="unit-name-b64")
    url: str | None = Field(default=None, alias="url")
    url_b64: str | None = Field(default=None, alias="url-b64")


class AssetSchema(BaseModel):
    """Specifies both the unique identifier and the parameters for an asset"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id_: int = Field(alias="index")
    params: AssetParamsSchema = Field(alias="params")


class AssetHoldingSchema(BaseModel):
    """Describes an asset held by an account.

    Definition:
    data/basics/userBalance.go : AssetHolding"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    amount: int = Field(ge=0, le=18446744073709551615, alias="amount")
    asset_id: int = Field(alias="asset-id")
    is_frozen: bool = Field(alias="is-frozen")


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
    apps_local_state: list[ApplicationLocalStateSchema] | None = Field(default=None, alias="apps-local-state")
    total_apps_opted_in: int = Field(alias="total-apps-opted-in")
    apps_total_schema: ApplicationStateSchemaSchema | None = Field(default=None, alias="apps-total-schema")
    apps_total_extra_pages: int | None = Field(default=None, alias="apps-total-extra-pages")
    assets: list[AssetHoldingSchema] | None = Field(default=None, alias="assets")
    total_assets_opted_in: int = Field(alias="total-assets-opted-in")
    created_apps: list[ApplicationSchema] | None = Field(default=None, alias="created-apps")
    total_created_apps: int = Field(alias="total-created-apps")
    created_assets: list[AssetSchema] | None = Field(default=None, alias="created-assets")
    total_created_assets: int = Field(alias="total-created-assets")
    total_boxes: int | None = Field(default=None, alias="total-boxes")
    total_box_bytes: int | None = Field(default=None, alias="total-box-bytes")
    participation: AccountParticipationSchema | None = Field(default=None, alias="participation")
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


class AccountApplicationResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    round_: int = Field(alias="round")
    app_local_state: ApplicationLocalStateSchema | None = Field(default=None, alias="app-local-state")
    created_app: ApplicationParamsSchema | None = Field(default=None, alias="created-app")


class AccountAssetHoldingSchema(BaseModel):
    """AccountAssetHolding describes the account's asset holding and asset parameters (if either exist) for a spec..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    asset_holding: AssetHoldingSchema = Field(alias="asset-holding")
    asset_params: AssetParamsSchema | None = Field(default=None, alias="asset-params")


class AccountAssetResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    round_: int = Field(alias="round")
    asset_holding: AssetHoldingSchema | None = Field(default=None, alias="asset-holding")
    created_asset: AssetParamsSchema | None = Field(default=None, alias="created-asset")


class AccountAssetsInformationResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    round_: int = Field(alias="round")
    next_token: str | None = Field(default=None, alias="next-token")
    asset_holdings: list[AccountAssetHoldingSchema] | None = Field(default=None, alias="asset-holdings")


class EvalDeltaSchema(BaseModel):
    """Represents a TEAL value delta."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    action: int = Field(alias="action")
    bytes_: str | None = Field(default=None, alias="bytes")
    uint: int | None = Field(default=None, ge=0, le=18446744073709551615, alias="uint")


class EvalDeltaKeyValueSchema(BaseModel):
    """Key-value pairs for StateDelta."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    key: str = Field(alias="key")
    value: EvalDeltaSchema = Field(alias="value")


class StateDeltaSchema(RootModel[list[EvalDeltaKeyValueSchema]]):
    """Application state delta."""


class AccountStateDeltaSchema(BaseModel):
    """Application state delta."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    delta: StateDeltaSchema = Field(alias="delta")


class AppCallLogsSchema(BaseModel):
    """The logged messages from an app call along with the app ID and outer transaction ID. Logs appear in the sam..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    logs: list[str] = Field(alias="logs")
    app_id: int = Field(alias="application-index")
    tx_id: str = Field(alias="txId")


class AvmValueSchema(BaseModel):
    """Represents an AVM value."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    type_: int = Field(alias="type")
    bytes_: str | None = Field(default=None, alias="bytes")
    uint: int | None = Field(default=None, ge=0, le=18446744073709551615, alias="uint")


class AvmKeyValueSchema(BaseModel):
    """Represents an AVM key-value pair in an application store."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    key: str = Field(alias="key")
    value: AvmValueSchema = Field(alias="value")


class ApplicationKVStorageSchema(BaseModel):
    """An application's global/local/box state."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    kvs: list[AvmKeyValueSchema] = Field(alias="kvs")
    account: str | None = Field(default=None, alias="account")


class ApplicationInitialStatesSchema(BaseModel):
    """An application's initial global/local/box states that were accessed during simulation."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id_: int = Field(alias="id")
    app_locals: list[ApplicationKVStorageSchema] | None = Field(default=None, alias="app-locals")
    app_globals: ApplicationKVStorageSchema | None = Field(default=None, alias="app-globals")
    app_boxes: ApplicationKVStorageSchema | None = Field(default=None, alias="app-boxes")


class ApplicationLocalReferenceSchema(BaseModel):
    """References an account's local state for an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    account: str = Field(alias="account")
    app: int = Field(alias="app")


class ApplicationStateOperationSchema(BaseModel):
    """An operation against an application's global/local/box state."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    operation: str = Field(alias="operation")
    app_state_type: str = Field(alias="app-state-type")
    key: str = Field(alias="key")
    new_value: AvmValueSchema | None = Field(default=None, alias="new-value")
    account: str | None = Field(default=None, alias="account")


class AssetHoldingReferenceSchema(BaseModel):
    """References an asset held by an account."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    account: str = Field(alias="account")
    asset: int = Field(alias="asset")


class BlockHashResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    block_hash: str = Field(alias="blockHash")


class BlockLogsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    logs: list[AppCallLogsSchema] = Field(alias="logs")


class BlockResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    block: dict[str, Any] = Field(alias="block")
    cert: dict[str, Any] | None = Field(default=None, alias="cert")


class BlockTxidsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    block_tx_ids: list[str] = Field(alias="blockTxids")


class BoxSchema(BaseModel):
    """Box name and its content."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    round_: int = Field(alias="round")
    name: str = Field(alias="name")
    value: str = Field(alias="value")


class BoxDescriptorSchema(BaseModel):
    """Box descriptor describes a Box."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    name: str = Field(alias="name")


class BoxReferenceSchema(BaseModel):
    """References a box of an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    app: int = Field(alias="app")
    name: str = Field(alias="name")


class BoxesResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    boxes: list[BoxDescriptorSchema] = Field(alias="boxes")


class BuildVersionSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    branch: str = Field(alias="branch")
    build_number: int = Field(alias="build_number")
    channel: str = Field(alias="channel")
    commit_hash: str = Field(alias="commit_hash")
    major: int = Field(alias="major")
    minor: int = Field(alias="minor")


class CatchpointAbortResponseSchema(BaseModel):
    """An catchpoint abort response."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    catchup_message: str = Field(alias="catchup-message")


class CatchpointStartResponseSchema(BaseModel):
    """An catchpoint start response."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    catchup_message: str = Field(alias="catchup-message")


class SourceMapSchema(BaseModel):
    """Source map for the program"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    version: int = Field(alias="version")
    sources: list[str] = Field(alias="sources")
    names: list[str] = Field(alias="names")
    mappings: str = Field(alias="mappings")


class CompileResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    hash_: str = Field(alias="hash")
    result: str = Field(alias="result")
    sourcemap: SourceMapSchema | None = Field(default=None, alias="sourcemap")


class DebugSettingsProfSchema(BaseModel):
    """algod mutex and blocking profiling state."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    block_rate: int | None = Field(default=None, ge=0, le=18446744073709551615, alias="block-rate")
    mutex_rate: int | None = Field(default=None, ge=0, le=18446744073709551615, alias="mutex-rate")


class DisassembleResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    result: str = Field(alias="result")


class DryrunSourceSchema(BaseModel):
    """DryrunSource is TEAL source text that gets uploaded, compiled, and inserted into transactions or applicatio..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    field_name: str = Field(alias="field-name")
    source: str = Field(alias="source")
    txn_index: int = Field(alias="txn-index")
    app_id: int = Field(alias="app-index")


class DryrunRequestSchema(BaseModel):
    """Request data type for dryrun endpoint. Given the Transactions and simulated ledger state upload, run TEAL s..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txns: list[str] = Field(alias="txns")
    accounts: list[AccountSchema] = Field(alias="accounts")
    apps: list[ApplicationSchema] = Field(alias="apps")
    protocol_version: str = Field(alias="protocol-version")
    round_: int = Field(alias="round")
    latest_timestamp: int = Field(ge=0, alias="latest-timestamp")
    sources: list[DryrunSourceSchema] = Field(alias="sources")


class DryrunStateSchema(BaseModel):
    """Stores the TEAL eval step data"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    line: int = Field(alias="line")
    pc: int = Field(alias="pc")
    stack: list[TealValueSchema] = Field(alias="stack")
    scratch: list[TealValueSchema] | None = Field(default=None, alias="scratch")
    error: str | None = Field(default=None, alias="error")


class DryrunTxnResultSchema(BaseModel):
    """DryrunTxnResult contains any LogicSig or ApplicationCall program debug information and state updates from a..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    disassembly: list[str] = Field(alias="disassembly")
    logic_sig_disassembly: list[str] | None = Field(default=None, alias="logic-sig-disassembly")
    logic_sig_trace: list[DryrunStateSchema] | None = Field(default=None, alias="logic-sig-trace")
    logic_sig_messages: list[str] | None = Field(default=None, alias="logic-sig-messages")
    app_call_trace: list[DryrunStateSchema] | None = Field(default=None, alias="app-call-trace")
    app_call_messages: list[str] | None = Field(default=None, alias="app-call-messages")
    global_delta: StateDeltaSchema | None = Field(default=None, alias="global-delta")
    local_deltas: list[AccountStateDeltaSchema] | None = Field(default=None, alias="local-deltas")
    logs: list[str] | None = Field(default=None, alias="logs")
    budget_added: int | None = Field(default=None, alias="budget-added")
    budget_consumed: int | None = Field(default=None, alias="budget-consumed")


class DryrunResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txns: list[DryrunTxnResultSchema] = Field(alias="txns")
    error: str = Field(alias="error")
    protocol_version: str = Field(alias="protocol-version")


class ErrorResponseSchema(BaseModel):
    """An error response with optional data field."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    data: dict[str, Any] | None = Field(default=None, alias="data")
    message: str = Field(alias="message")


class GenesisAllocationSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    addr: str = Field(alias="addr")
    comment: str = Field(alias="comment")
    state: dict[str, Any] = Field(alias="state")


class GenesisSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    alloc: list[GenesisAllocationSchema] = Field(alias="alloc")
    comment: str | None = Field(default=None, alias="comment")
    devmode: bool | None = Field(default=None, alias="devmode")
    fees: str = Field(alias="fees")
    id_: str = Field(alias="id")
    network: str = Field(alias="network")
    proto: str = Field(alias="proto")
    rwd: str = Field(alias="rwd")
    timestamp: int | None = Field(default=None, alias="timestamp")


class GetBlockTimeStampOffsetResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    offset: int = Field(alias="offset")


class GetSyncRoundResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    round_: int = Field(alias="round")


class LedgerStateDeltaSchema(BaseModel):
    """Ledger StateDelta object"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, extra="allow")


class LedgerStateDeltaForTransactionGroupSchema(BaseModel):
    """Contains a ledger delta for a single transaction group"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    delta: LedgerStateDeltaSchema = Field(alias="Delta")
    ids: list[str] = Field(alias="Ids")


class LightBlockHeaderProofSchema(BaseModel):
    """Proof of membership and position of a light block header."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    index: int = Field(alias="index")
    treedepth: int = Field(alias="treedepth")
    proof: str = Field(alias="proof")


class NodeStatusResponseSchema(BaseModel):
    """NodeStatus contains the information about a node status"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    catchup_time: int = Field(alias="catchup-time")
    last_round: int = Field(alias="last-round")
    last_version: str = Field(alias="last-version")
    next_version: str = Field(alias="next-version")
    next_version_round: int = Field(alias="next-version-round")
    next_version_supported: bool = Field(alias="next-version-supported")
    stopped_at_unsupported_round: bool = Field(alias="stopped-at-unsupported-round")
    time_since_last_round: int = Field(alias="time-since-last-round")
    last_catchpoint: str | None = Field(default=None, alias="last-catchpoint")
    catchpoint: str | None = Field(default=None, alias="catchpoint")
    catchpoint_total_accounts: int | None = Field(default=None, alias="catchpoint-total-accounts")
    catchpoint_processed_accounts: int | None = Field(default=None, alias="catchpoint-processed-accounts")
    catchpoint_verified_accounts: int | None = Field(default=None, alias="catchpoint-verified-accounts")
    catchpoint_total_kvs: int | None = Field(default=None, alias="catchpoint-total-kvs")
    catchpoint_processed_kvs: int | None = Field(default=None, alias="catchpoint-processed-kvs")
    catchpoint_verified_kvs: int | None = Field(default=None, alias="catchpoint-verified-kvs")
    catchpoint_total_blocks: int | None = Field(default=None, alias="catchpoint-total-blocks")
    catchpoint_acquired_blocks: int | None = Field(default=None, alias="catchpoint-acquired-blocks")
    upgrade_delay: int | None = Field(default=None, alias="upgrade-delay")
    upgrade_node_vote: bool | None = Field(default=None, alias="upgrade-node-vote")
    upgrade_votes_required: int | None = Field(default=None, alias="upgrade-votes-required")
    upgrade_votes: int | None = Field(default=None, alias="upgrade-votes")
    upgrade_yes_votes: int | None = Field(default=None, alias="upgrade-yes-votes")
    upgrade_no_votes: int | None = Field(default=None, alias="upgrade-no-votes")
    upgrade_next_protocol_vote_before: int | None = Field(default=None, alias="upgrade-next-protocol-vote-before")
    upgrade_vote_rounds: int | None = Field(default=None, alias="upgrade-vote-rounds")


class ParticipationKeySchema(BaseModel):
    """Represents a participation key used by the node."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id_: str = Field(alias="id")
    address: str = Field(alias="address")
    effective_first_valid: int | None = Field(default=None, alias="effective-first-valid")
    effective_last_valid: int | None = Field(default=None, alias="effective-last-valid")
    last_vote: int | None = Field(default=None, alias="last-vote")
    last_block_proposal: int | None = Field(default=None, alias="last-block-proposal")
    last_state_proof: int | None = Field(default=None, alias="last-state-proof")
    key: AccountParticipationSchema = Field(alias="key")


class ParticipationKeysResponseSchema(RootModel[list[ParticipationKeySchema]]):
    pass


class PendingTransactionResponseSchema(BaseModel):
    """Details about a pending transaction. If the transaction was recently confirmed, includes confirmation detai..."""

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
    local_state_delta: list[AccountStateDeltaSchema] | None = Field(default=None, alias="local-state-delta")
    global_state_delta: StateDeltaSchema | None = Field(default=None, alias="global-state-delta")
    logs: list[str] | None = Field(default=None, alias="logs")
    inner_txns: list[PendingTransactionResponseSchema] | None = Field(default=None, alias="inner-txns")
    txn: dict[str, Any] = Field(alias="txn")


class PendingTransactionsResponseSchema(BaseModel):
    """PendingTransactions is an array of signed transactions exactly as they were submitted."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    top_transactions: list[dict[str, Any]] = Field(alias="top-transactions")
    total_transactions: int = Field(alias="total-transactions")


class PostParticipationResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    part_id: str = Field(alias="partId")


class PostTransactionsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    tx_id: str = Field(alias="txId")


class ScratchChangeSchema(BaseModel):
    """A write operation into a scratch slot."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    slot: int = Field(alias="slot")
    new_value: AvmValueSchema = Field(alias="new-value")


class SimulateInitialStatesSchema(BaseModel):
    """Initial states of resources that were accessed during simulation."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    app_initial_states: list[ApplicationInitialStatesSchema] | None = Field(default=None, alias="app-initial-states")


class SimulateRequestTransactionGroupSchema(BaseModel):
    """A transaction group to simulate."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txns: list[str] = Field(alias="txns")


class SimulateTraceConfigSchema(BaseModel):
    """An object that configures simulation execution trace."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    enable: bool | None = Field(default=None, alias="enable")
    stack_change: bool | None = Field(default=None, alias="stack-change")
    scratch_change: bool | None = Field(default=None, alias="scratch-change")
    state_change: bool | None = Field(default=None, alias="state-change")


class SimulateRequestSchema(BaseModel):
    """Request type for simulation endpoint."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txn_groups: list[SimulateRequestTransactionGroupSchema] = Field(alias="txn-groups")
    round_: int | None = Field(default=None, alias="round")
    allow_empty_signatures: bool | None = Field(default=None, alias="allow-empty-signatures")
    allow_more_logging: bool | None = Field(default=None, alias="allow-more-logging")
    allow_unnamed_resources: bool | None = Field(default=None, alias="allow-unnamed-resources")
    extra_opcode_budget: int | None = Field(default=None, alias="extra-opcode-budget")
    exec_trace_config: SimulateTraceConfigSchema | None = Field(default=None, alias="exec-trace-config")
    fix_signers: bool | None = Field(default=None, alias="fix-signers")


class SimulateUnnamedResourcesAccessedSchema(BaseModel):
    """These are resources that were accessed by this group that would normally have caused failure, but were allo..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    accounts: list[str] | None = Field(default=None, alias="accounts")
    assets: list[int] | None = Field(default=None, alias="assets")
    apps: list[int] | None = Field(default=None, alias="apps")
    boxes: list[BoxReferenceSchema] | None = Field(default=None, alias="boxes")
    extra_box_refs: int | None = Field(default=None, alias="extra-box-refs")
    asset_holdings: list[AssetHoldingReferenceSchema] | None = Field(default=None, alias="asset-holdings")
    app_locals: list[ApplicationLocalReferenceSchema] | None = Field(default=None, alias="app-locals")


class SimulationOpcodeTraceUnitSchema(BaseModel):
    """The set of trace information and effect from evaluating a single opcode."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    pc: int = Field(alias="pc")
    scratch_changes: list[ScratchChangeSchema] | None = Field(default=None, alias="scratch-changes")
    state_changes: list[ApplicationStateOperationSchema] | None = Field(default=None, alias="state-changes")
    spawned_inners: list[int] | None = Field(default=None, alias="spawned-inners")
    stack_pop_count: int | None = Field(default=None, alias="stack-pop-count")
    stack_additions: list[AvmValueSchema] | None = Field(default=None, alias="stack-additions")


class SimulationTransactionExecTraceSchema(BaseModel):
    """The execution trace of calling an app or a logic sig, containing the inner app call trace in a recursive wa..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    approval_program_trace: list[SimulationOpcodeTraceUnitSchema] | None = Field(
        default=None, alias="approval-program-trace"
    )
    approval_program_hash: str | None = Field(default=None, alias="approval-program-hash")
    clear_state_program_trace: list[SimulationOpcodeTraceUnitSchema] | None = Field(
        default=None, alias="clear-state-program-trace"
    )
    clear_state_program_hash: str | None = Field(default=None, alias="clear-state-program-hash")
    clear_state_rollback: bool | None = Field(default=None, alias="clear-state-rollback")
    clear_state_rollback_error: str | None = Field(default=None, alias="clear-state-rollback-error")
    logic_sig_trace: list[SimulationOpcodeTraceUnitSchema] | None = Field(default=None, alias="logic-sig-trace")
    logic_sig_hash: str | None = Field(default=None, alias="logic-sig-hash")
    inner_trace: list[SimulationTransactionExecTraceSchema] | None = Field(default=None, alias="inner-trace")


class SimulateTransactionResultSchema(BaseModel):
    """Simulation result for an individual transaction"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txn_result: PendingTransactionResponseSchema = Field(alias="txn-result")
    app_budget_consumed: int | None = Field(default=None, alias="app-budget-consumed")
    logic_sig_budget_consumed: int | None = Field(default=None, alias="logic-sig-budget-consumed")
    exec_trace: SimulationTransactionExecTraceSchema | None = Field(default=None, alias="exec-trace")
    unnamed_resources_accessed: SimulateUnnamedResourcesAccessedSchema | None = Field(
        default=None, alias="unnamed-resources-accessed"
    )
    fixed_signer: str | None = Field(default=None, alias="fixed-signer")


class SimulateTransactionGroupResultSchema(BaseModel):
    """Simulation result for an atomic transaction group"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txn_results: list[SimulateTransactionResultSchema] = Field(alias="txn-results")
    failure_message: str | None = Field(default=None, alias="failure-message")
    failed_at: list[int] | None = Field(default=None, alias="failed-at")
    app_budget_added: int | None = Field(default=None, alias="app-budget-added")
    app_budget_consumed: int | None = Field(default=None, alias="app-budget-consumed")
    unnamed_resources_accessed: SimulateUnnamedResourcesAccessedSchema | None = Field(
        default=None, alias="unnamed-resources-accessed"
    )


class SimulationEvalOverridesSchema(BaseModel):
    """The set of parameters and limits override during simulation. If this set of parameters is present, then eva..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    allow_empty_signatures: bool | None = Field(default=None, alias="allow-empty-signatures")
    allow_unnamed_resources: bool | None = Field(default=None, alias="allow-unnamed-resources")
    max_log_calls: int | None = Field(default=None, alias="max-log-calls")
    max_log_size: int | None = Field(default=None, alias="max-log-size")
    extra_opcode_budget: int | None = Field(default=None, alias="extra-opcode-budget")
    fix_signers: bool | None = Field(default=None, alias="fix-signers")


class SimulateResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    version: int = Field(alias="version")
    last_round: int = Field(alias="last-round")
    txn_groups: list[SimulateTransactionGroupResultSchema] = Field(alias="txn-groups")
    eval_overrides: SimulationEvalOverridesSchema | None = Field(default=None, alias="eval-overrides")
    exec_trace_config: SimulateTraceConfigSchema | None = Field(default=None, alias="exec-trace-config")
    initial_states: SimulateInitialStatesSchema | None = Field(default=None, alias="initial-states")


class StateProofMessageSchema(BaseModel):
    """Represents the message that the state proofs are attesting to."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    block_headers_commitment: str = Field(alias="BlockHeadersCommitment")
    voters_commitment: str = Field(alias="VotersCommitment")
    ln_proven_weight: int = Field(ge=0, le=18446744073709551615, alias="LnProvenWeight")
    first_attested_round: int = Field(alias="FirstAttestedRound")
    last_attested_round: int = Field(alias="LastAttestedRound")


class StateProofSchema(BaseModel):
    """Represents a state proof and its corresponding message"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    message: StateProofMessageSchema = Field(alias="Message")
    state_proof: str = Field(alias="StateProof")


class SupplyResponseSchema(BaseModel):
    """Supply represents the current supply of MicroAlgos in the system"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    current_round: int = Field(alias="current_round")
    online_money: int = Field(alias="online-money")
    total_money: int = Field(alias="total-money")


class TransactionGroupLedgerStateDeltasForRoundResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    deltas: list[LedgerStateDeltaForTransactionGroupSchema] = Field(alias="Deltas")


class TransactionParametersResponseSchema(BaseModel):
    """TransactionParams contains the parameters that help a client construct
    a new transaction."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    consensus_version: str = Field(alias="consensus-version")
    fee: int = Field(alias="fee")
    genesis_hash: str = Field(alias="genesis-hash")
    genesis_id: str = Field(alias="genesis-id")
    last_round: int = Field(alias="last-round")
    min_fee: int = Field(alias="min-fee")


class TransactionProofSchema(BaseModel):
    """Proof of transaction in a block."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    proof: str = Field(alias="proof")
    stibhash: str = Field(alias="stibhash")
    treedepth: int = Field(alias="treedepth")
    idx: int = Field(alias="idx")
    hashtype: str = Field(alias="hashtype")


class VersionSchema(BaseModel):
    """algod version information."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    build: BuildVersionSchema = Field(alias="build")
    genesis_hash_b64: str = Field(alias="genesis_hash_b64")
    genesis_id: str = Field(alias="genesis_id")
    versions: list[str] = Field(alias="versions")
