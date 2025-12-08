# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._application import Application
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class ApplicationsResponse:
    applications: list[Application] = field(
        default_factory=list,
        metadata=wire(
            "applications",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Application, raw),
        ),
    )
    current_round: int = field(
        default=0,
        metadata=wire("current-round"),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
