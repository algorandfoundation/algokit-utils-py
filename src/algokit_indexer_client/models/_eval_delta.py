# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class EvalDelta:
    """
    Represents a TEAL value delta.
    """

    action: int = field(
        default=0,
        metadata=wire("action"),
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
