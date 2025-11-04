# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class TealCompileResponseModel:
    hash_: str = field(
        metadata=wire("hash"),
    )
    result: str = field(
        metadata=wire("result"),
    )
    sourcemap: dict[str, object] | None = field(
        default=None,
        metadata=wire("sourcemap"),
    )
