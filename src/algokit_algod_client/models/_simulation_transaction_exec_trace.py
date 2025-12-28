# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, decode_model_sequence, encode_bytes, encode_model_sequence
from ._simulation_opcode_trace_unit import SimulationOpcodeTraceUnit


@dataclass(slots=True)
class SimulationTransactionExecTrace:
    """
    The execution trace of calling an app or a logic sig, containing the inner app call
    trace in a recursive way.
    """

    approval_program_hash: bytes | None = field(
        default=None,
        metadata=wire(
            "approval-program-hash",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    approval_program_trace: list[SimulationOpcodeTraceUnit] | None = field(
        default=None,
        metadata=wire(
            "approval-program-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulationOpcodeTraceUnit, raw),
        ),
    )
    clear_state_program_hash: bytes | None = field(
        default=None,
        metadata=wire(
            "clear-state-program-hash",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    clear_state_program_trace: list[SimulationOpcodeTraceUnit] | None = field(
        default=None,
        metadata=wire(
            "clear-state-program-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulationOpcodeTraceUnit, raw),
        ),
    )
    clear_state_rollback: bool | None = field(
        default=None,
        metadata=wire("clear-state-rollback"),
    )
    clear_state_rollback_error: str | None = field(
        default=None,
        metadata=wire("clear-state-rollback-error"),
    )
    inner_trace: list["SimulationTransactionExecTrace"] | None = field(
        default=None,
        metadata=wire(
            "inner-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulationTransactionExecTrace, raw),
        ),
    )
    logic_sig_hash: bytes | None = field(
        default=None,
        metadata=wire(
            "logic-sig-hash",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    logic_sig_trace: list[SimulationOpcodeTraceUnit] | None = field(
        default=None,
        metadata=wire(
            "logic-sig-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulationOpcodeTraceUnit, raw),
        ),
    )
