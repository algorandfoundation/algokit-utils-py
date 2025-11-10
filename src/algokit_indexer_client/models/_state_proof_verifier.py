# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class StateProofVerifier:
    commitment: bytes | None = field(
        default=None,
        metadata=wire(
            "commitment",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    key_lifetime: int | None = field(
        default=None,
        metadata=wire("key-lifetime"),
    )
