# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .application_state_schema import ApplicationStateSchema
from .teal_key_value import TealKeyValue


@dataclass(slots=True)
class ApplicationParams:
    """
    Stores the global information associated with an application.
    """

    approval_program: bytes = field(
        metadata=wire("approval-program"),
    )
    clear_state_program: bytes = field(
        metadata=wire("clear-state-program"),
    )
    creator: str = field(
        metadata=wire("creator"),
    )
    extra_program_pages: int | None = field(
        default=None,
        metadata=wire("extra-program-pages"),
    )
    global_state: list[TealKeyValue] | None = field(
        default=None,
        metadata=wire(
            "global-state",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: TealKeyValue, raw),
        ),
    )
    global_state_schema: ApplicationStateSchema | None = field(
        default=None,
        metadata=nested("global-state-schema", lambda: ApplicationStateSchema),
    )
    local_state_schema: ApplicationStateSchema | None = field(
        default=None,
        metadata=nested("local-state-schema", lambda: ApplicationStateSchema),
    )
    version: int | None = field(
        default=None,
        metadata=wire("version"),
    )
