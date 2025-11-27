# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._eval_delta_key_value import EvalDeltaKeyValue
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class AccountStateDelta:
    """
    Application state delta.
    """

    address: str = field(
        default="",
        metadata=wire("address"),
    )
    delta: list[EvalDeltaKeyValue] = field(
        default_factory=list,
        metadata=wire(
            "delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: EvalDeltaKeyValue, raw),
        ),
    )
