# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class StateProofVerifier:
    commitment: bytes | None = field(
        default=None,
        metadata=wire("commitment"),
    )
    key_lifetime: int | None = field(
        default=None,
        metadata=wire("key-lifetime"),
    )
