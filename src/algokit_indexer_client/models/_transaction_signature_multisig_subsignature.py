# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_fixed_bytes, encode_fixed_bytes


@dataclass(slots=True)
class TransactionSignatureMultisigSubsignature:
    public_key: bytes | None = field(
        default=None,
        metadata=wire(
            "public-key",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    signature: bytes | None = field(
        default=None,
        metadata=wire(
            "signature",
            encode=lambda v: encode_fixed_bytes(v, 64),
            decode=lambda raw: decode_fixed_bytes(raw, 64),
        ),
    )
