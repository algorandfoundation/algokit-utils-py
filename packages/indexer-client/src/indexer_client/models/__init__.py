from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from algokit_common.serde import enum_value, nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence

__all__ = [
    "Account",
    "AccountParticipation",
    "AccountStateDelta",
    "Application",
    "ApplicationLocalState",
    "ApplicationLogData",
    "ApplicationParams",
    "ApplicationStateSchema",
    "Asset",
    "AssetHolding",
    "AssetParams",
    "Block",
    "BlockRewards",
    "BlockUpgradeState",
    "BlockUpgradeVote",
    "Box",
    "BoxDescriptor",
    "BoxReference",
    "EvalDelta",
    "EvalDeltaKeyValue",
    "HashFactory",
    "Hashtype",
    "HbProofFields",
    "HealthCheck",
    "HoldingRef",
    "IndexerStateProofMessage",
    "LocalsRef",
    "MerkleArrayProof",
    "MiniAssetHolding",
    "OnCompletion",
    "ParticipationUpdates",
    "ResourceRef",
    "StateDelta",
    "StateProofFields",
    "StateProofParticipant",
    "StateProofReveal",
    "StateProofSigSlot",
    "StateProofSignature",
    "StateProofTracking",
    "StateProofVerifier",
    "StateSchema",
    "TealKeyValue",
    "TealKeyValueStore",
    "TealValue",
    "Transaction",
    "TransactionApplication",
    "TransactionAssetConfig",
    "TransactionAssetFreeze",
    "TransactionAssetTransfer",
    "TransactionHeartbeat",
    "TransactionKeyreg",
    "TransactionPayment",
    "TransactionSignature",
    "TransactionSignatureLogicsig",
    "TransactionSignatureMultisig",
    "TransactionSignatureMultisigSubsignature",
    "TransactionStateProof",
]


class Hashtype(Enum):
    """
    The type of hash function used to create the proof, must be one of:
    * sha512_256
    * sha256
    """

    SHA512_256 = "sha512_256"
    SHA256 = "sha256"


class OnCompletion(Enum):
    r"""
    \[apan\] defines the what additional actions occur with the transaction.

    Valid types:
    * noop
    * optin
    * closeout
    * clear
    * update
    * delete
    """

    NOOP = "noop"
    OPTIN = "optin"
    CLOSEOUT = "closeout"
    CLEAR = "clear"
    UPDATE = "update"
    DELETE = "delete"


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
    total_box_bytes: int = field(
        metadata=wire("total-box-bytes"),
    )
    total_boxes: int = field(
        metadata=wire("total-boxes"),
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
    closed_at_round: int = field(
        default=None,
        metadata=wire("closed-at-round"),
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
    created_at_round: int = field(
        default=None,
        metadata=wire("created-at-round"),
    )
    deleted: bool = field(
        default=None,
        metadata=wire("deleted"),
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
    created_at_round: int = field(
        default=None,
        metadata=wire("created-at-round"),
    )
    deleted: bool = field(
        default=None,
        metadata=wire("deleted"),
    )
    deleted_at_round: int = field(
        default=None,
        metadata=wire("deleted-at-round"),
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
    closed_out_at_round: int = field(
        default=None,
        metadata=wire("closed-out-at-round"),
    )
    deleted: bool = field(
        default=None,
        metadata=wire("deleted"),
    )
    key_value: list[TealKeyValue] = field(
        default=None,
        metadata=wire(
            "key-value",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: TealKeyValue, raw),
        ),
    )
    opted_in_at_round: int = field(
        default=None,
        metadata=wire("opted-in-at-round"),
    )


@dataclass(slots=True)
class ApplicationLogData:
    """
    Stores the global information associated with an application.
    """

    logs: list[bytes] = field(
        metadata=wire("logs"),
    )
    txid: str = field(
        metadata=wire("txid"),
    )


@dataclass(slots=True)
class ApplicationParams:
    """
    Stores the global information associated with an application.
    """

    approval_program: bytes = field(
        default=None,
        metadata=wire("approval-program"),
    )
    clear_state_program: bytes = field(
        default=None,
        metadata=wire("clear-state-program"),
    )
    creator: str = field(
        default=None,
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
    created_at_round: int = field(
        default=None,
        metadata=wire("created-at-round"),
    )
    deleted: bool = field(
        default=None,
        metadata=wire("deleted"),
    )
    destroyed_at_round: int = field(
        default=None,
        metadata=wire("destroyed-at-round"),
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
    deleted: bool = field(
        default=None,
        metadata=wire("deleted"),
    )
    opted_in_at_round: int = field(
        default=None,
        metadata=wire("opted-in-at-round"),
    )
    opted_out_at_round: int = field(
        default=None,
        metadata=wire("opted-out-at-round"),
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
class Block:
    """
    Block information.

    Definition:
    data/bookkeeping/block.go : Block
    """

    genesis_hash: bytes = field(
        metadata=wire("genesis-hash"),
    )
    genesis_id: str = field(
        metadata=wire("genesis-id"),
    )
    previous_block_hash: bytes = field(
        metadata=wire("previous-block-hash"),
    )
    round_: int = field(
        metadata=wire("round"),
    )
    seed: bytes = field(
        metadata=wire("seed"),
    )
    timestamp: int = field(
        metadata=wire("timestamp"),
    )
    transactions_root: bytes = field(
        metadata=wire("transactions-root"),
    )
    transactions_root_sha256: bytes = field(
        metadata=wire("transactions-root-sha256"),
    )
    bonus: int = field(
        default=None,
        metadata=wire("bonus"),
    )
    fees_collected: int = field(
        default=None,
        metadata=wire("fees-collected"),
    )
    participation_updates: ParticipationUpdates = field(
        default=None,
        metadata=nested("participation-updates", lambda: ParticipationUpdates),
    )
    previous_block_hash_512: bytes = field(
        default=None,
        metadata=wire("previous-block-hash-512"),
    )
    proposer: str = field(
        default=None,
        metadata=wire("proposer"),
    )
    proposer_payout: int = field(
        default=None,
        metadata=wire("proposer-payout"),
    )
    rewards: BlockRewards = field(
        default=None,
        metadata=nested("rewards", lambda: BlockRewards),
    )
    state_proof_tracking: list[StateProofTracking] = field(
        default=None,
        metadata=wire(
            "state-proof-tracking",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: StateProofTracking, raw),
        ),
    )
    transactions: list[Transaction] = field(
        default=None,
        metadata=wire(
            "transactions",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Transaction, raw),
        ),
    )
    transactions_root_sha512: bytes = field(
        default=None,
        metadata=wire("transactions-root-sha512"),
    )
    txn_counter: int = field(
        default=None,
        metadata=wire("txn-counter"),
    )
    upgrade_state: BlockUpgradeState = field(
        default=None,
        metadata=nested("upgrade-state", lambda: BlockUpgradeState),
    )
    upgrade_vote: BlockUpgradeVote = field(
        default=None,
        metadata=nested("upgrade-vote", lambda: BlockUpgradeVote),
    )


@dataclass(slots=True)
class BlockRewards:
    """
    Fields relating to rewards,
    """

    fee_sink: str = field(
        metadata=wire("fee-sink"),
    )
    rewards_calculation_round: int = field(
        metadata=wire("rewards-calculation-round"),
    )
    rewards_level: int = field(
        metadata=wire("rewards-level"),
    )
    rewards_pool: str = field(
        metadata=wire("rewards-pool"),
    )
    rewards_rate: int = field(
        metadata=wire("rewards-rate"),
    )
    rewards_residue: int = field(
        metadata=wire("rewards-residue"),
    )


@dataclass(slots=True)
class BlockUpgradeState:
    """
    Fields relating to a protocol upgrade.
    """

    current_protocol: str = field(
        metadata=wire("current-protocol"),
    )
    next_protocol: str = field(
        default=None,
        metadata=wire("next-protocol"),
    )
    next_protocol_approvals: int = field(
        default=None,
        metadata=wire("next-protocol-approvals"),
    )
    next_protocol_switch_on: int = field(
        default=None,
        metadata=wire("next-protocol-switch-on"),
    )
    next_protocol_vote_before: int = field(
        default=None,
        metadata=wire("next-protocol-vote-before"),
    )


@dataclass(slots=True)
class BlockUpgradeVote:
    """
    Fields relating to voting for a protocol upgrade.
    """

    upgrade_approve: bool = field(
        default=None,
        metadata=wire("upgrade-approve"),
    )
    upgrade_delay: int = field(
        default=None,
        metadata=wire("upgrade-delay"),
    )
    upgrade_propose: str = field(
        default=None,
        metadata=wire("upgrade-propose"),
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
    Box descriptor describes an app box without a value.
    """

    name: bytes = field(
        metadata=wire("name"),
    )


@dataclass(slots=True)
class BoxReference:
    """
    BoxReference names a box by its name and the application ID it belongs to.
    """

    app: int = field(
        metadata=wire("app"),
    )
    name: bytes = field(
        metadata=wire("name"),
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
class HashFactory:
    hash_type: int = field(
        default=None,
        metadata=wire("hash-type"),
    )


@dataclass(slots=True)
class HbProofFields:
    r"""
    \[hbprf\] HbProof is a signature using HeartbeatAddress's partkey, thereby showing it is
    online.
    """

    hb_pk: bytes = field(
        default=None,
        metadata=wire("hb-pk"),
    )
    hb_pk1sig: bytes = field(
        default=None,
        metadata=wire("hb-pk1sig"),
    )
    hb_pk2: bytes = field(
        default=None,
        metadata=wire("hb-pk2"),
    )
    hb_pk2sig: bytes = field(
        default=None,
        metadata=wire("hb-pk2sig"),
    )
    hb_sig: bytes = field(
        default=None,
        metadata=wire("hb-sig"),
    )


@dataclass(slots=True)
class HealthCheck:
    """
    A health check response.
    """

    db_available: bool = field(
        metadata=wire("db-available"),
    )
    is_migrating: bool = field(
        metadata=wire("is-migrating"),
    )
    message: str = field(
        metadata=wire("message"),
    )
    round_: int = field(
        metadata=wire("round"),
    )
    version: str = field(
        metadata=wire("version"),
    )
    data: dict[str, object] = field(
        default=None,
        metadata=wire("data"),
    )
    errors: list[str] = field(
        default=None,
        metadata=wire("errors"),
    )


@dataclass(slots=True)
class HoldingRef:
    """
    HoldingRef names a holding by referring to an Address and Asset it belongs to.
    """

    address: str = field(
        metadata=wire("address"),
    )
    asset: int = field(
        metadata=wire("asset"),
    )


@dataclass(slots=True)
class IndexerStateProofMessage:
    block_headers_commitment: bytes = field(
        default=None,
        metadata=wire("block-headers-commitment"),
    )
    first_attested_round: int = field(
        default=None,
        metadata=wire("first-attested-round"),
    )
    latest_attested_round: int = field(
        default=None,
        metadata=wire("latest-attested-round"),
    )
    ln_proven_weight: int = field(
        default=None,
        metadata=wire("ln-proven-weight"),
    )
    voters_commitment: bytes = field(
        default=None,
        metadata=wire("voters-commitment"),
    )


@dataclass(slots=True)
class LocalsRef:
    """
    LocalsRef names a local state by referring to an Address and App it belongs to.
    """

    address: str = field(
        metadata=wire("address"),
    )
    app: int = field(
        metadata=wire("app"),
    )


@dataclass(slots=True)
class MerkleArrayProof:
    hash_factory: HashFactory = field(
        default=None,
        metadata=nested("hash-factory", lambda: HashFactory),
    )
    path: list[bytes] = field(
        default=None,
        metadata=wire("path"),
    )
    tree_depth: int = field(
        default=None,
        metadata=wire("tree-depth"),
    )


@dataclass(slots=True)
class MiniAssetHolding:
    """
    A simplified version of AssetHolding
    """

    address: str = field(
        metadata=wire("address"),
    )
    amount: int = field(
        metadata=wire("amount"),
    )
    is_frozen: bool = field(
        metadata=wire("is-frozen"),
    )
    deleted: bool = field(
        default=None,
        metadata=wire("deleted"),
    )
    opted_in_at_round: int = field(
        default=None,
        metadata=wire("opted-in-at-round"),
    )
    opted_out_at_round: int = field(
        default=None,
        metadata=wire("opted-out-at-round"),
    )


@dataclass(slots=True)
class ParticipationUpdates:
    """
    Participation account data that needs to be checked/acted on by the network.
    """

    absent_participation_accounts: list[str] = field(
        default=None,
        metadata=wire("absent-participation-accounts"),
    )
    expired_participation_accounts: list[str] = field(
        default=None,
        metadata=wire("expired-participation-accounts"),
    )


@dataclass(slots=True)
class ResourceRef:
    """
    ResourceRef names a single resource. Only one of the fields should be set.
    """

    address: str = field(
        default=None,
        metadata=wire("address"),
    )
    application_id: int = field(
        default=None,
        metadata=wire("application-id"),
    )
    asset_id: int = field(
        default=None,
        metadata=wire("asset-id"),
    )
    box: BoxReference = field(
        default=None,
        metadata=nested("box", lambda: BoxReference),
    )
    holding: HoldingRef = field(
        default=None,
        metadata=nested("holding", lambda: HoldingRef),
    )
    local: LocalsRef = field(
        default=None,
        metadata=nested("local", lambda: LocalsRef),
    )


@dataclass(slots=True)
class StateProofFields:
    r"""
    \[sp\] represents a state proof.

    Definition:
    crypto/stateproof/structs.go : StateProof
    """

    part_proofs: MerkleArrayProof = field(
        default=None,
        metadata=nested("part-proofs", lambda: MerkleArrayProof),
    )
    positions_to_reveal: list[int] = field(
        default=None,
        metadata=wire("positions-to-reveal"),
    )
    reveals: list[StateProofReveal] = field(
        default=None,
        metadata=wire(
            "reveals",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: StateProofReveal, raw),
        ),
    )
    salt_version: int = field(
        default=None,
        metadata=wire("salt-version"),
    )
    sig_commit: bytes = field(
        default=None,
        metadata=wire("sig-commit"),
    )
    sig_proofs: MerkleArrayProof = field(
        default=None,
        metadata=nested("sig-proofs", lambda: MerkleArrayProof),
    )
    signed_weight: int = field(
        default=None,
        metadata=wire("signed-weight"),
    )


@dataclass(slots=True)
class StateProofParticipant:
    verifier: StateProofVerifier = field(
        default=None,
        metadata=nested("verifier", lambda: StateProofVerifier),
    )
    weight: int = field(
        default=None,
        metadata=wire("weight"),
    )


@dataclass(slots=True)
class StateProofReveal:
    participant: StateProofParticipant = field(
        default=None,
        metadata=nested("participant", lambda: StateProofParticipant),
    )
    position: int = field(
        default=None,
        metadata=wire("position"),
    )
    sig_slot: StateProofSigSlot = field(
        default=None,
        metadata=nested("sig-slot", lambda: StateProofSigSlot),
    )


@dataclass(slots=True)
class StateProofSigSlot:
    lower_sig_weight: int = field(
        default=None,
        metadata=wire("lower-sig-weight"),
    )
    signature: StateProofSignature = field(
        default=None,
        metadata=nested("signature", lambda: StateProofSignature),
    )


@dataclass(slots=True)
class StateProofSignature:
    falcon_signature: bytes = field(
        default=None,
        metadata=wire("falcon-signature"),
    )
    merkle_array_index: int = field(
        default=None,
        metadata=wire("merkle-array-index"),
    )
    proof: MerkleArrayProof = field(
        default=None,
        metadata=nested("proof", lambda: MerkleArrayProof),
    )
    verifying_key: bytes = field(
        default=None,
        metadata=wire("verifying-key"),
    )


@dataclass(slots=True)
class StateProofTracking:
    next_round: int = field(
        default=None,
        metadata=wire("next-round"),
    )
    online_total_weight: int = field(
        default=None,
        metadata=wire("online-total-weight"),
    )
    type_: int = field(
        default=None,
        metadata=wire("type"),
    )
    voters_commitment: bytes = field(
        default=None,
        metadata=wire("voters-commitment"),
    )


@dataclass(slots=True)
class StateProofVerifier:
    commitment: bytes = field(
        default=None,
        metadata=wire("commitment"),
    )
    key_lifetime: int = field(
        default=None,
        metadata=wire("key-lifetime"),
    )


@dataclass(slots=True)
class StateSchema:
    r"""
    Represents a \[apls\] local-state or \[apgs\] global-state schema. These schemas
    determine how much storage may be used in a local-state or global-state for an
    application. The more space used, the larger minimum balance must be maintained in the
    account holding the data.
    """

    num_byte_slice: int = field(
        metadata=wire("num-byte-slice"),
    )
    num_uint: int = field(
        metadata=wire("num-uint"),
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
class Transaction:
    """
    Contains all fields common to all transactions and serves as an envelope to all
    transactions type. Represents both regular and inner transactions.

    Definition:
    data/transactions/signedtxn.go : SignedTxn
    data/transactions/transaction.go : Transaction
    """

    fee: int = field(
        metadata=wire("fee"),
    )
    first_valid: int = field(
        metadata=wire("first-valid"),
    )
    last_valid: int = field(
        metadata=wire("last-valid"),
    )
    sender: str = field(
        metadata=wire("sender"),
    )
    tx_type: str = field(
        metadata=wire("tx-type"),
    )
    application_transaction: TransactionApplication = field(
        default=None,
        metadata=nested("application-transaction", lambda: TransactionApplication),
    )
    asset_config_transaction: TransactionAssetConfig = field(
        default=None,
        metadata=nested("asset-config-transaction", lambda: TransactionAssetConfig),
    )
    asset_freeze_transaction: TransactionAssetFreeze = field(
        default=None,
        metadata=nested("asset-freeze-transaction", lambda: TransactionAssetFreeze),
    )
    asset_transfer_transaction: TransactionAssetTransfer = field(
        default=None,
        metadata=nested("asset-transfer-transaction", lambda: TransactionAssetTransfer),
    )
    auth_addr: str = field(
        default=None,
        metadata=wire("auth-addr"),
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
    created_application_index: int = field(
        default=None,
        metadata=wire("created-application-index"),
    )
    created_asset_index: int = field(
        default=None,
        metadata=wire("created-asset-index"),
    )
    genesis_hash: bytes = field(
        default=None,
        metadata=wire("genesis-hash"),
    )
    genesis_id: str = field(
        default=None,
        metadata=wire("genesis-id"),
    )
    global_state_delta: list[EvalDeltaKeyValue] = field(
        default=None,
        metadata=wire(
            "global-state-delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: EvalDeltaKeyValue, raw),
        ),
    )
    group: bytes = field(
        default=None,
        metadata=wire("group"),
    )
    heartbeat_transaction: TransactionHeartbeat = field(
        default=None,
        metadata=nested("heartbeat-transaction", lambda: TransactionHeartbeat),
    )
    id_: str = field(
        default=None,
        metadata=wire("id"),
    )
    inner_txns: list[Transaction] = field(
        default=None,
        metadata=wire(
            "inner-txns",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Transaction, raw),
        ),
    )
    intra_round_offset: int = field(
        default=None,
        metadata=wire("intra-round-offset"),
    )
    keyreg_transaction: TransactionKeyreg = field(
        default=None,
        metadata=nested("keyreg-transaction", lambda: TransactionKeyreg),
    )
    lease: bytes = field(
        default=None,
        metadata=wire("lease"),
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
    note: bytes = field(
        default=None,
        metadata=wire("note"),
    )
    payment_transaction: TransactionPayment = field(
        default=None,
        metadata=nested("payment-transaction", lambda: TransactionPayment),
    )
    receiver_rewards: int = field(
        default=None,
        metadata=wire("receiver-rewards"),
    )
    rekey_to: str = field(
        default=None,
        metadata=wire("rekey-to"),
    )
    round_time: int = field(
        default=None,
        metadata=wire("round-time"),
    )
    sender_rewards: int = field(
        default=None,
        metadata=wire("sender-rewards"),
    )
    signature: TransactionSignature = field(
        default=None,
        metadata=nested("signature", lambda: TransactionSignature),
    )
    state_proof_transaction: TransactionStateProof = field(
        default=None,
        metadata=nested("state-proof-transaction", lambda: TransactionStateProof),
    )


@dataclass(slots=True)
class TransactionApplication:
    """
    Fields for application transactions.

    Definition:
    data/transactions/application.go : ApplicationCallTxnFields
    """

    application_id: int = field(
        metadata=wire("application-id"),
    )
    on_completion: OnCompletion = field(
        metadata=enum_value("on-completion", OnCompletion),
    )
    access: list[ResourceRef] = field(
        default=None,
        metadata=wire(
            "access", encode=encode_model_sequence, decode=lambda raw: decode_model_sequence(lambda: ResourceRef, raw)
        ),
    )
    accounts: list[str] = field(
        default=None,
        metadata=wire("accounts"),
    )
    application_args: list[str] = field(
        default=None,
        metadata=wire("application-args"),
    )
    approval_program: bytes = field(
        default=None,
        metadata=wire("approval-program"),
    )
    box_references: list[BoxReference] = field(
        default=None,
        metadata=wire(
            "box-references",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: BoxReference, raw),
        ),
    )
    clear_state_program: bytes = field(
        default=None,
        metadata=wire("clear-state-program"),
    )
    extra_program_pages: int = field(
        default=None,
        metadata=wire("extra-program-pages"),
    )
    foreign_apps: list[int] = field(
        default=None,
        metadata=wire("foreign-apps"),
    )
    foreign_assets: list[int] = field(
        default=None,
        metadata=wire("foreign-assets"),
    )
    global_state_schema: StateSchema = field(
        default=None,
        metadata=nested("global-state-schema", lambda: StateSchema),
    )
    local_state_schema: StateSchema = field(
        default=None,
        metadata=nested("local-state-schema", lambda: StateSchema),
    )
    reject_version: int = field(
        default=None,
        metadata=wire("reject-version"),
    )


@dataclass(slots=True)
class TransactionAssetConfig:
    """
    Fields for asset allocation, re-configuration, and destruction.


    A zero value for asset-id indicates asset creation.
    A zero value for the params indicates asset destruction.

    Definition:
    data/transactions/asset.go : AssetConfigTxnFields
    """

    asset_id: int = field(
        default=None,
        metadata=wire("asset-id"),
    )
    params: AssetParams = field(
        default=None,
        metadata=nested("params", lambda: AssetParams),
    )


@dataclass(slots=True)
class TransactionAssetFreeze:
    """
    Fields for an asset freeze transaction.

    Definition:
    data/transactions/asset.go : AssetFreezeTxnFields
    """

    address: str = field(
        metadata=wire("address"),
    )
    asset_id: int = field(
        metadata=wire("asset-id"),
    )
    new_freeze_status: bool = field(
        metadata=wire("new-freeze-status"),
    )


@dataclass(slots=True)
class TransactionAssetTransfer:
    """
    Fields for an asset transfer transaction.

    Definition:
    data/transactions/asset.go : AssetTransferTxnFields
    """

    amount: int = field(
        metadata=wire("amount"),
    )
    asset_id: int = field(
        metadata=wire("asset-id"),
    )
    receiver: str = field(
        metadata=wire("receiver"),
    )
    close_amount: int = field(
        default=None,
        metadata=wire("close-amount"),
    )
    close_to: str = field(
        default=None,
        metadata=wire("close-to"),
    )
    sender: str = field(
        default=None,
        metadata=wire("sender"),
    )


@dataclass(slots=True)
class TransactionHeartbeat:
    """
    Fields for a heartbeat transaction.

    Definition:
    data/transactions/heartbeat.go : HeartbeatTxnFields
    """

    hb_address: str = field(
        metadata=wire("hb-address"),
    )
    hb_key_dilution: int = field(
        metadata=wire("hb-key-dilution"),
    )
    hb_proof: HbProofFields = field(
        metadata=nested("hb-proof", lambda: HbProofFields),
    )
    hb_seed: bytes = field(
        metadata=wire("hb-seed"),
    )
    hb_vote_id: bytes = field(
        metadata=wire("hb-vote-id"),
    )


@dataclass(slots=True)
class TransactionKeyreg:
    """
    Fields for a keyreg transaction.

    Definition:
    data/transactions/keyreg.go : KeyregTxnFields
    """

    non_participation: bool = field(
        default=None,
        metadata=wire("non-participation"),
    )
    selection_participation_key: bytes = field(
        default=None,
        metadata=wire("selection-participation-key"),
    )
    state_proof_key: bytes = field(
        default=None,
        metadata=wire("state-proof-key"),
    )
    vote_first_valid: int = field(
        default=None,
        metadata=wire("vote-first-valid"),
    )
    vote_key_dilution: int = field(
        default=None,
        metadata=wire("vote-key-dilution"),
    )
    vote_last_valid: int = field(
        default=None,
        metadata=wire("vote-last-valid"),
    )
    vote_participation_key: bytes = field(
        default=None,
        metadata=wire("vote-participation-key"),
    )


@dataclass(slots=True)
class TransactionPayment:
    """
    Fields for a payment transaction.

    Definition:
    data/transactions/payment.go : PaymentTxnFields
    """

    amount: int = field(
        metadata=wire("amount"),
    )
    receiver: str = field(
        metadata=wire("receiver"),
    )
    close_amount: int = field(
        default=None,
        metadata=wire("close-amount"),
    )
    close_remainder_to: str = field(
        default=None,
        metadata=wire("close-remainder-to"),
    )


@dataclass(slots=True)
class TransactionSignature:
    """
    Validation signature associated with some data. Only one of the signatures should be
    provided.
    """

    logicsig: TransactionSignatureLogicsig = field(
        default=None,
        metadata=nested("logicsig", lambda: TransactionSignatureLogicsig),
    )
    multisig: TransactionSignatureMultisig = field(
        default=None,
        metadata=nested("multisig", lambda: TransactionSignatureMultisig),
    )
    sig: bytes = field(
        default=None,
        metadata=wire("sig"),
    )


@dataclass(slots=True)
class TransactionSignatureLogicsig:
    r"""
    \[lsig\] Programatic transaction signature.

    Definition:
    data/transactions/logicsig.go
    """

    logic: bytes = field(
        metadata=wire("logic"),
    )
    args: list[str] = field(
        default=None,
        metadata=wire("args"),
    )
    logic_multisig_signature: TransactionSignatureMultisig = field(
        default=None,
        metadata=nested("logic-multisig-signature", lambda: TransactionSignatureMultisig),
    )
    multisig_signature: TransactionSignatureMultisig = field(
        default=None,
        metadata=nested("multisig-signature", lambda: TransactionSignatureMultisig),
    )
    signature: bytes = field(
        default=None,
        metadata=wire("signature"),
    )


@dataclass(slots=True)
class TransactionSignatureMultisig:
    """
    structure holding multiple subsignatures.

    Definition:
    crypto/multisig.go : MultisigSig
    """

    subsignature: list[TransactionSignatureMultisigSubsignature] = field(
        default=None,
        metadata=wire(
            "subsignature",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: TransactionSignatureMultisigSubsignature, raw),
        ),
    )
    threshold: int = field(
        default=None,
        metadata=wire("threshold"),
    )
    version: int = field(
        default=None,
        metadata=wire("version"),
    )


@dataclass(slots=True)
class TransactionSignatureMultisigSubsignature:
    public_key: bytes = field(
        default=None,
        metadata=wire("public-key"),
    )
    signature: bytes = field(
        default=None,
        metadata=wire("signature"),
    )


@dataclass(slots=True)
class TransactionStateProof:
    """
    Fields for a state proof transaction.

    Definition:
    data/transactions/stateproof.go : StateProofTxnFields
    """

    message: IndexerStateProofMessage = field(
        default=None,
        metadata=nested("message", lambda: IndexerStateProofMessage),
    )
    state_proof: StateProofFields = field(
        default=None,
        metadata=nested("state-proof", lambda: StateProofFields),
    )
    state_proof_type: int = field(
        default=None,
        metadata=wire("state-proof-type"),
    )


StateDelta = list[EvalDeltaKeyValue]
TealKeyValueStore = list[TealKeyValue]
