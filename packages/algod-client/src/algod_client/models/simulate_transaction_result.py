from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .pending_transaction_response import PendingTransactionResponse
from .simulate_unnamed_resources_accessed import SimulateUnnamedResourcesAccessed
from .simulation_transaction_exec_trace import SimulationTransactionExecTrace


@dataclass(slots=True)
class SimulateTransactionResult:
    """
    Simulation result for an individual transaction
    """

    txn_result: PendingTransactionResponse = field(
        metadata=nested("txn-result", lambda: PendingTransactionResponse),
    )
    app_budget_consumed: int | None = field(
        default=None,
        metadata=wire("app-budget-consumed"),
    )
    exec_trace: SimulationTransactionExecTrace | None = field(
        default=None,
        metadata=nested("exec-trace", lambda: SimulationTransactionExecTrace),
    )
    fixed_signer: str | None = field(
        default=None,
        metadata=wire("fixed-signer"),
    )
    logic_sig_budget_consumed: int | None = field(
        default=None,
        metadata=wire("logic-sig-budget-consumed"),
    )
    unnamed_resources_accessed: SimulateUnnamedResourcesAccessed | None = field(
        default=None,
        metadata=nested("unnamed-resources-accessed", lambda: SimulateUnnamedResourcesAccessed),
    )
