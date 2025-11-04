# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._box_descriptor import BoxDescriptor
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class GetApplicationBoxesResponseModel:
    boxes: list[BoxDescriptor] = field(
        metadata=wire(
            "boxes",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: BoxDescriptor, raw),
        ),
    )
