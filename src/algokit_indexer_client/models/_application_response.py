# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._application import Application


@dataclass(slots=True)
class ApplicationResponse:
    current_round: int = field(
        default=0,
        metadata=wire("current-round"),
    )
    application: Application | None = field(
        default=None,
        metadata=nested("application", lambda: Application),
    )
