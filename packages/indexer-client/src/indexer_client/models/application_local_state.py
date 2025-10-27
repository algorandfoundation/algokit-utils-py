from __future__ import annotations

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
    closed_out_at_round: int | None = field(
        default=None,
        metadata=wire("closed-out-at-round"),
    )
    deleted: bool | None = field(
        default=None,
        metadata=wire("deleted"),
    )
    key_value: list[TealKeyValue] | None = field(
        default=None,
        metadata=wire(
            "key-value",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: TealKeyValue, raw),
        ),
    )
    opted_in_at_round: int | None = field(
        default=None,
        metadata=wire("opted-in-at-round"),
    )
