# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class SignMultisigResponse:
    """
    SignMultisigResponse is the response to `POST /v1/multisig/sign`
    """

    multisig: bytes = field(
        default=b"",
        metadata=wire(
            "multisig",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
