# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class HbProofFields:
    r"""
    \[hbprf\] HbProof is a signature using HeartbeatAddress's partkey, thereby showing it is
    online.
    """

    hb_pk: bytes | None = field(
        default=None,
        metadata=wire(
            "hb-pk",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    hb_pk1sig: bytes | None = field(
        default=None,
        metadata=wire(
            "hb-pk1sig",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    hb_pk2: bytes | None = field(
        default=None,
        metadata=wire(
            "hb-pk2",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    hb_pk2sig: bytes | None = field(
        default=None,
        metadata=wire(
            "hb-pk2sig",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    hb_sig: bytes | None = field(
        default=None,
        metadata=wire(
            "hb-sig",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
