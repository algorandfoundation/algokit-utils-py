# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class BoxDescriptor:
    """
    Box descriptor describes a Box.
    """

    name: bytes = field(
        default=b"",
        metadata=wire(
            "name",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
