# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class HbProofFields:
    r"""
    \[hbprf\] HbProof is a signature using HeartbeatAddress's partkey, thereby showing it is
    online.
    """

    hb_pk: bytes | None = field(
        default=None,
        metadata=wire("hb-pk"),
    )
    hb_pk1sig: bytes | None = field(
        default=None,
        metadata=wire("hb-pk1sig"),
    )
    hb_pk2: bytes | None = field(
        default=None,
        metadata=wire("hb-pk2"),
    )
    hb_pk2sig: bytes | None = field(
        default=None,
        metadata=wire("hb-pk2sig"),
    )
    hb_sig: bytes | None = field(
        default=None,
        metadata=wire("hb-sig"),
    )
