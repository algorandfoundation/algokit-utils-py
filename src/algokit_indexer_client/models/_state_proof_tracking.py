# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class StateProofTracking:
    next_round: int | None = field(
        default=None,
        metadata=wire("next-round"),
    )
    online_total_weight: int | None = field(
        default=None,
        metadata=wire("online-total-weight"),
    )
    type_: int | None = field(
        default=None,
        metadata=wire("type"),
    )
    voters_commitment: bytes | None = field(
        default=None,
        metadata=wire(
            "voters-commitment",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
