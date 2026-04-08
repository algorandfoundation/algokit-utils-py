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
    uint: int = Field(alias="uint")


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

    creator: str | None = Field(default=None, alias="creator")
    approval_program: str | None = Field(default=None, alias="approval-program")
    clear_state_program: str | None = Field(default=None, alias="clear-state-program")
    extra_program_pages: int | None = Field(default=None, ge=0, le=3, alias="extra-program-pages")
    local_state_schema: ApplicationStateSchemaSchema | None = Field(default=None, alias="local-state-schema")
    global_state_schema: ApplicationStateSchemaSchema | None = Field(default=None, alias="global-state-schema")
    global_state: TealKeyValueStoreSchema | None = Field(default=None, alias="global-state")
    version: int | None = Field(default=None, alias="version")


class ApplicationSchema(BaseModel):
    """Application index and its parameters"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id_: int = Field(alias="id")
    deleted: bool | None = Field(default=None, alias="deleted")
    created_at_round: int | None = Field(default=None, alias="created-at-round")
    deleted_at_round: int | None = Field(default=None, alias="deleted-at-round")
    params: ApplicationParamsSchema = Field(alias="params")


class ApplicationLocalStateSchema(BaseModel):
    """Stores local state associated with an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id_: int = Field(alias="id")
    deleted: bool | None = Field(default=None, alias="deleted")
    opted_in_at_round: int | None = Field(default=None, alias="opted-in-at-round")
    closed_out_at_round: int | None = Field(default=None, alias="closed-out-at-round")
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
    total: int = Field(alias="total")
    unit_name: str | None = Field(default=None, alias="unit-name")
    unit_name_b64: str | None = Field(default=None, alias="unit-name-b64")
    url: str | None = Field(default=None, alias="url")
    url_b64: str | None = Field(default=None, alias="url-b64")


class AssetSchema(BaseModel):
    """Specifies both the unique identifier and the parameters for an asset"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id_: int = Field(alias="index")
    deleted: bool | None = Field(default=None, alias="deleted")
    created_at_round: int | None = Field(default=None, alias="created-at-round")
    destroyed_at_round: int | None = Field(default=None, alias="destroyed-at-round")
    params: AssetParamsSchema = Field(alias="params")


class AssetHoldingSchema(BaseModel):
    """Describes an asset held by an account.

    Definition:
    data/basics/userBalance.go : AssetHolding"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    amount: int = Field(alias="amount")
    asset_id: int = Field(alias="asset-id")
    is_frozen: bool = Field(alias="is-frozen")
    deleted: bool | None = Field(default=None, alias="deleted")
    opted_in_at_round: int | None = Field(default=None, alias="opted-in-at-round")
    opted_out_at_round: int | None = Field(default=None, alias="opted-out-at-round")


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
    apps_local_state: list[ApplicationLocalStateSchema] | None = Field(default=None, alias="apps-local-state")
    apps_total_schema: ApplicationStateSchemaSchema | None = Field(default=None, alias="apps-total-schema")
    apps_total_extra_pages: int | None = Field(default=None, alias="apps-total-extra-pages")
    assets: list[AssetHoldingSchema] | None = Field(default=None, alias="assets")
    created_apps: list[ApplicationSchema] | None = Field(default=None, alias="created-apps")
    created_assets: list[AssetSchema] | None = Field(default=None, alias="created-assets")
    participation: AccountParticipationSchema | None = Field(default=None, alias="participation")
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


class AccountResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    account: AccountSchema = Field(alias="account")
    current_round: int = Field(alias="current-round")


class EvalDeltaSchema(BaseModel):
    """Represents a TEAL value delta."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    action: int = Field(alias="action")
    bytes_: str | None = Field(default=None, alias="bytes")
    uint: int | None = Field(default=None, alias="uint")


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


class AccountsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    accounts: list[AccountSchema] = Field(alias="accounts")
    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")


class ApplicationLocalStatesResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    apps_local_states: list[ApplicationLocalStateSchema] = Field(alias="apps-local-states")
    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")


class ApplicationLogDataSchema(BaseModel):
    """Stores the global information associated with an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    tx_id: str = Field(alias="txid")
    logs: list[str] = Field(alias="logs")


class ApplicationLogsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    application_id: int = Field(alias="application-id")
    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")
    log_data: list[ApplicationLogDataSchema] | None = Field(default=None, alias="log-data")


class ApplicationResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    application: ApplicationSchema | None = Field(default=None, alias="application")
    current_round: int = Field(alias="current-round")


class ApplicationsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    applications: list[ApplicationSchema] = Field(alias="applications")
    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")


class MiniAssetHoldingSchema(BaseModel):
    """A simplified version of AssetHolding"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    amount: int = Field(alias="amount")
    is_frozen: bool = Field(alias="is-frozen")
    deleted: bool | None = Field(default=None, alias="deleted")
    opted_in_at_round: int | None = Field(default=None, alias="opted-in-at-round")
    opted_out_at_round: int | None = Field(default=None, alias="opted-out-at-round")


class AssetBalancesResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    balances: list[MiniAssetHoldingSchema] = Field(alias="balances")
    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")


class AssetHoldingsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")
    assets: list[AssetHoldingSchema] = Field(alias="assets")


class AssetResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    asset: AssetSchema = Field(alias="asset")
    current_round: int = Field(alias="current-round")


class AssetsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    assets: list[AssetSchema] = Field(alias="assets")
    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")


class BlockRewardsSchema(BaseModel):
    """Fields relating to rewards,"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    fee_sink: str = Field(alias="fee-sink")
    rewards_calculation_round: int = Field(alias="rewards-calculation-round")
    rewards_level: int = Field(alias="rewards-level")
    rewards_pool: str = Field(alias="rewards-pool")
    rewards_rate: int = Field(alias="rewards-rate")
    rewards_residue: int = Field(alias="rewards-residue")


class BlockUpgradeStateSchema(BaseModel):
    """Fields relating to a protocol upgrade."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    current_protocol: str = Field(alias="current-protocol")
    next_protocol: str | None = Field(default=None, alias="next-protocol")
    next_protocol_approvals: int | None = Field(default=None, alias="next-protocol-approvals")
    next_protocol_switch_on: int | None = Field(default=None, alias="next-protocol-switch-on")
    next_protocol_vote_before: int | None = Field(default=None, alias="next-protocol-vote-before")


class BlockUpgradeVoteSchema(BaseModel):
    """Fields relating to voting for a protocol upgrade."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    upgrade_approve: bool | None = Field(default=None, alias="upgrade-approve")
    upgrade_delay: int | None = Field(default=None, alias="upgrade-delay")
    upgrade_propose: str | None = Field(default=None, alias="upgrade-propose")


class ParticipationUpdatesSchema(BaseModel):
    """Participation account data that needs to be checked/acted on by the network."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    expired_participation_accounts: list[str] = Field(alias="expired-participation-accounts")
    absent_participation_accounts: list[str] = Field(alias="absent-participation-accounts")


class StateProofTrackingSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    type_: int | None = Field(default=None, alias="type")
    voters_commitment: str | None = Field(default=None, alias="voters-commitment")
    online_total_weight: int | None = Field(default=None, alias="online-total-weight")
    next_round: int | None = Field(default=None, alias="next-round")


class BoxReferenceSchema(BaseModel):
    """BoxReference names a box by its name and the application ID it belongs to."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    app: int = Field(alias="app")
    name: str = Field(alias="name")


class OnCompletionSchema(RootModel[str]):
    """\\[apan\\] defines the what additional actions occur with the transaction.

    Valid types:
    * noop
    * optin
    * c..."""


class HoldingRefSchema(BaseModel):
    """HoldingRef names a holding by referring to an Address and Asset it belongs to."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    asset: int = Field(alias="asset")


class LocalsRefSchema(BaseModel):
    """LocalsRef names a local state by referring to an Address and App it belongs to."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    app: int = Field(alias="app")


class ResourceRefSchema(BaseModel):
    """ResourceRef names a single resource. Only one of the fields should be set."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str | None = Field(default=None, alias="address")
    application_id: int | None = Field(default=None, alias="application-id")
    asset_id: int | None = Field(default=None, alias="asset-id")
    box: BoxReferenceSchema | None = Field(default=None, alias="box")
    holding: HoldingRefSchema | None = Field(default=None, alias="holding")
    local: LocalsRefSchema | None = Field(default=None, alias="local")


class StateSchemaSchema(BaseModel):
    """Represents a \\[apls\\] local-state or \\[apgs\\] global-state schema. These schemas determine how much sto..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    num_uints: int = Field(ge=0, le=64, alias="num-uint")
    num_byte_slices: int = Field(ge=0, le=64, alias="num-byte-slice")


class TransactionApplicationSchema(BaseModel):
    """Fields for application transactions.

    Definition:
    data/transactions/application.go : ApplicationCallTxnFiel..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    application_id: int = Field(alias="application-id")
    on_completion: OnCompletionSchema = Field(alias="on-completion")
    application_args: list[str] | None = Field(default=None, alias="application-args")
    access: list[ResourceRefSchema] | None = Field(default=None, alias="access")
    accounts: list[str] | None = Field(default=None, alias="accounts")
    box_references: list[BoxReferenceSchema] | None = Field(default=None, alias="box-references")
    foreign_apps: list[int] | None = Field(default=None, alias="foreign-apps")
    foreign_assets: list[int] | None = Field(default=None, alias="foreign-assets")
    local_state_schema: StateSchemaSchema | None = Field(default=None, alias="local-state-schema")
    global_state_schema: StateSchemaSchema | None = Field(default=None, alias="global-state-schema")
    approval_program: str | None = Field(default=None, alias="approval-program")
    clear_state_program: str | None = Field(default=None, alias="clear-state-program")
    extra_program_pages: int | None = Field(default=None, ge=0, le=3, alias="extra-program-pages")
    reject_version: int | None = Field(default=None, alias="reject-version")


class TransactionAssetConfigSchema(BaseModel):
    """Fields for asset allocation, re-configuration, and destruction.


    A zero value for asset-id indicates asset..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    asset_id: int | None = Field(default=None, alias="asset-id")
    params: AssetParamsSchema | None = Field(default=None, alias="params")


class TransactionAssetFreezeSchema(BaseModel):
    """Fields for an asset freeze transaction.

    Definition:
    data/transactions/asset.go : AssetFreezeTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    asset_id: int = Field(alias="asset-id")
    new_freeze_status: bool = Field(alias="new-freeze-status")


class TransactionAssetTransferSchema(BaseModel):
    """Fields for an asset transfer transaction.

    Definition:
    data/transactions/asset.go : AssetTransferTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    amount: int = Field(alias="amount")
    asset_id: int = Field(alias="asset-id")
    close_amount: int | None = Field(default=None, alias="close-amount")
    close_to: str | None = Field(default=None, alias="close-to")
    receiver: str = Field(alias="receiver")
    sender: str | None = Field(default=None, alias="sender")


class HbProofFieldsSchema(BaseModel):
    """\\[hbprf\\] HbProof is a signature using HeartbeatAddress's partkey, thereby showing it is online."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    hb_sig: str | None = Field(default=None, alias="hb-sig")
    hb_pk: str | None = Field(default=None, alias="hb-pk")
    hb_pk2: str | None = Field(default=None, alias="hb-pk2")
    hb_pk1sig: str | None = Field(default=None, alias="hb-pk1sig")
    hb_pk2sig: str | None = Field(default=None, alias="hb-pk2sig")


class TransactionHeartbeatSchema(BaseModel):
    """Fields for a heartbeat transaction.

    Definition:
    data/transactions/heartbeat.go : HeartbeatTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    hb_address: str = Field(alias="hb-address")
    hb_proof: HbProofFieldsSchema = Field(alias="hb-proof")
    hb_seed: str = Field(alias="hb-seed")
    hb_vote_id: str = Field(alias="hb-vote-id")
    hb_key_dilution: int = Field(alias="hb-key-dilution")


class TransactionKeyregSchema(BaseModel):
    """Fields for a keyreg transaction.

    Definition:
    data/transactions/keyreg.go : KeyregTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    non_participation: bool | None = Field(default=None, alias="non-participation")
    selection_participation_key: str | None = Field(default=None, alias="selection-participation-key")
    vote_first_valid: int | None = Field(default=None, alias="vote-first-valid")
    vote_key_dilution: int | None = Field(default=None, alias="vote-key-dilution")
    vote_last_valid: int | None = Field(default=None, alias="vote-last-valid")
    vote_participation_key: str | None = Field(default=None, alias="vote-participation-key")
    state_proof_key: str | None = Field(default=None, alias="state-proof-key")


class TransactionPaymentSchema(BaseModel):
    """Fields for a payment transaction.

    Definition:
    data/transactions/payment.go : PaymentTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    amount: int = Field(alias="amount")
    close_amount: int | None = Field(default=None, alias="close-amount")
    close_remainder_to: str | None = Field(default=None, alias="close-remainder-to")
    receiver: str = Field(alias="receiver")


class TransactionSignatureMultisigSubsignatureSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    public_key: str | None = Field(default=None, alias="public-key")
    signature: str | None = Field(default=None, alias="signature")


class TransactionSignatureMultisigSchema(BaseModel):
    """structure holding multiple subsignatures.

    Definition:
    crypto/multisig.go : MultisigSig"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    subsignature: list[TransactionSignatureMultisigSubsignatureSchema] | None = Field(
        default=None, alias="subsignature"
    )
    threshold: int | None = Field(default=None, alias="threshold")
    version: int | None = Field(default=None, alias="version")


class TransactionSignatureLogicsigSchema(BaseModel):
    """\\[lsig\\] Programatic transaction signature.

    Definition:
    data/transactions/logicsig.go"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    args: list[str] | None = Field(default=None, alias="args")
    logic: str = Field(alias="logic")
    multisig_signature: TransactionSignatureMultisigSchema | None = Field(default=None, alias="multisig-signature")
    logic_multisig_signature: TransactionSignatureMultisigSchema | None = Field(
        default=None, alias="logic-multisig-signature"
    )
    signature: str | None = Field(default=None, alias="signature")


class TransactionSignatureSchema(BaseModel):
    """Validation signature associated with some data. Only one of the signatures should be provided."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    logicsig: TransactionSignatureLogicsigSchema | None = Field(default=None, alias="logicsig")
    multisig: TransactionSignatureMultisigSchema | None = Field(default=None, alias="multisig")
    sig: str | None = Field(default=None, alias="sig")


class IndexerStateProofMessageSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    block_headers_commitment: str | None = Field(default=None, alias="block-headers-commitment")
    voters_commitment: str | None = Field(default=None, alias="voters-commitment")
    ln_proven_weight: int | None = Field(default=None, alias="ln-proven-weight")
    first_attested_round: int | None = Field(default=None, alias="first-attested-round")
    latest_attested_round: int | None = Field(default=None, alias="latest-attested-round")


class HashFactorySchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    hash_type: int | None = Field(default=None, alias="hash-type")


class MerkleArrayProofSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    path: list[str] | None = Field(default=None, alias="path")
    hash_factory: HashFactorySchema | None = Field(default=None, alias="hash-factory")
    tree_depth: int | None = Field(default=None, alias="tree-depth")


class StateProofVerifierSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    commitment: str | None = Field(default=None, alias="commitment")
    key_lifetime: int | None = Field(default=None, alias="key-lifetime")


class StateProofParticipantSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    verifier: StateProofVerifierSchema | None = Field(default=None, alias="verifier")
    weight: int | None = Field(default=None, alias="weight")


class StateProofSignatureSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    falcon_signature: str | None = Field(default=None, alias="falcon-signature")
    merkle_array_index: int | None = Field(default=None, alias="merkle-array-index")
    proof: MerkleArrayProofSchema | None = Field(default=None, alias="proof")
    verifying_key: str | None = Field(default=None, alias="verifying-key")


class StateProofSigSlotSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    signature: StateProofSignatureSchema | None = Field(default=None, alias="signature")
    lower_sig_weight: int | None = Field(default=None, alias="lower-sig-weight")


class StateProofRevealSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    position: int | None = Field(default=None, alias="position")
    sig_slot: StateProofSigSlotSchema | None = Field(default=None, alias="sig-slot")
    participant: StateProofParticipantSchema | None = Field(default=None, alias="participant")


class StateProofFieldsSchema(BaseModel):
    """\\[sp\\] represents a state proof.

    Definition:
    crypto/stateproof/structs.go : StateProof"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    sig_commit: str | None = Field(default=None, alias="sig-commit")
    signed_weight: int | None = Field(default=None, alias="signed-weight")
    sig_proofs: MerkleArrayProofSchema | None = Field(default=None, alias="sig-proofs")
    part_proofs: MerkleArrayProofSchema | None = Field(default=None, alias="part-proofs")
    salt_version: int | None = Field(default=None, alias="salt-version")
    reveals: list[StateProofRevealSchema] | None = Field(default=None, alias="reveals")
    positions_to_reveal: list[int] | None = Field(default=None, alias="positions-to-reveal")


class TransactionStateProofSchema(BaseModel):
    """Fields for a state proof transaction.

    Definition:
    data/transactions/stateproof.go : StateProofTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    state_proof_type: int | None = Field(default=None, alias="state-proof-type")
    state_proof: StateProofFieldsSchema | None = Field(default=None, alias="state-proof")
    message: IndexerStateProofMessageSchema | None = Field(default=None, alias="message")


class TransactionSchema(BaseModel):
    """Contains all fields common to all transactions and serves as an envelope to all transactions type. Represen..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    application_transaction: TransactionApplicationSchema | None = Field(default=None, alias="application-transaction")
    asset_config_transaction: TransactionAssetConfigSchema | None = Field(
        default=None, alias="asset-config-transaction"
    )
    asset_freeze_transaction: TransactionAssetFreezeSchema | None = Field(
        default=None, alias="asset-freeze-transaction"
    )
    asset_transfer_transaction: TransactionAssetTransferSchema | None = Field(
        default=None, alias="asset-transfer-transaction"
    )
    state_proof_transaction: TransactionStateProofSchema | None = Field(default=None, alias="state-proof-transaction")
    heartbeat_transaction: TransactionHeartbeatSchema | None = Field(default=None, alias="heartbeat-transaction")
    auth_addr: str | None = Field(default=None, alias="auth-addr")
    close_rewards: int | None = Field(default=None, alias="close-rewards")
    closing_amount: int | None = Field(default=None, alias="closing-amount")
    confirmed_round: int | None = Field(default=None, alias="confirmed-round")
    created_app_id: int | None = Field(default=None, alias="created-application-index")
    created_asset_id: int | None = Field(default=None, alias="created-asset-index")
    fee: int = Field(alias="fee")
    first_valid: int = Field(alias="first-valid")
    genesis_hash: str | None = Field(default=None, alias="genesis-hash")
    genesis_id: str | None = Field(default=None, alias="genesis-id")
    group: str | None = Field(default=None, alias="group")
    id_: str | None = Field(default=None, alias="id")
    intra_round_offset: int | None = Field(default=None, alias="intra-round-offset")
    keyreg_transaction: TransactionKeyregSchema | None = Field(default=None, alias="keyreg-transaction")
    last_valid: int = Field(alias="last-valid")
    lease: str | None = Field(default=None, alias="lease")
    note: str | None = Field(default=None, alias="note")
    payment_transaction: TransactionPaymentSchema | None = Field(default=None, alias="payment-transaction")
    receiver_rewards: int | None = Field(default=None, alias="receiver-rewards")
    rekey_to: str | None = Field(default=None, alias="rekey-to")
    round_time: int | None = Field(default=None, alias="round-time")
    sender: str = Field(alias="sender")
    sender_rewards: int | None = Field(default=None, alias="sender-rewards")
    signature: TransactionSignatureSchema | None = Field(default=None, alias="signature")
    tx_type: str = Field(alias="tx-type")
    local_state_delta: list[AccountStateDeltaSchema] | None = Field(default=None, alias="local-state-delta")
    global_state_delta: StateDeltaSchema | None = Field(default=None, alias="global-state-delta")
    logs: list[str] | None = Field(default=None, alias="logs")
    inner_txns: list[TransactionSchema] | None = Field(default=None, alias="inner-txns")


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
    rewards: BlockRewardsSchema = Field(alias="rewards")
    round_: int = Field(alias="round")
    seed: str = Field(alias="seed")
    state_proof_tracking: list[StateProofTrackingSchema] | None = Field(default=None, alias="state-proof-tracking")
    timestamp: int = Field(alias="timestamp")
    transactions: list[TransactionSchema] = Field(alias="transactions")
    transactions_root: str = Field(alias="transactions-root")
    transactions_root_sha256: str | None = Field(default=None, alias="transactions-root-sha256")
    transactions_root_sha512: str | None = Field(default=None, alias="transactions-root-sha512")
    txn_counter: int | None = Field(default=None, alias="txn-counter")
    upgrade_state: BlockUpgradeStateSchema = Field(alias="upgrade-state")
    upgrade_vote: BlockUpgradeVoteSchema | None = Field(default=None, alias="upgrade-vote")
    participation_updates: ParticipationUpdatesSchema = Field(alias="participation-updates")


class BlockHeadersResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")
    blocks: list[BlockSchema] = Field(alias="blocks")


class BoxSchema(BaseModel):
    """Box name and its content."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    round_: int = Field(alias="round")
    name: str = Field(alias="name")
    value: str = Field(alias="value")


class BoxDescriptorSchema(BaseModel):
    """Box descriptor describes an app box without a value."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    name: str = Field(alias="name")


class BoxesResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    application_id: int = Field(alias="application-id")
    boxes: list[BoxDescriptorSchema] = Field(alias="boxes")
    next_token: str | None = Field(default=None, alias="next-token")


class ErrorResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    data: dict[str, Any] | None = Field(default=None, alias="data")
    message: str = Field(alias="message")


class HashtypeSchema(RootModel[str]):
    """The type of hash function used to create the proof, must be one of:
    * sha512_256
    * sha256"""


class HealthCheckSchema(BaseModel):
    """A health check response."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    version: str = Field(alias="version")
    data: dict[str, Any] | None = Field(default=None, alias="data")
    round_: int = Field(alias="round")
    is_migrating: bool = Field(alias="is-migrating")
    db_available: bool = Field(alias="db-available")
    message: str = Field(alias="message")
    errors: list[str] | None = Field(default=None, alias="errors")


class TransactionResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    transaction: TransactionSchema = Field(alias="transaction")
    current_round: int = Field(alias="current-round")


class TransactionsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    current_round: int = Field(alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")
    transactions: list[TransactionSchema] = Field(alias="transactions")
