# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class PostmultisigProgramSignResponse:
    """
    APIV1POSTMultisigProgramSignResponse is the response to `POST /v1/multisig/signdata`
    friendly:SignProgramMultisigResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
    multisig: bytes | None = field(
        default=None,
        metadata=wire(
            "multisig",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
