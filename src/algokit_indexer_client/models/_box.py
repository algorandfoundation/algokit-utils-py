# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class Box:
    """
    Box name and its content.
    """

    name: bytes = field(
        default=b"",
        metadata=wire(
            "name",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    round_: int = field(
        default=0,
        metadata=wire("round"),
    )
    value: bytes = field(
        default=b"",
        metadata=wire(
            "value",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
