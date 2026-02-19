# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._application_kv_storage import ApplicationKvStorage
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class ApplicationInitialStates:
    """
    An application's initial global/local/box states that were accessed during simulation.
    """

    id_: int = field(
        default=0,
        metadata=wire("id"),
    )
    app_boxes: ApplicationKvStorage | None = field(
        default=None,
        metadata=nested("app-boxes", lambda: ApplicationKvStorage),
    )
    app_globals: ApplicationKvStorage | None = field(
        default=None,
        metadata=nested("app-globals", lambda: ApplicationKvStorage),
    )
    app_locals: list[ApplicationKvStorage] | None = field(
        default=None,
        metadata=wire(
            "app-locals",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationKvStorage, raw),
        ),
    )
