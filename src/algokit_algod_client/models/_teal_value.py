# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class TealValue:
    """
    Represents a TEAL value.
    """

    bytes_: bytes = field(
        default=b"",
        metadata=wire(
            "bytes",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    type_: int = field(
        default=0,
        metadata=wire("type"),
    )
    uint: int = field(
        default=0,
        metadata=wire("uint"),
    )
