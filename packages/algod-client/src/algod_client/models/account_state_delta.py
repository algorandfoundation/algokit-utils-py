from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .eval_delta_key_value import EvalDeltaKeyValue


@dataclass(slots=True)
class AccountStateDelta:
    """
    Application state delta.
    """

    address: str = field(
        metadata=wire("address"),
    )
    delta: list[EvalDeltaKeyValue] = field(
        metadata=wire(
            "delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: EvalDeltaKeyValue, raw),
        ),
    )
