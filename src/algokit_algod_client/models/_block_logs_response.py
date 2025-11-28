# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._app_call_logs import AppCallLogs
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class BlockLogsResponse:
    logs: list[AppCallLogs] = field(
        default_factory=list,
        metadata=wire(
            "logs",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AppCallLogs, raw),
        ),
    )
