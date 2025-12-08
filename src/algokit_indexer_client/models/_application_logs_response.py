# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._application_log_data import ApplicationLogData
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class ApplicationLogsResponse:
    application_id: int = field(
        default=0,
        metadata=wire("application-id"),
    )
    current_round: int = field(
        default=0,
        metadata=wire("current-round"),
    )
    log_data: list[ApplicationLogData] | None = field(
        default=None,
        metadata=wire(
            "log-data",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationLogData, raw),
        ),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
