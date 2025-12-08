# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class GetBlockTimeStampOffsetResponse:
    offset: int = field(
        default=0,
        metadata=wire("offset"),
    )
