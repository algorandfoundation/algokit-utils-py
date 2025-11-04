# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._app_call_logs import AppCallLogs
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class GetBlockLogsResponseModel:
    logs: list[AppCallLogs] = field(
        metadata=wire(
            "logs",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AppCallLogs, raw),
        ),
    )
