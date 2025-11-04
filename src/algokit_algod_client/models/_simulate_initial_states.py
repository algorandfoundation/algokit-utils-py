# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._application_initial_states import ApplicationInitialStates
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class SimulateInitialStates:
    """
    Initial states of resources that were accessed during simulation.
    """

    app_initial_states: list[ApplicationInitialStates] | None = field(
        default=None,
        metadata=wire(
            "app-initial-states",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationInitialStates, raw),
        ),
    )
