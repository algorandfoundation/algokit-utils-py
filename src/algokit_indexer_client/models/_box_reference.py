# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class BoxReference:
    """
    BoxReference names a box by its name and the application ID it belongs to.
    """

    app: int = field(
        default=0,
        metadata=wire("app"),
    )
    name: bytes = field(
        default=b"",
        metadata=wire(
            "name",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
