# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class GetSyncRoundResponse:
    round_: int = field(
        default=0,
        metadata=wire("round"),
    )
