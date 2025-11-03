# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .application_state_schema import ApplicationStateSchema
from .teal_key_value import TealKeyValue


@dataclass(slots=True)
class ApplicationLocalState:
    """
    Stores local state associated with an application.
    """

    id_: int = field(
        metadata=wire("id"),
    )
    schema: ApplicationStateSchema = field(
        metadata=nested("schema", lambda: ApplicationStateSchema),
    )
    key_value: list[TealKeyValue] | None = field(
        default=None,
        metadata=wire(
            "key-value",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: TealKeyValue, raw),
        ),
    )
