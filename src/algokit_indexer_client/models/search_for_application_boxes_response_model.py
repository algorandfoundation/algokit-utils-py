# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .box_descriptor import BoxDescriptor


@dataclass(slots=True)
class SearchForApplicationBoxesResponseModel:
    application_id: int = field(
        metadata=wire("application-id"),
    )
    boxes: list[BoxDescriptor] = field(
        metadata=wire(
            "boxes",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: BoxDescriptor, raw),
        ),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
