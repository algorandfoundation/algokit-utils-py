# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_fixed_bytes_base64, encode_fixed_bytes_base64


@dataclass(slots=True)
class StateProofVerifier:
    commitment: bytes | None = field(
        default=None,
        metadata=wire(
            "commitment",
            encode=lambda v: encode_fixed_bytes_base64(v, 64),
            decode=lambda raw: decode_fixed_bytes_base64(raw, 64),
        ),
    )
    key_lifetime: int | None = field(
        default=None,
        metadata=wire("key-lifetime"),
    )
