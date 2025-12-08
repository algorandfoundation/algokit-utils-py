# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._application_state_operation import ApplicationStateOperation
from ._avm_value import AvmValue
from ._scratch_change import ScratchChange
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class SimulationOpcodeTraceUnit:
    """
    The set of trace information and effect from evaluating a single opcode.
    """

    pc: int = field(
        default=0,
        metadata=wire("pc"),
    )
    scratch_changes: list[ScratchChange] | None = field(
        default=None,
        metadata=wire(
            "scratch-changes",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ScratchChange, raw),
        ),
    )
    spawned_inners: list[int] | None = field(
        default=None,
        metadata=wire("spawned-inners"),
    )
    stack_additions: list[AvmValue] | None = field(
        default=None,
        metadata=wire(
            "stack-additions",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AvmValue, raw),
        ),
    )
    stack_pop_count: int | None = field(
        default=None,
        metadata=wire("stack-pop-count"),
    )
    state_changes: list[ApplicationStateOperation] | None = field(
        default=None,
        metadata=wire(
            "state-changes",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationStateOperation, raw),
        ),
    )
