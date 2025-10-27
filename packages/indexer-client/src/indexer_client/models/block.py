from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .block_rewards import BlockRewards
from .block_upgrade_state import BlockUpgradeState
from .block_upgrade_vote import BlockUpgradeVote
from .participation_updates import ParticipationUpdates
from .state_proof_tracking import StateProofTracking
from .transaction import Transaction


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
    bonus: int | None = field(
        default=None,
        metadata=wire("bonus"),
    )
    fees_collected: int | None = field(
        default=None,
        metadata=wire("fees-collected"),
    )
    participation_updates: ParticipationUpdates | None = field(
        default=None,
        metadata=nested("participation-updates", lambda: ParticipationUpdates),
    )
    previous_block_hash_512: bytes | None = field(
        default=None,
        metadata=wire("previous-block-hash-512"),
    )
    proposer: str | None = field(
        default=None,
        metadata=wire("proposer"),
    )
    proposer_payout: int | None = field(
        default=None,
        metadata=wire("proposer-payout"),
    )
    rewards: BlockRewards | None = field(
        default=None,
        metadata=nested("rewards", lambda: BlockRewards),
    )
    state_proof_tracking: list[StateProofTracking] | None = field(
        default=None,
        metadata=wire(
            "state-proof-tracking",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: StateProofTracking, raw),
        ),
    )
    transactions: list[Transaction] | None = field(
        default=None,
        metadata=wire(
            "transactions",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Transaction, raw),
        ),
    )
    transactions_root_sha512: bytes | None = field(
        default=None,
        metadata=wire("transactions-root-sha512"),
    )
    txn_counter: int | None = field(
        default=None,
        metadata=wire("txn-counter"),
    )
    upgrade_state: BlockUpgradeState | None = field(
        default=None,
        metadata=nested("upgrade-state", lambda: BlockUpgradeState),
    )
    upgrade_vote: BlockUpgradeVote | None = field(
        default=None,
        metadata=nested("upgrade-vote", lambda: BlockUpgradeVote),
    )
