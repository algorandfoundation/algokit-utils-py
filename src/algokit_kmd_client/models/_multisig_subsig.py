# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class MultisigSubsig:
    """
    MultisigSubsig is a struct that holds a pair of public key and signatures
    signatures may be empty
    """

    public_key: bytes = field(
        default=b"",
        metadata=wire(
            "pk",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    signature: bytes | None = field(
        default=None,
        metadata=wire(
            "s",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
