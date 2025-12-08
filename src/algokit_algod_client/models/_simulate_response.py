# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from ._simulate_initial_states import SimulateInitialStates
from ._simulate_trace_config import SimulateTraceConfig
from ._simulate_transaction_group_result import SimulateTransactionGroupResult
from ._simulation_eval_overrides import SimulationEvalOverrides


@dataclass(slots=True)
class SimulateResponse:
    last_round: int = field(
        default=0,
        metadata=wire("last-round"),
    )
    txn_groups: list[SimulateTransactionGroupResult] = field(
        default_factory=list,
        metadata=wire(
            "txn-groups",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulateTransactionGroupResult, raw),
        ),
    )
    version: int = field(
        default=0,
        metadata=wire("version"),
    )
    eval_overrides: SimulationEvalOverrides | None = field(
        default=None,
        metadata=nested("eval-overrides", lambda: SimulationEvalOverrides),
    )
    exec_trace_config: SimulateTraceConfig | None = field(
        default=None,
        metadata=nested("exec-trace-config", lambda: SimulateTraceConfig),
    )
    initial_states: SimulateInitialStates | None = field(
        default=None,
        metadata=nested("initial-states", lambda: SimulateInitialStates),
    )
