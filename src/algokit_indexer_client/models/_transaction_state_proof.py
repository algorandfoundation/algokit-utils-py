# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._indexer_state_proof_message import IndexerStateProofMessage
from ._state_proof_fields import StateProofFields


@dataclass(slots=True)
class TransactionStateProof:
    """
    Fields for a state proof transaction.

    Definition:
    data/transactions/stateproof.go : StateProofTxnFields
    """

    message: IndexerStateProofMessage | None = field(
        default=None,
        metadata=nested("message", lambda: IndexerStateProofMessage),
    )
    state_proof: StateProofFields | None = field(
        default=None,
        metadata=nested("state-proof", lambda: StateProofFields),
    )
    state_proof_type: int | None = field(
        default=None,
        metadata=wire("state-proof-type"),
    )
