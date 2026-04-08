# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class SignProgramResponse:
    """
    SignProgramResponse is the response to `POST /v1/data/sign`
    """

    sig: bytes = field(
        default=b"",
        metadata=wire(
            "sig",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
