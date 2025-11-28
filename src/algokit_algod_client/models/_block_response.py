# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BlockResponse:
    block: dict[str, object] = field(
        metadata=wire("block"),
    )
    cert: dict[str, object] | None = field(
        default=None,
        metadata=wire("cert"),
    )
