# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._application_local_state import ApplicationLocalState
from ._application_params import ApplicationParams


@dataclass(slots=True)
class AccountApplicationResponse:
    round_: int = field(
        default=0,
        metadata=wire("round"),
    )
    app_local_state: ApplicationLocalState | None = field(
        default=None,
        metadata=nested("app-local-state", lambda: ApplicationLocalState),
    )
    created_app: ApplicationParams | None = field(
        default=None,
        metadata=nested("created-app", lambda: ApplicationParams),
    )
