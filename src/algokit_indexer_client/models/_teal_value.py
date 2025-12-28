# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class TealValue:
    """
    Represents a TEAL value.
    """

    bytes_: bytes = field(
        default=b"",
        metadata=wire(
            "bytes",
            encode=encode_bytes,
            decode=decode_bytes,
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
