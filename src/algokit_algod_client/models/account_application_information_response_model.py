# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .application_local_state import ApplicationLocalState
from .application_params import ApplicationParams


@dataclass(slots=True)
class AccountApplicationInformationResponseModel:
    round_: int = field(
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
