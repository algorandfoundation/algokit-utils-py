# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .hb_proof_fields import HbProofFields


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
