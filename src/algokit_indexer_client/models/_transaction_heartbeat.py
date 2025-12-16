# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._hb_proof_fields import HbProofFields
from ._serde_helpers import (
    decode_bytes_base64,
    decode_fixed_bytes_base64,
    encode_bytes_base64,
    encode_fixed_bytes_base64,
)


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
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    hb_vote_id: bytes = field(
        default=b"",
        metadata=wire(
            "hb-vote-id",
            encode=lambda v: encode_fixed_bytes_base64(v, 32),
            decode=lambda raw: decode_fixed_bytes_base64(raw, 32),
        ),
    )
