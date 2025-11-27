# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from ._teal_value import TealValue


@dataclass(slots=True)
class DryrunState:
    """
    Stores the TEAL eval step data
    """

    line: int = field(
        default=0,
        metadata=wire("line"),
    )
    pc: int = field(
        default=0,
        metadata=wire("pc"),
    )
    stack: list[TealValue] = field(
        default_factory=list,
        metadata=wire(
            "stack",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: TealValue, raw),
        ),
    )
    error: str | None = field(
        default=None,
        metadata=wire("error"),
    )
    scratch: list[TealValue] | None = field(
        default=None,
        metadata=wire(
            "scratch",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: TealValue, raw),
        ),
    )
