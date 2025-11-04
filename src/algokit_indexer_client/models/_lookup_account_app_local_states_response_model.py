# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._application_local_state import ApplicationLocalState
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class LookupAccountAppLocalStatesResponseModel:
    apps_local_states: list[ApplicationLocalState] = field(
        metadata=wire(
            "apps-local-states",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationLocalState, raw),
        ),
    )
    current_round: int = field(
        metadata=wire("current-round"),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
