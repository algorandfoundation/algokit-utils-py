# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_fixed_bytes, encode_fixed_bytes


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
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    hb_pk1sig: bytes | None = field(
        default=None,
        metadata=wire(
            "hb-pk1sig",
            encode=lambda v: encode_fixed_bytes(v, 64),
            decode=lambda raw: decode_fixed_bytes(raw, 64),
        ),
    )
    hb_pk2: bytes | None = field(
        default=None,
        metadata=wire(
            "hb-pk2",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    hb_pk2sig: bytes | None = field(
        default=None,
        metadata=wire(
            "hb-pk2sig",
            encode=lambda v: encode_fixed_bytes(v, 64),
            decode=lambda raw: decode_fixed_bytes(raw, 64),
        ),
    )
    hb_sig: bytes | None = field(
        default=None,
        metadata=wire(
            "hb-sig",
            encode=lambda v: encode_fixed_bytes(v, 64),
            decode=lambda raw: decode_fixed_bytes(raw, 64),
        ),
    )
