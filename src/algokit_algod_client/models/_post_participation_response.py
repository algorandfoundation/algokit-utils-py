# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostParticipationResponse:
    part_id: str = field(
        default="",
        metadata=wire("partId"),
    )
