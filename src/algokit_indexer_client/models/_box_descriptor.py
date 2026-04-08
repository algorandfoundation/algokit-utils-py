# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class BoxDescriptor:
    """
    Box descriptor describes an app box without a value.
    """

    name: bytes = field(
        default=b"",
        metadata=wire(
            "name",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
