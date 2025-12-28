# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_common.serde import nested, wire

from ._application_state_schema import ApplicationStateSchema
from ._serde_helpers import decode_bytes, decode_model_sequence, encode_bytes, encode_model_sequence
from ._teal_key_value import TealKeyValue


@dataclass(slots=True)
class ApplicationParams:
    """
    Stores the global information associated with an application.
    """

    approval_program: bytes = field(
        default=b"",
        metadata=wire(
            "approval-program",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    clear_state_program: bytes = field(
        default=b"",
        metadata=wire(
            "clear-state-program",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    creator: str = field(
        default=ZERO_ADDRESS,
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
