# AUTO-GENERATED: oas_generator


from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, cast

from algokit_common.serde import flatten, nested, wire
from algokit_transact.models.signed_transaction import SignedTransaction

from ._serde_helpers import (
    decode_bytes_base64,
    decode_model_mapping,
    decode_model_sequence,
    encode_bytes_base64,
    encode_model_mapping,
    encode_model_sequence,
    mapping_decoder,
    mapping_encoder,
)

__all__ = [
    "Block",
    "BlockAccountStateDelta",
    "BlockAppEvalDelta",
    "BlockEvalDelta",
    "BlockStateDelta",
    "BlockStateProofTracking",
    "BlockStateProofTrackingData",
    "GetBlock",
    "SignedTxnInBlock",
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
        return encode_bytes_base64(key)
    if isinstance(key, memoryview):
        return encode_bytes_base64(bytes(key))
    if isinstance(key, bytearray):
        return encode_bytes_base64(bytes(key))
    raise TypeError("State delta keys must be bytes-like")


def _decode_state_proof_tracking_key(key: object) -> int:
    if isinstance(key, int):
        return key
    if isinstance(key, str):
        return int(key)
    raise TypeError("State proof tracking keys must be numeric")


def _decode_block_state_delta(raw: object) -> BlockStateDelta | None:
    decoded = decode_model_mapping(lambda: BlockEvalDelta, raw, key_decoder=decode_bytes_base64)
    return decoded or None


def _encode_local_deltas(mapping: Mapping[int, BlockStateDelta] | None) -> dict[str, object] | None:
    if mapping is None:
        return None
    out: dict[str, object] = {}
    for key, value in mapping.items():
        encoded = _encode_block_state_delta(value)
        if encoded:
            out[str(int(key))] = encoded
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
    bytes: str | None = field(default=None, metadata=wire("bs"))
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
class SignedTxnInBlock:
    """Signed transaction details with block-specific apply data."""

    signed_transaction: SignedTransaction = field(metadata=flatten(lambda: SignedTransaction))
    logic_signature: dict[str, Any] | None = field(default=None, metadata=wire("lsig"))
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
    has_genesis_id: bool | None = field(default=None, metadata=wire("hgi"))
    has_genesis_hash: bool | None = field(default=None, metadata=wire("hgh"))


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
    inner_txns: list[SignedTxnInBlock] | None = field(
        default=None,
        metadata=wire(
            "itx",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SignedTxnInBlock, raw),
        ),
    )
    shared_accounts: list[bytes] | None = field(default=None, metadata=wire("sa"))
    logs: list[bytes] | None = field(default=None, metadata=wire("lg"))


@dataclass(slots=True)
class Block:
    """Block header fields and transactions for a ledger round."""

    round: int | None = field(default=None, metadata=wire("rnd"))
    previous_block_hash: bytes | None = field(default=None, metadata=wire("prev"))
    previous_block_hash_512: bytes | None = field(default=None, metadata=wire("prev512"))
    seed: bytes | None = field(default=None, metadata=wire("seed"))
    transactions_root: bytes | None = field(default=None, metadata=wire("txn"))
    transactions_root_sha256: bytes | None = field(default=None, metadata=wire("txn256"))
    transactions_root_sha512: bytes | None = field(default=None, metadata=wire("txn512"))
    timestamp: int | None = field(default=None, metadata=wire("ts"))
    genesis_id: str | None = field(default=None, metadata=wire("gen"))
    genesis_hash: bytes | None = field(default=None, metadata=wire("gh"))
    proposer: bytes | None = field(default=None, metadata=wire("prp"))
    fees_collected: int | None = field(default=None, metadata=wire("fc"))
    bonus: int | None = field(default=None, metadata=wire("bi"))
    proposer_payout: int | None = field(default=None, metadata=wire("pp"))
    fee_sink: bytes | None = field(default=None, metadata=wire("fees"))
    rewards_pool: bytes | None = field(default=None, metadata=wire("rwd"))
    rewards_level: int | None = field(default=None, metadata=wire("earn"))
    rewards_rate: int | None = field(default=None, metadata=wire("rate"))
    rewards_residue: int | None = field(default=None, metadata=wire("frac"))
    rewards_recalculation_round: int | None = field(default=None, metadata=wire("rwcalr"))
    current_protocol: str | None = field(default=None, metadata=wire("proto"))
    next_protocol: str | None = field(default=None, metadata=wire("nextproto"))
    next_protocol_approvals: int | None = field(default=None, metadata=wire("nextyes"))
    next_protocol_vote_before: int | None = field(default=None, metadata=wire("nextbefore"))
    next_protocol_switch_on: int | None = field(default=None, metadata=wire("nextswitch"))
    upgrade_propose: str | None = field(default=None, metadata=wire("upgradeprop"))
    upgrade_delay: int | None = field(default=None, metadata=wire("upgradedelay"))
    upgrade_approve: bool | None = field(default=None, metadata=wire("upgradeyes"))
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
    expired_participation_accounts: list[bytes] | None = field(
        default=None,
        metadata=wire("partupdrmv"),
    )
    absent_participation_accounts: list[bytes] | None = field(
        default=None,
        metadata=wire("partupdabs"),
    )
    transactions: list[SignedTxnInBlock] | None = field(
        default=None,
        metadata=wire(
            "txns",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SignedTxnInBlock, raw),
        ),
    )


@dataclass(slots=True)
class GetBlock:
    """Response payload for the get block endpoint (with optional certificate)."""

    block: Block = field(metadata=nested("block", lambda: Block))
    cert: dict[str, object] | None = field(default=None, metadata=wire("cert"))
