# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._hb_proof_fields import HbProofFields
from ._serde_helpers import decode_bytes, decode_fixed_bytes, encode_bytes, encode_fixed_bytes


@dataclass(slots=True)
class TransactionHeartbeat:
    """
    Fields for a heartbeat transaction.

    Definition:
    data/transactions/heartbeat.go : HeartbeatTxnFields
    """

    hb_proof: HbProofFields = field(
        metadata=nested("hb-proof", lambda: HbProofFields, required=True),
    )
    hb_address: str = field(
        default="",
        metadata=wire("hb-address"),
    )
    hb_key_dilution: int = field(
        default=0,
        metadata=wire("hb-key-dilution"),
    )
    hb_seed: bytes = field(
        default=b"",
        metadata=wire(
            "hb-seed",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    hb_vote_id: bytes = field(
        default=b"",
        metadata=wire(
            "hb-vote-id",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
