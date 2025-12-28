# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._block_rewards import BlockRewards
from ._block_upgrade_state import BlockUpgradeState
from ._block_upgrade_vote import BlockUpgradeVote
from ._participation_updates import ParticipationUpdates
from ._serde_helpers import decode_fixed_bytes, decode_model_sequence, encode_fixed_bytes, encode_model_sequence
from ._state_proof_tracking import StateProofTracking
from ._transaction import Transaction


@dataclass(slots=True)
class Block:
    """
    Block information.

    Definition:
    data/bookkeeping/block.go : Block
    """

    participation_updates: ParticipationUpdates = field(
        metadata=nested("participation-updates", lambda: ParticipationUpdates, required=True),
    )
    rewards: BlockRewards = field(
        metadata=nested("rewards", lambda: BlockRewards, required=True),
    )
    upgrade_state: BlockUpgradeState = field(
        metadata=nested("upgrade-state", lambda: BlockUpgradeState, required=True),
    )
    genesis_hash: bytes = field(
        default=b"",
        metadata=wire(
            "genesis-hash",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    genesis_id: str = field(
        default="",
        metadata=wire("genesis-id"),
    )
    previous_block_hash: bytes = field(
        default=b"",
        metadata=wire(
            "previous-block-hash",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    round_: int = field(
        default=0,
        metadata=wire("round"),
    )
    seed: bytes = field(
        default=b"",
        metadata=wire(
            "seed",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    timestamp: int = field(
        default=0,
        metadata=wire("timestamp"),
    )
    transactions: list[Transaction] = field(
        default_factory=list,
        metadata=wire(
            "transactions",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Transaction, raw),
        ),
    )
    transactions_root: bytes = field(
        default=b"",
        metadata=wire(
            "transactions-root",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    bonus: int | None = field(
        default=None,
        metadata=wire("bonus"),
    )
    fees_collected: int | None = field(
        default=None,
        metadata=wire("fees-collected"),
    )
    previous_block_hash_512: bytes | None = field(
        default=None,
        metadata=wire(
            "previous-block-hash-512",
            encode=lambda v: encode_fixed_bytes(v, 64),
            decode=lambda raw: decode_fixed_bytes(raw, 64),
        ),
    )
    proposer: str | None = field(
        default=None,
        metadata=wire("proposer"),
    )
    proposer_payout: int | None = field(
        default=None,
        metadata=wire("proposer-payout"),
    )
    state_proof_tracking: list[StateProofTracking] | None = field(
        default=None,
        metadata=wire(
            "state-proof-tracking",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: StateProofTracking, raw),
        ),
    )
    transactions_root_sha256: bytes | None = field(
        default=None,
        metadata=wire(
            "transactions-root-sha256",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    transactions_root_sha512: bytes | None = field(
        default=None,
        metadata=wire(
            "transactions-root-sha512",
            encode=lambda v: encode_fixed_bytes(v, 64),
            decode=lambda raw: decode_fixed_bytes(raw, 64),
        ),
    )
    txn_counter: int | None = field(
        default=None,
        metadata=wire("txn-counter"),
    )
    upgrade_vote: BlockUpgradeVote | None = field(
        default=None,
        metadata=nested("upgrade-vote", lambda: BlockUpgradeVote),
    )
