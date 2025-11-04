# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class TransactionSignatureMultisigSubsignature:
    public_key: bytes | None = field(
        default=None,
        metadata=wire("public-key"),
    )
    signature: bytes | None = field(
        default=None,
        metadata=wire("signature"),
    )
