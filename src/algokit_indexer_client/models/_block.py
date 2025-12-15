# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._block_rewards import BlockRewards
from ._block_upgrade_state import BlockUpgradeState
from ._block_upgrade_vote import BlockUpgradeVote
from ._participation_updates import ParticipationUpdates
from ._serde_helpers import (
    decode_bytes_base64,
    decode_fixed_bytes_base64,
    decode_model_sequence,
    encode_bytes_base64,
    encode_fixed_bytes_base64,
    encode_model_sequence,
)
from ._state_proof_tracking import StateProofTracking
from ._transaction import Transaction


@dataclass(slots=True)
class Block:
    """
    Block information.

    Definition:
    data/bookkeeping/block.go : Block
    """

    genesis_hash: bytes = field(
        default=b"",
        metadata=wire(
            "genesis-hash",
            encode=lambda v: encode_fixed_bytes_base64(v, 32),
            decode=lambda raw: decode_fixed_bytes_base64(raw, 32),
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
            encode=lambda v: encode_fixed_bytes_base64(v, 32),
            decode=lambda raw: decode_fixed_bytes_base64(raw, 32),
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
            encode=lambda v: encode_fixed_bytes_base64(v, 32),
            decode=lambda raw: decode_fixed_bytes_base64(raw, 32),
        ),
    )
    timestamp: int = field(
        default=0,
        metadata=wire("timestamp"),
    )
    transactions_root: bytes = field(
        default=b"",
        metadata=wire(
            "transactions-root",
            encode=lambda v: encode_fixed_bytes_base64(v, 32),
            decode=lambda raw: decode_fixed_bytes_base64(raw, 32),
        ),
    )
    transactions_root_sha256: bytes = field(
        default=b"",
        metadata=wire(
            "transactions-root-sha256",
            encode=lambda v: encode_fixed_bytes_base64(v, 32),
            decode=lambda raw: decode_fixed_bytes_base64(raw, 32),
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
    participation_updates: ParticipationUpdates | None = field(
        default=None,
        metadata=nested("participation-updates", lambda: ParticipationUpdates),
    )
    previous_block_hash_512: bytes | None = field(
        default=None,
        metadata=wire(
            "previous-block-hash-512",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
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
        metadata=wire(
            "transactions-root-sha512",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
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
