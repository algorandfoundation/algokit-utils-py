# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class BoxReference:
    """
    References a box of an application.
    """

    app: int = field(
        metadata=wire("app"),
    )
    name: bytes = field(
        metadata=wire(
            "name",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
