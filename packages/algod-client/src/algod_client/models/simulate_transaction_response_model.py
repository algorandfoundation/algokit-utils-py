from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .simulate_initial_states import SimulateInitialStates
from .simulate_trace_config import SimulateTraceConfig
from .simulate_transaction_group_result import SimulateTransactionGroupResult
from .simulation_eval_overrides import SimulationEvalOverrides


@dataclass(slots=True)
class SimulateTransactionResponseModel:
    last_round: int = field(
        metadata=wire("last-round"),
    )
    txn_groups: list[SimulateTransactionGroupResult] = field(
        metadata=wire(
            "txn-groups",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulateTransactionGroupResult, raw),
        ),
    )
    version: int = field(
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
