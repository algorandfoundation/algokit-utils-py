# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class TransactionSignatureMultisigSubsignature:
    public_key: bytes | None = field(
        default=None,
        metadata=wire(
            "public-key",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    signature: bytes | None = field(
        default=None,
        metadata=wire(
            "signature",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
