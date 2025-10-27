from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .application_kvstorage import ApplicationKvstorage


@dataclass(slots=True)
class ApplicationInitialStates:
    """
    An application's initial global/local/box states that were accessed during simulation.
    """

    id_: int = field(
        metadata=wire("id"),
    )
    app_boxes: ApplicationKvstorage | None = field(
        default=None,
        metadata=nested("app-boxes", lambda: ApplicationKvstorage),
    )
    app_globals: ApplicationKvstorage | None = field(
        default=None,
        metadata=nested("app-globals", lambda: ApplicationKvstorage),
    )
    app_locals: list[ApplicationKvstorage] | None = field(
        default=None,
        metadata=wire(
            "app-locals",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationKvstorage, raw),
        ),
    )
