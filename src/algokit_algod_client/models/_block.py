# AUTO-GENERATED: oas_generator
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

from algokit_common import ZERO_ADDRESS
from algokit_common.serde import addr, addr_seq, flatten, nested, wire
from algokit_transact.models.signed_transaction import SignedTransaction

from ._serde_helpers import (
    decode_bytes_map_key,
    decode_model_mapping,
    decode_model_sequence,
    decode_optional_bool,
    encode_bytes,
    encode_model_mapping,
    encode_model_sequence,
    mapping_decoder,
    mapping_encoder,
)

__all__ = [
    "ApplyData",
    "Block",
    "BlockAccountStateDelta",
    "BlockAppEvalDelta",
    "BlockEvalDelta",
    "BlockHeader",
    "BlockResponse",
    "BlockStateDelta",
    "BlockStateProofTracking",
    "BlockStateProofTrackingData",
    "ParticipationUpdates",
    "RewardState",
    "SignedTxnInBlock",
    "SignedTxnWithAD",
    "TxnCommitments",
    "UpgradeState",
    "UpgradeVote",
]

BlockStateDelta = dict[bytes, "BlockEvalDelta"]
BlockStateProofTracking = dict[int, "BlockStateProofTrackingData"]


def _encode_block_state_delta(value: BlockStateDelta | None) -> dict[str, object] | None:
    if value is None:
        return None
    return encode_model_mapping(
        lambda: BlockEvalDelta,
        cast(Mapping[object, object], value),
        key_encoder=_encode_state_delta_key,
    )


def _encode_state_delta_key(key: object) -> str:
    if isinstance(key, bytes):
        return encode_bytes(key)
    if isinstance(key, memoryview):
        return encode_bytes(bytes(key))
    if isinstance(key, bytearray):
        return encode_bytes(bytes(key))
    raise TypeError("State delta keys must be bytes-like")


def _decode_state_proof_tracking_key(key: object) -> int:
    if isinstance(key, int):
        return key
    if isinstance(key, str):
        return int(key)
    raise TypeError("State proof tracking keys must be numeric")


def _decode_block_state_delta(raw: object) -> BlockStateDelta | None:
    decoded = decode_model_mapping(lambda: BlockEvalDelta, raw, key_decoder=decode_bytes_map_key)
    return decoded or None


def _encode_local_delta_index_key(key: object) -> str:
    if isinstance(key, bool):
        return str(int(key))
    if isinstance(key, int):
        return str(key)
    if isinstance(key, str):
        return str(int(key))
    raise TypeError("Local delta keys must be numeric")


def _encode_local_deltas(mapping: Mapping[int, BlockStateDelta] | None) -> dict[str, object] | None:
    if mapping is None:
        return None
    out: dict[str, object] = {}
    for key, value in mapping.items():
        encoded = _encode_block_state_delta(value)
        if encoded:
            out[_encode_local_delta_index_key(key)] = encoded
    return out or None


def _decode_local_deltas(raw: object) -> dict[int, BlockStateDelta] | None:
    if not isinstance(raw, Mapping):
        return None
    out: dict[int, BlockStateDelta] = {}
    for key, value in raw.items():
        decoded = _decode_block_state_delta(value)
        if decoded is not None:
            out[_decode_local_delta_index_key(key)] = decoded
    return out or None


def _decode_local_delta_index_key(key: object) -> int:
    if isinstance(key, int):
        return key
    if isinstance(key, str):
        return int(key)
    raise TypeError("Local delta keys must be numeric")


@dataclass(slots=True)
class BlockEvalDelta:
    """Represents a TEAL value delta within block state changes."""

    action: int = field(metadata=wire("at", required=True))
    bytes_: bytes | None = field(default=None, metadata=wire("bs"))
    uint: int | None = field(default=None, metadata=wire("ui"))


@dataclass(slots=True)
class BlockAccountStateDelta:
    """Associates an account address with its state delta."""

    address: str = field(metadata=wire("address", required=True))
    delta: BlockStateDelta = field(
        metadata=wire(
            "delta",
            encode=_encode_block_state_delta,
            decode=_decode_block_state_delta,
        )
    )


@dataclass(slots=True)
class BlockStateProofTrackingData:
    """Tracking metadata for a specific state proof type."""

    state_proof_voters_commitment: bytes | None = field(
        default=None,
        metadata=wire("v"),
    )
    state_proof_online_total_weight: int | None = field(
        default=None,
        metadata=wire("t"),
    )
    state_proof_next_round: int | None = field(
        default=None,
        metadata=wire("n"),
    )


@dataclass(slots=True)
class ApplyData:
    """Transaction execution apply data containing state changes and rewards."""

    closing_amount: int | None = field(default=None, metadata=wire("ca"))
    asset_closing_amount: int | None = field(default=None, metadata=wire("aca"))
    sender_rewards: int | None = field(default=None, metadata=wire("rs"))
    receiver_rewards: int | None = field(default=None, metadata=wire("rr"))
    close_rewards: int | None = field(default=None, metadata=wire("rc"))
    eval_delta: "BlockAppEvalDelta | None" = field(
        default=None,
        metadata=nested("dt", lambda: BlockAppEvalDelta),
    )
    config_asset: int | None = field(default=None, metadata=wire("caid"))
    application_id: int | None = field(default=None, metadata=wire("apid"))


@dataclass(slots=True)
class SignedTxnWithAD:
    """Signed transaction with associated apply data."""

    signed_transaction: SignedTransaction = field(metadata=flatten(lambda: SignedTransaction))
    apply_data: ApplyData | None = field(default=None, metadata=flatten(lambda: ApplyData))


@dataclass(slots=True)
class TxnCommitments:
    """Transaction commitment hashes for the block."""

    native_sha512_256_commitment: bytes = field(default_factory=lambda: bytes(32), metadata=wire("txn"))
    """Root of transaction merkle tree using SHA512_256."""
    sha256_commitment: bytes | None = field(default_factory=lambda: bytes(32), metadata=wire("txn256"))
    """Root of transaction vector commitment using SHA256."""
    sha512_commitment: bytes | None = field(default_factory=lambda: bytes(64), metadata=wire("txn512"))
    """Root of transaction vector commitment using SHA512."""


@dataclass(slots=True)
class RewardState:
    """Reward distribution state for the block."""

    fee_sink: str = field(default=ZERO_ADDRESS, metadata=addr("fees"))
    rewards_pool: str = field(default=ZERO_ADDRESS, metadata=addr("rwd"))
    rewards_level: int = field(default=0, metadata=wire("earn"))
    rewards_rate: int = field(default=0, metadata=wire("rate"))
    rewards_residue: int = field(default=0, metadata=wire("frac"))
    rewards_recalculation_round: int = field(default=0, metadata=wire("rwcalr"))


@dataclass(slots=True)
class UpgradeState:
    """Protocol upgrade state for the block."""

    current_protocol: str = field(default="", metadata=wire("proto", required=True))
    next_protocol: str | None = field(default=None, metadata=wire("nextproto"))
    next_protocol_approvals: int | None = field(default=None, metadata=wire("nextyes"))
    next_protocol_vote_before: int | None = field(default=None, metadata=wire("nextbefore"))
    next_protocol_switch_on: int | None = field(default=None, metadata=wire("nextswitch"))


@dataclass(slots=True)
class UpgradeVote:
    """Protocol upgrade vote parameters for the block."""

    upgrade_propose: str | None = field(default=None, metadata=wire("upgradeprop"))
    upgrade_delay: int | None = field(default=None, metadata=wire("upgradedelay"))
    upgrade_approve: bool | None = field(default=None, metadata=wire("upgradeyes"))


@dataclass(slots=True)
class ParticipationUpdates:
    """Participation account updates embedded in a block."""

    expired_participation_accounts: tuple[str, ...] = field(default=(), metadata=addr_seq("partupdrmv"))
    absent_participation_accounts: tuple[str, ...] = field(default=(), metadata=addr_seq("partupdabs"))


@dataclass(slots=True)
class SignedTxnInBlock:
    """Signed transaction details with block-specific apply data."""

    signed_transaction: SignedTxnWithAD = field(metadata=flatten(lambda: SignedTxnWithAD))
    has_genesis_id: bool | None = field(default=None, metadata=wire("hgi", decode=decode_optional_bool))
    has_genesis_hash: bool | None = field(default=None, metadata=wire("hgh", decode=decode_optional_bool))


@dataclass(slots=True)
class BlockAppEvalDelta:
    """State changes produced by an application execution during block evaluation."""

    global_delta: BlockStateDelta | None = field(
        default=None,
        metadata=wire(
            "gd",
            encode=_encode_block_state_delta,
            decode=_decode_block_state_delta,
        ),
    )
    local_deltas: dict[int, BlockStateDelta] | None = field(
        default=None,
        metadata=wire(
            "ld",
            encode=_encode_local_deltas,
            decode=_decode_local_deltas,
        ),
    )
    inner_txns: list[SignedTxnWithAD] | None = field(
        default=None,
        metadata=wire(
            "itx",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SignedTxnWithAD, raw),
        ),
    )
    shared_accounts: tuple[str, ...] | None = field(default=None, metadata=addr_seq("sa"))
    logs: list[bytes] | None = field(default=None, metadata=wire("lg"))


@dataclass(slots=True)
class BlockHeader:
    """Block header fields."""

    round: int = field(default=0, metadata=wire("rnd"))
    previous_block_hash: bytes = field(default_factory=lambda: bytes(32), metadata=wire("prev"))
    previous_block_hash_512: bytes | None = field(default=None, metadata=wire("prev512"))
    seed: bytes = field(default=b"", metadata=wire("seed"))
    txn_commitments: TxnCommitments = field(
        default_factory=TxnCommitments,
        metadata=flatten(lambda: TxnCommitments),
    )
    timestamp: int = field(default=0, metadata=wire("ts"))
    genesis_id: str = field(default="", metadata=wire("gen"))
    genesis_hash: bytes = field(default_factory=lambda: bytes(32), metadata=wire("gh"))
    proposer: str | None = field(default=None, metadata=addr("prp"))
    fees_collected: int | None = field(default=None, metadata=wire("fc"))
    bonus: int | None = field(default=None, metadata=wire("bi"))
    proposer_payout: int | None = field(default=None, metadata=wire("pp"))
    reward_state: RewardState = field(
        default_factory=RewardState,
        metadata=flatten(lambda: RewardState),
    )
    upgrade_state: UpgradeState = field(
        default_factory=UpgradeState,
        metadata=flatten(lambda: UpgradeState),
    )
    upgrade_vote: UpgradeVote | None = field(
        default=None,
        metadata=flatten(lambda: UpgradeVote),
    )
    txn_counter: int | None = field(default=None, metadata=wire("tc"))
    state_proof_tracking: BlockStateProofTracking | None = field(
        default=None,
        metadata=wire(
            "spt",
            encode=mapping_encoder(lambda: BlockStateProofTrackingData),
            decode=mapping_decoder(
                lambda: BlockStateProofTrackingData,
                key_decoder=_decode_state_proof_tracking_key,
            ),
        ),
    )
    participation_updates: ParticipationUpdates = field(
        default_factory=ParticipationUpdates,
        metadata=flatten(lambda: ParticipationUpdates),
    )


@dataclass(slots=True)
class Block:
    """Block header fields and transactions for a ledger round."""

    header: BlockHeader = field(metadata=flatten(lambda: BlockHeader))
    payset: list[SignedTxnInBlock] | None = field(
        default=None,
        metadata=wire(
            "txns",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SignedTxnInBlock, raw),
        ),
    )

    def __post_init__(self) -> None:
        # populates genesis id and hash on transactions if required to ensure
        # tx id's are correct
        genesis_id = self.header.genesis_id
        genesis_hash = self.header.genesis_hash
        set_frozen_field = object.__setattr__
        for txn_in_block in self.payset or []:
            txn = txn_in_block.signed_transaction.signed_transaction.txn

            if txn_in_block.has_genesis_id and txn.genesis_id is None:
                set_frozen_field(txn, "genesis_id", genesis_id)

            # the following assumes that Consensus.RequireGenesisHash is true
            # so assigns genesis hash unless explicitly set to False
            if txn_in_block.has_genesis_hash is not False and txn.genesis_hash is None:
                set_frozen_field(txn, "genesis_hash", genesis_hash)


@dataclass(slots=True)
class BlockResponse:
    """Response payload for the get block endpoint (with optional certificate)."""

    block: Block = field(metadata=nested("block", lambda: Block))
    cert: dict[str, object] | None = field(default=None, metadata=wire("cert"))
