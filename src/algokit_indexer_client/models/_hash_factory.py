# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class HashFactory:
    hash_type: int | None = field(
        default=None,
        metadata=wire("hash-type"),
    )
