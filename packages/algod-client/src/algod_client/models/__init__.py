from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire
from algokit_transact.models.signed_transaction import SignedTransaction

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .block import (
    Block,
    BlockAccountStateDelta,
    BlockAppEvalDelta,
    BlockEvalDelta,
    BlockStateDelta,
    BlockStateProofTracking,
    BlockStateProofTrackingData,
    GetBlock,
    SignedTxnInBlock,
)

__all__ = [
    "Account",
    "AccountAssetHolding",
    "AccountParticipation",
    "AccountStateDelta",
    "AlgodMutexAndBlockingProfilingState",
    "AllocationsForGenesisFile",
    "AppCallLogs",
    "Application",
    "ApplicationInitialStates",
    "ApplicationKvstorage",
    "ApplicationLocalReference",
    "ApplicationLocalState",
    "ApplicationParams",
    "ApplicationStateOperation",
    "ApplicationStateSchema",
    "Asset",
    "AssetHolding",
    "AssetHoldingReference",
    "AssetParams",
    "AvmKeyValue",
    "AvmValue",
    "Block",
    "BlockAccountStateDelta",
    "BlockAppEvalDelta",
    "BlockEvalDelta",
    "BlockStateDelta",
    "BlockStateProofTracking",
    "BlockStateProofTrackingData",
    "Box",
    "BoxDescriptor",
    "BoxReference",
    "BuildVersionContainsTheCurrentAlgodBuildVersionInformation",
    "DryrunRequest",
    "DryrunSource",
    "DryrunState",
    "DryrunTxnResult",
    "ErrorResponse",
    "EvalDelta",
    "EvalDeltaKeyValue",
    "GenesisFileInJson",
    "GetBlock",
    "Inline1AllocationsForGenesisFileStateModel",
    "LedgerStateDelta",
    "LedgerStateDeltaForTransactionGroup",
    "LightBlockHeaderProof",
    "ParticipationKey",
    "PendingTransactionResponse",
    "ScratchChange",
    "SignedTransaction",
    "SignedTxnInBlock",
    "SimulateInitialStates",
    "SimulateRequest",
    "SimulateRequestTransactionGroup",
    "SimulateTraceConfig",
    "SimulateTransactionGroupResult",
    "SimulateTransactionResult",
    "SimulateUnnamedResourcesAccessed",
    "SimulationEvalOverrides",
    "SimulationOpcodeTraceUnit",
    "SimulationTransactionExecTrace",
    "StateDelta",
    "StateProof",
    "StateProofMessage",
    "TealKeyValue",
    "TealKeyValueStore",
    "TealValue",
    "TransactionProof",
    "VersionContainsTheCurrentAlgodVersion",
]


@dataclass(slots=True)
class Account:
    """
    Account information at a given round.

    Definition:
    data/basics/userBalance.go : AccountData
    """

    address: str = field(
        metadata=wire("address"),
    )
    amount: int = field(
        metadata=wire("amount"),
    )
    amount_without_pending_rewards: int = field(
        metadata=wire("amount-without-pending-rewards"),
    )
    min_balance: int = field(
        metadata=wire("min-balance"),
    )
    pending_rewards: int = field(
        metadata=wire("pending-rewards"),
    )
    rewards: int = field(
        metadata=wire("rewards"),
    )
    round_: int = field(
        metadata=wire("round"),
    )
    status: str = field(
        metadata=wire("status"),
    )
    total_apps_opted_in: int = field(
        metadata=wire("total-apps-opted-in"),
    )
    total_assets_opted_in: int = field(
        metadata=wire("total-assets-opted-in"),
    )
    total_created_apps: int = field(
        metadata=wire("total-created-apps"),
    )
    total_created_assets: int = field(
        metadata=wire("total-created-assets"),
    )
    apps_local_state: list[ApplicationLocalState] = field(
        default=None,
        metadata=wire(
            "apps-local-state",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationLocalState, raw),
        ),
    )
    apps_total_extra_pages: int = field(
        default=None,
        metadata=wire("apps-total-extra-pages"),
    )
    apps_total_schema: ApplicationStateSchema = field(
        default=None,
        metadata=nested("apps-total-schema", lambda: ApplicationStateSchema),
    )
    assets: list[AssetHolding] = field(
        default=None,
        metadata=wire(
            "assets", encode=encode_model_sequence, decode=lambda raw: decode_model_sequence(lambda: AssetHolding, raw)
        ),
    )
    auth_addr: str = field(
        default=None,
        metadata=wire("auth-addr"),
    )
    created_apps: list[Application] = field(
        default=None,
        metadata=wire(
            "created-apps",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Application, raw),
        ),
    )
    created_assets: list[Asset] = field(
        default=None,
        metadata=wire(
            "created-assets", encode=encode_model_sequence, decode=lambda raw: decode_model_sequence(lambda: Asset, raw)
        ),
    )
    incentive_eligible: bool = field(
        default=None,
        metadata=wire("incentive-eligible"),
    )
    last_heartbeat: int = field(
        default=None,
        metadata=wire("last-heartbeat"),
    )
    last_proposed: int = field(
        default=None,
        metadata=wire("last-proposed"),
    )
    participation: AccountParticipation = field(
        default=None,
        metadata=nested("participation", lambda: AccountParticipation),
    )
    reward_base: int = field(
        default=None,
        metadata=wire("reward-base"),
    )
    sig_type: str = field(
        default=None,
        metadata=wire("sig-type"),
    )
    total_box_bytes: int = field(
        default=None,
        metadata=wire("total-box-bytes"),
    )
    total_boxes: int = field(
        default=None,
        metadata=wire("total-boxes"),
    )


@dataclass(slots=True)
class AccountAssetHolding:
    """
    AccountAssetHolding describes the account's asset holding and asset parameters (if
    either exist) for a specific asset ID.
    """

    asset_holding: AssetHolding = field(
        metadata=nested("asset-holding", lambda: AssetHolding),
    )
    asset_params: AssetParams = field(
        default=None,
        metadata=nested("asset-params", lambda: AssetParams),
    )


@dataclass(slots=True)
class AccountParticipation:
    """
    AccountParticipation describes the parameters used by this account in consensus
    protocol.
    """

    selection_participation_key: bytes = field(
        metadata=wire("selection-participation-key"),
    )
    vote_first_valid: int = field(
        metadata=wire("vote-first-valid"),
    )
    vote_key_dilution: int = field(
        metadata=wire("vote-key-dilution"),
    )
    vote_last_valid: int = field(
        metadata=wire("vote-last-valid"),
    )
    vote_participation_key: bytes = field(
        metadata=wire("vote-participation-key"),
    )
    state_proof_key: bytes = field(
        default=None,
        metadata=wire("state-proof-key"),
    )


@dataclass(slots=True)
class AccountStateDelta:
    """
    Application state delta.
    """

    address: str = field(
        metadata=wire("address"),
    )
    delta: list[EvalDeltaKeyValue] = field(
        metadata=wire(
            "delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: EvalDeltaKeyValue, raw),
        ),
    )


@dataclass(slots=True)
class AppCallLogs:
    """
    The logged messages from an app call along with the app ID and outer transaction ID.
    Logs appear in the same order that they were emitted.
    """

    app_id: int = field(
        metadata=wire("app_id"),
    )
    logs: list[bytes] = field(
        metadata=wire("logs"),
    )
    tx_id: str = field(
        metadata=wire("txId"),
    )


@dataclass(slots=True)
class Application:
    """
    Application index and its parameters
    """

    id_: int = field(
        metadata=wire("id"),
    )
    params: ApplicationParams = field(
        metadata=nested("params", lambda: ApplicationParams),
    )


@dataclass(slots=True)
class ApplicationInitialStates:
    """
    An application's initial global/local/box states that were accessed during simulation.
    """

    id_: int = field(
        metadata=wire("id"),
    )
    app_boxes: ApplicationKvstorage = field(
        default=None,
        metadata=nested("app-boxes", lambda: ApplicationKvstorage),
    )
    app_globals: ApplicationKvstorage = field(
        default=None,
        metadata=nested("app-globals", lambda: ApplicationKvstorage),
    )
    app_locals: list[ApplicationKvstorage] = field(
        default=None,
        metadata=wire(
            "app-locals",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationKvstorage, raw),
        ),
    )


@dataclass(slots=True)
class ApplicationKvstorage:
    """
    An application's global/local/box state.
    """

    kvs: list[AvmKeyValue] = field(
        metadata=wire(
            "kvs", encode=encode_model_sequence, decode=lambda raw: decode_model_sequence(lambda: AvmKeyValue, raw)
        ),
    )
    account: str = field(
        default=None,
        metadata=wire("account"),
    )


@dataclass(slots=True)
class ApplicationLocalReference:
    """
    References an account's local state for an application.
    """

    account: str = field(
        metadata=wire("account"),
    )
    app: int = field(
        metadata=wire("app"),
    )


@dataclass(slots=True)
class ApplicationLocalState:
    """
    Stores local state associated with an application.
    """

    id_: int = field(
        metadata=wire("id"),
    )
    schema: ApplicationStateSchema = field(
        metadata=nested("schema", lambda: ApplicationStateSchema),
    )
    key_value: list[TealKeyValue] = field(
        default=None,
        metadata=wire(
            "key-value",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: TealKeyValue, raw),
        ),
    )


@dataclass(slots=True)
class ApplicationParams:
    """
    Stores the global information associated with an application.
    """

    approval_program: bytes = field(
        metadata=wire("approval-program"),
    )
    clear_state_program: bytes = field(
        metadata=wire("clear-state-program"),
    )
    creator: str = field(
        metadata=wire("creator"),
    )
    extra_program_pages: int = field(
        default=None,
        metadata=wire("extra-program-pages"),
    )
    global_state: list[TealKeyValue] = field(
        default=None,
        metadata=wire(
            "global-state",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: TealKeyValue, raw),
        ),
    )
    global_state_schema: ApplicationStateSchema = field(
        default=None,
        metadata=nested("global-state-schema", lambda: ApplicationStateSchema),
    )
    local_state_schema: ApplicationStateSchema = field(
        default=None,
        metadata=nested("local-state-schema", lambda: ApplicationStateSchema),
    )
    version: int = field(
        default=None,
        metadata=wire("version"),
    )


@dataclass(slots=True)
class ApplicationStateOperation:
    """
    An operation against an application's global/local/box state.
    """

    app_state_type: str = field(
        metadata=wire("app-state-type"),
    )
    key: bytes = field(
        metadata=wire("key"),
    )
    operation: str = field(
        metadata=wire("operation"),
    )
    account: str = field(
        default=None,
        metadata=wire("account"),
    )
    new_value: AvmValue = field(
        default=None,
        metadata=nested("new-value", lambda: AvmValue),
    )


@dataclass(slots=True)
class ApplicationStateSchema:
    """
    Specifies maximums on the number of each type that may be stored.
    """

    num_byte_slice: int = field(
        metadata=wire("num-byte-slice"),
    )
    num_uint: int = field(
        metadata=wire("num-uint"),
    )


@dataclass(slots=True)
class Asset:
    """
    Specifies both the unique identifier and the parameters for an asset
    """

    index: int = field(
        metadata=wire("index"),
    )
    params: AssetParams = field(
        metadata=nested("params", lambda: AssetParams),
    )


@dataclass(slots=True)
class AssetHolding:
    """
    Describes an asset held by an account.

    Definition:
    data/basics/userBalance.go : AssetHolding
    """

    amount: int = field(
        metadata=wire("amount"),
    )
    asset_id: int = field(
        metadata=wire("asset-id"),
    )
    is_frozen: bool = field(
        metadata=wire("is-frozen"),
    )


@dataclass(slots=True)
class AssetHoldingReference:
    """
    References an asset held by an account.
    """

    account: str = field(
        metadata=wire("account"),
    )
    asset: int = field(
        metadata=wire("asset"),
    )


@dataclass(slots=True)
class AssetParams:
    r"""
    AssetParams specifies the parameters for an asset.

    \[apar\] when part of an AssetConfig transaction.

    Definition:
    data/transactions/asset.go : AssetParams
    """

    creator: str = field(
        metadata=wire("creator"),
    )
    decimals: int = field(
        metadata=wire("decimals"),
    )
    total: int = field(
        metadata=wire("total"),
    )
    clawback: str = field(
        default=None,
        metadata=wire("clawback"),
    )
    default_frozen: bool = field(
        default=None,
        metadata=wire("default-frozen"),
    )
    freeze: str = field(
        default=None,
        metadata=wire("freeze"),
    )
    manager: str = field(
        default=None,
        metadata=wire("manager"),
    )
    metadata_hash: bytes = field(
        default=None,
        metadata=wire("metadata-hash"),
    )
    name: str = field(
        default=None,
        metadata=wire("name"),
    )
    name_b64: bytes = field(
        default=None,
        metadata=wire("name-b64"),
    )
    reserve: str = field(
        default=None,
        metadata=wire("reserve"),
    )
    unit_name: str = field(
        default=None,
        metadata=wire("unit-name"),
    )
    unit_name_b64: bytes = field(
        default=None,
        metadata=wire("unit-name-b64"),
    )
    url: str = field(
        default=None,
        metadata=wire("url"),
    )
    url_b64: bytes = field(
        default=None,
        metadata=wire("url-b64"),
    )


@dataclass(slots=True)
class AvmKeyValue:
    """
    Represents an AVM key-value pair in an application store.
    """

    key: bytes = field(
        metadata=wire("key"),
    )
    value: AvmValue = field(
        metadata=nested("value", lambda: AvmValue),
    )


@dataclass(slots=True)
class AvmValue:
    """
    Represents an AVM value.
    """

    type_: int = field(
        metadata=wire("type"),
    )
    bytes: str = field(
        default=None,
        metadata=wire("bytes"),
    )
    uint: int = field(
        default=None,
        metadata=wire("uint"),
    )


@dataclass(slots=True)
class Box:
    """
    Box name and its content.
    """

    name: bytes = field(
        metadata=wire("name"),
    )
    round_: int = field(
        metadata=wire("round"),
    )
    value: bytes = field(
        metadata=wire("value"),
    )


@dataclass(slots=True)
class BoxDescriptor:
    """
    Box descriptor describes a Box.
    """

    name: bytes = field(
        metadata=wire("name"),
    )


@dataclass(slots=True)
class BoxReference:
    """
    References a box of an application.
    """

    app: int = field(
        metadata=wire("app"),
    )
    name: bytes = field(
        metadata=wire("name"),
    )


@dataclass(slots=True)
class BuildVersionContainsTheCurrentAlgodBuildVersionInformation:
    branch: str = field(
        metadata=wire("branch"),
    )
    build_number: int = field(
        metadata=wire("build_number"),
    )
    channel: str = field(
        metadata=wire("channel"),
    )
    commit_hash: str = field(
        metadata=wire("commit_hash"),
    )
    major: int = field(
        metadata=wire("major"),
    )
    minor: int = field(
        metadata=wire("minor"),
    )


@dataclass(slots=True)
class AlgodMutexAndBlockingProfilingState:
    """
    algod mutex and blocking profiling state.
    """

    block_rate: int = field(
        default=None,
        metadata=wire("block-rate"),
    )
    mutex_rate: int = field(
        default=None,
        metadata=wire("mutex-rate"),
    )


@dataclass(slots=True)
class DryrunRequest:
    """
    Request data type for dryrun endpoint. Given the Transactions and simulated ledger state
    upload, run TEAL scripts and return debugging information.
    """

    accounts: list[Account] = field(
        metadata=wire(
            "accounts", encode=encode_model_sequence, decode=lambda raw: decode_model_sequence(lambda: Account, raw)
        ),
    )
    apps: list[Application] = field(
        metadata=wire(
            "apps", encode=encode_model_sequence, decode=lambda raw: decode_model_sequence(lambda: Application, raw)
        ),
    )
    latest_timestamp: int = field(
        metadata=wire("latest-timestamp"),
    )
    protocol_version: str = field(
        metadata=wire("protocol-version"),
    )
    round_: int = field(
        metadata=wire("round"),
    )
    sources: list[DryrunSource] = field(
        metadata=wire(
            "sources", encode=encode_model_sequence, decode=lambda raw: decode_model_sequence(lambda: DryrunSource, raw)
        ),
    )
    txns: list[SignedTransaction] = field(
        metadata=wire(
            "txns",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SignedTransaction, raw),
        ),
    )


@dataclass(slots=True)
class DryrunSource:
    """
    DryrunSource is TEAL source text that gets uploaded, compiled, and inserted into
    transactions or application state.
    """

    app_index: int = field(
        metadata=wire("app-index"),
    )
    field_name: str = field(
        metadata=wire("field-name"),
    )
    source: str = field(
        metadata=wire("source"),
    )
    txn_index: int = field(
        metadata=wire("txn-index"),
    )


@dataclass(slots=True)
class DryrunState:
    """
    Stores the TEAL eval step data
    """

    line: int = field(
        metadata=wire("line"),
    )
    pc: int = field(
        metadata=wire("pc"),
    )
    stack: list[TealValue] = field(
        metadata=wire(
            "stack", encode=encode_model_sequence, decode=lambda raw: decode_model_sequence(lambda: TealValue, raw)
        ),
    )
    error: str = field(
        default=None,
        metadata=wire("error"),
    )
    scratch: list[TealValue] = field(
        default=None,
        metadata=wire(
            "scratch", encode=encode_model_sequence, decode=lambda raw: decode_model_sequence(lambda: TealValue, raw)
        ),
    )


@dataclass(slots=True)
class DryrunTxnResult:
    """
    DryrunTxnResult contains any LogicSig or ApplicationCall program debug information and
    state updates from a dryrun.
    """

    disassembly: list[str] = field(
        metadata=wire("disassembly"),
    )
    app_call_messages: list[str] = field(
        default=None,
        metadata=wire("app-call-messages"),
    )
    app_call_trace: list[DryrunState] = field(
        default=None,
        metadata=wire(
            "app-call-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: DryrunState, raw),
        ),
    )
    budget_added: int = field(
        default=None,
        metadata=wire("budget-added"),
    )
    budget_consumed: int = field(
        default=None,
        metadata=wire("budget-consumed"),
    )
    global_delta: list[EvalDeltaKeyValue] = field(
        default=None,
        metadata=wire(
            "global-delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: EvalDeltaKeyValue, raw),
        ),
    )
    local_deltas: list[AccountStateDelta] = field(
        default=None,
        metadata=wire(
            "local-deltas",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AccountStateDelta, raw),
        ),
    )
    logic_sig_disassembly: list[str] = field(
        default=None,
        metadata=wire("logic-sig-disassembly"),
    )
    logic_sig_messages: list[str] = field(
        default=None,
        metadata=wire("logic-sig-messages"),
    )
    logic_sig_trace: list[DryrunState] = field(
        default=None,
        metadata=wire(
            "logic-sig-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: DryrunState, raw),
        ),
    )
    logs: list[bytes] = field(
        default=None,
        metadata=wire("logs"),
    )


@dataclass(slots=True)
class ErrorResponse:
    """
    An error response with optional data field.
    """

    message: str = field(
        metadata=wire("message"),
    )
    data: dict[str, object] = field(
        default=None,
        metadata=wire("data"),
    )


@dataclass(slots=True)
class EvalDelta:
    """
    Represents a TEAL value delta.
    """

    action: int = field(
        metadata=wire("action"),
    )
    bytes: str = field(
        default=None,
        metadata=wire("bytes"),
    )
    uint: int = field(
        default=None,
        metadata=wire("uint"),
    )


@dataclass(slots=True)
class EvalDeltaKeyValue:
    """
    Key-value pairs for StateDelta.
    """

    key: str = field(
        metadata=wire("key"),
    )
    value: EvalDelta = field(
        metadata=nested("value", lambda: EvalDelta),
    )


@dataclass(slots=True)
class GenesisFileInJson:
    alloc: list[AllocationsForGenesisFile] = field(
        metadata=wire(
            "alloc",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AllocationsForGenesisFile, raw),
        ),
    )
    fees: str = field(
        metadata=wire("fees"),
    )
    id_: str = field(
        metadata=wire("id"),
    )
    network: str = field(
        metadata=wire("network"),
    )
    proto: str = field(
        metadata=wire("proto"),
    )
    rwd: str = field(
        metadata=wire("rwd"),
    )
    timestamp: int = field(
        metadata=wire("timestamp"),
    )
    comment: str = field(
        default=None,
        metadata=wire("comment"),
    )
    devmode: bool = field(
        default=None,
        metadata=wire("devmode"),
    )


@dataclass(slots=True)
class AllocationsForGenesisFile:
    addr: str = field(
        metadata=wire("addr"),
    )
    comment: str = field(
        metadata=wire("comment"),
    )
    state: Inline1AllocationsForGenesisFileStateModel = field(
        metadata=nested("state", lambda: Inline1AllocationsForGenesisFileStateModel),
    )


@dataclass(slots=True)
class LedgerStateDelta:
    """
    Ledger StateDelta object
    """


@dataclass(slots=True)
class LedgerStateDeltaForTransactionGroup:
    """
    Contains a ledger delta for a single transaction group
    """

    delta: LedgerStateDelta = field(
        metadata=nested("Delta", lambda: LedgerStateDelta),
    )
    ids: list[str] = field(
        metadata=wire("Ids"),
    )


@dataclass(slots=True)
class LightBlockHeaderProof:
    """
    Proof of membership and position of a light block header.
    """

    index: int = field(
        metadata=wire("index"),
    )
    proof: bytes = field(
        metadata=wire("proof"),
    )
    treedepth: int = field(
        metadata=wire("treedepth"),
    )


@dataclass(slots=True)
class ParticipationKey:
    """
    Represents a participation key used by the node.
    """

    address: str = field(
        metadata=wire("address"),
    )
    id_: str = field(
        metadata=wire("id"),
    )
    key: AccountParticipation = field(
        metadata=nested("key", lambda: AccountParticipation),
    )
    effective_first_valid: int = field(
        default=None,
        metadata=wire("effective-first-valid"),
    )
    effective_last_valid: int = field(
        default=None,
        metadata=wire("effective-last-valid"),
    )
    last_block_proposal: int = field(
        default=None,
        metadata=wire("last-block-proposal"),
    )
    last_state_proof: int = field(
        default=None,
        metadata=wire("last-state-proof"),
    )
    last_vote: int = field(
        default=None,
        metadata=wire("last-vote"),
    )


@dataclass(slots=True)
class PendingTransactionResponse:
    """
    Details about a pending transaction. If the transaction was recently confirmed, includes
    confirmation details like the round and reward details.
    """

    pool_error: str = field(
        metadata=wire("pool-error"),
    )
    txn: SignedTransaction = field(
        metadata=nested("txn", lambda: SignedTransaction),
    )
    app_id: int = field(
        default=None,
        metadata=wire("app_id"),
    )
    asset_closing_amount: int = field(
        default=None,
        metadata=wire("asset-closing-amount"),
    )
    asset_id: int = field(
        default=None,
        metadata=wire("asset_id"),
    )
    close_rewards: int = field(
        default=None,
        metadata=wire("close-rewards"),
    )
    closing_amount: int = field(
        default=None,
        metadata=wire("closing-amount"),
    )
    confirmed_round: int = field(
        default=None,
        metadata=wire("confirmed-round"),
    )
    global_state_delta: list[EvalDeltaKeyValue] = field(
        default=None,
        metadata=wire(
            "global-state-delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: EvalDeltaKeyValue, raw),
        ),
    )
    inner_txns: list[PendingTransactionResponse] = field(
        default=None,
        metadata=wire(
            "inner-txns",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: PendingTransactionResponse, raw),
        ),
    )
    local_state_delta: list[AccountStateDelta] = field(
        default=None,
        metadata=wire(
            "local-state-delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AccountStateDelta, raw),
        ),
    )
    logs: list[bytes] = field(
        default=None,
        metadata=wire("logs"),
    )
    receiver_rewards: int = field(
        default=None,
        metadata=wire("receiver-rewards"),
    )
    sender_rewards: int = field(
        default=None,
        metadata=wire("sender-rewards"),
    )


@dataclass(slots=True)
class ScratchChange:
    """
    A write operation into a scratch slot.
    """

    new_value: AvmValue = field(
        metadata=nested("new-value", lambda: AvmValue),
    )
    slot: int = field(
        metadata=wire("slot"),
    )


@dataclass(slots=True)
class SimulateInitialStates:
    """
    Initial states of resources that were accessed during simulation.
    """

    app_initial_states: list[ApplicationInitialStates] = field(
        default=None,
        metadata=wire(
            "app-initial-states",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationInitialStates, raw),
        ),
    )


@dataclass(slots=True)
class SimulateRequest:
    """
    Request type for simulation endpoint.
    """

    txn_groups: list[SimulateRequestTransactionGroup] = field(
        metadata=wire(
            "txn-groups",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulateRequestTransactionGroup, raw),
        ),
    )
    allow_empty_signatures: bool = field(
        default=None,
        metadata=wire("allow-empty-signatures"),
    )
    allow_more_logging: bool = field(
        default=None,
        metadata=wire("allow-more-logging"),
    )
    allow_unnamed_resources: bool = field(
        default=None,
        metadata=wire("allow-unnamed-resources"),
    )
    exec_trace_config: SimulateTraceConfig = field(
        default=None,
        metadata=nested("exec-trace-config", lambda: SimulateTraceConfig),
    )
    extra_opcode_budget: int = field(
        default=None,
        metadata=wire("extra-opcode-budget"),
    )
    fix_signers: bool = field(
        default=None,
        metadata=wire("fix-signers"),
    )
    round_: int = field(
        default=None,
        metadata=wire("round"),
    )


@dataclass(slots=True)
class SimulateRequestTransactionGroup:
    """
    A transaction group to simulate.
    """

    txns: list[SignedTransaction] = field(
        metadata=wire(
            "txns",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SignedTransaction, raw),
        ),
    )


@dataclass(slots=True)
class SimulateTraceConfig:
    """
    An object that configures simulation execution trace.
    """

    enable: bool = field(
        default=None,
        metadata=wire("enable"),
    )
    scratch_change: bool = field(
        default=None,
        metadata=wire("scratch-change"),
    )
    stack_change: bool = field(
        default=None,
        metadata=wire("stack-change"),
    )
    state_change: bool = field(
        default=None,
        metadata=wire("state-change"),
    )


@dataclass(slots=True)
class SimulateTransactionGroupResult:
    """
    Simulation result for an atomic transaction group
    """

    txn_results: list[SimulateTransactionResult] = field(
        metadata=wire(
            "txn-results",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulateTransactionResult, raw),
        ),
    )
    app_budget_added: int = field(
        default=None,
        metadata=wire("app-budget-added"),
    )
    app_budget_consumed: int = field(
        default=None,
        metadata=wire("app-budget-consumed"),
    )
    failed_at: list[int] = field(
        default=None,
        metadata=wire("failed-at"),
    )
    failure_message: str = field(
        default=None,
        metadata=wire("failure-message"),
    )
    unnamed_resources_accessed: SimulateUnnamedResourcesAccessed = field(
        default=None,
        metadata=nested("unnamed-resources-accessed", lambda: SimulateUnnamedResourcesAccessed),
    )


@dataclass(slots=True)
class SimulateTransactionResult:
    """
    Simulation result for an individual transaction
    """

    txn_result: PendingTransactionResponse = field(
        metadata=nested("txn-result", lambda: PendingTransactionResponse),
    )
    app_budget_consumed: int = field(
        default=None,
        metadata=wire("app-budget-consumed"),
    )
    exec_trace: SimulationTransactionExecTrace = field(
        default=None,
        metadata=nested("exec-trace", lambda: SimulationTransactionExecTrace),
    )
    fixed_signer: str = field(
        default=None,
        metadata=wire("fixed-signer"),
    )
    logic_sig_budget_consumed: int = field(
        default=None,
        metadata=wire("logic-sig-budget-consumed"),
    )
    unnamed_resources_accessed: SimulateUnnamedResourcesAccessed = field(
        default=None,
        metadata=nested("unnamed-resources-accessed", lambda: SimulateUnnamedResourcesAccessed),
    )


@dataclass(slots=True)
class SimulateUnnamedResourcesAccessed:
    """
    These are resources that were accessed by this group that would normally have caused
    failure, but were allowed in simulation. Depending on where this object is in the
    response, the unnamed resources it contains may or may not qualify for group resource
    sharing. If this is a field in SimulateTransactionGroupResult, the resources do qualify,
    but if this is a field in SimulateTransactionResult, they do not qualify. In order to
    make this group valid for actual submission, resources that qualify for group sharing
    can be made available by any transaction of the group; otherwise, resources must be
    placed in the same transaction which accessed them.
    """

    accounts: list[str] = field(
        default=None,
        metadata=wire("accounts"),
    )
    app_locals: list[ApplicationLocalReference] = field(
        default=None,
        metadata=wire(
            "app-locals",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationLocalReference, raw),
        ),
    )
    apps: list[int] = field(
        default=None,
        metadata=wire("apps"),
    )
    asset_holdings: list[AssetHoldingReference] = field(
        default=None,
        metadata=wire(
            "asset-holdings",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AssetHoldingReference, raw),
        ),
    )
    assets: list[int] = field(
        default=None,
        metadata=wire("assets"),
    )
    boxes: list[BoxReference] = field(
        default=None,
        metadata=wire(
            "boxes", encode=encode_model_sequence, decode=lambda raw: decode_model_sequence(lambda: BoxReference, raw)
        ),
    )
    extra_box_refs: int = field(
        default=None,
        metadata=wire("extra-box-refs"),
    )


@dataclass(slots=True)
class SimulationEvalOverrides:
    """
    The set of parameters and limits override during simulation. If this set of parameters
    is present, then evaluation parameters may differ from standard evaluation in certain
    ways.
    """

    allow_empty_signatures: bool = field(
        default=None,
        metadata=wire("allow-empty-signatures"),
    )
    allow_unnamed_resources: bool = field(
        default=None,
        metadata=wire("allow-unnamed-resources"),
    )
    extra_opcode_budget: int = field(
        default=None,
        metadata=wire("extra-opcode-budget"),
    )
    fix_signers: bool = field(
        default=None,
        metadata=wire("fix-signers"),
    )
    max_log_calls: int = field(
        default=None,
        metadata=wire("max-log-calls"),
    )
    max_log_size: int = field(
        default=None,
        metadata=wire("max-log-size"),
    )


@dataclass(slots=True)
class SimulationOpcodeTraceUnit:
    """
    The set of trace information and effect from evaluating a single opcode.
    """

    pc: int = field(
        metadata=wire("pc"),
    )
    scratch_changes: list[ScratchChange] = field(
        default=None,
        metadata=wire(
            "scratch-changes",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ScratchChange, raw),
        ),
    )
    spawned_inners: list[int] = field(
        default=None,
        metadata=wire("spawned-inners"),
    )
    stack_additions: list[AvmValue] = field(
        default=None,
        metadata=wire(
            "stack-additions",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AvmValue, raw),
        ),
    )
    stack_pop_count: int = field(
        default=None,
        metadata=wire("stack-pop-count"),
    )
    state_changes: list[ApplicationStateOperation] = field(
        default=None,
        metadata=wire(
            "state-changes",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationStateOperation, raw),
        ),
    )


@dataclass(slots=True)
class SimulationTransactionExecTrace:
    """
    The execution trace of calling an app or a logic sig, containing the inner app call
    trace in a recursive way.
    """

    approval_program_hash: bytes = field(
        default=None,
        metadata=wire("approval-program-hash"),
    )
    approval_program_trace: list[SimulationOpcodeTraceUnit] = field(
        default=None,
        metadata=wire(
            "approval-program-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulationOpcodeTraceUnit, raw),
        ),
    )
    clear_state_program_hash: bytes = field(
        default=None,
        metadata=wire("clear-state-program-hash"),
    )
    clear_state_program_trace: list[SimulationOpcodeTraceUnit] = field(
        default=None,
        metadata=wire(
            "clear-state-program-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulationOpcodeTraceUnit, raw),
        ),
    )
    clear_state_rollback: bool = field(
        default=None,
        metadata=wire("clear-state-rollback"),
    )
    clear_state_rollback_error: str = field(
        default=None,
        metadata=wire("clear-state-rollback-error"),
    )
    inner_trace: list[SimulationTransactionExecTrace] = field(
        default=None,
        metadata=wire(
            "inner-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulationTransactionExecTrace, raw),
        ),
    )
    logic_sig_hash: bytes = field(
        default=None,
        metadata=wire("logic-sig-hash"),
    )
    logic_sig_trace: list[SimulationOpcodeTraceUnit] = field(
        default=None,
        metadata=wire(
            "logic-sig-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulationOpcodeTraceUnit, raw),
        ),
    )


@dataclass(slots=True)
class StateProof:
    """
    Represents a state proof and its corresponding message
    """

    message: StateProofMessage = field(
        metadata=nested("Message", lambda: StateProofMessage),
    )
    state_proof: bytes = field(
        metadata=wire("StateProof"),
    )


@dataclass(slots=True)
class StateProofMessage:
    """
    Represents the message that the state proofs are attesting to.
    """

    block_headers_commitment: bytes = field(
        metadata=wire("BlockHeadersCommitment"),
    )
    first_attested_round: int = field(
        metadata=wire("FirstAttestedRound"),
    )
    last_attested_round: int = field(
        metadata=wire("LastAttestedRound"),
    )
    ln_proven_weight: int = field(
        metadata=wire("LnProvenWeight"),
    )
    voters_commitment: bytes = field(
        metadata=wire("VotersCommitment"),
    )


@dataclass(slots=True)
class TealKeyValue:
    """
    Represents a key-value pair in an application store.
    """

    key: str = field(
        metadata=wire("key"),
    )
    value: TealValue = field(
        metadata=nested("value", lambda: TealValue),
    )


@dataclass(slots=True)
class TealValue:
    """
    Represents a TEAL value.
    """

    bytes: bytes = field(
        metadata=wire("bytes"),
    )
    type_: int = field(
        metadata=wire("type"),
    )
    uint: int = field(
        metadata=wire("uint"),
    )


@dataclass(slots=True)
class TransactionProof:
    """
    Proof of transaction in a block.
    """

    hashtype: str = field(
        metadata=wire("hashtype"),
    )
    idx: int = field(
        metadata=wire("idx"),
    )
    proof: bytes = field(
        metadata=wire("proof"),
    )
    stibhash: bytes = field(
        metadata=wire("stibhash"),
    )
    treedepth: int = field(
        metadata=wire("treedepth"),
    )


@dataclass(slots=True)
class VersionContainsTheCurrentAlgodVersion:
    """
    algod version information.
    """

    build: BuildVersionContainsTheCurrentAlgodBuildVersionInformation = field(
        metadata=nested("build", lambda: BuildVersionContainsTheCurrentAlgodBuildVersionInformation),
    )
    genesis_hash_b64: bytes = field(
        metadata=wire("genesis_hash_b64"),
    )
    genesis_id: str = field(
        metadata=wire("genesis_id"),
    )
    versions: list[str] = field(
        metadata=wire("versions"),
    )


@dataclass(slots=True)
class Inline1AllocationsForGenesisFileStateModel:
    algo: int = field(
        metadata=wire("algo"),
    )
    onl: int = field(
        metadata=wire("onl"),
    )
    sel: str = field(
        default=None,
        metadata=wire("sel"),
    )
    stprf: str = field(
        default=None,
        metadata=wire("stprf"),
    )
    vote: str = field(
        default=None,
        metadata=wire("vote"),
    )
    vote_fst: int = field(
        default=None,
        metadata=wire("voteFst"),
    )
    vote_kd: int = field(
        default=None,
        metadata=wire("voteKD"),
    )
    vote_lst: int = field(
        default=None,
        metadata=wire("voteLst"),
    )


StateDelta = list[EvalDeltaKeyValue]
TealKeyValueStore = list[TealKeyValue]
