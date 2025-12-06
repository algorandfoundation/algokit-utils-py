# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._application_state_schema import ApplicationStateSchema
from ._serde_helpers import decode_model_sequence, encode_model_sequence
from ._teal_key_value import TealKeyValue


@dataclass(slots=True)
class ApplicationLocalState:
    """
    Stores local state associated with an application.
    """

    schema: ApplicationStateSchema = field(
        metadata=nested("schema", lambda: ApplicationStateSchema, required=True),
    )
    id_: int = field(
        default=0,
        metadata=wire("id"),
    )
    key_value: list[TealKeyValue] | None = field(
        default=None,
        metadata=wire(
            "key-value",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: TealKeyValue, raw),
        ),
    )
