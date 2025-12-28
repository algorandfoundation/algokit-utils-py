# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class AvmValue:
    """
    Represents an AVM value.
    """

    type_: int = field(
        default=0,
        metadata=wire("type"),
    )
    bytes_: bytes | None = field(
        default=None,
        metadata=wire(
            "bytes",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    uint: int | None = field(
        default=None,
        metadata=wire("uint"),
    )
