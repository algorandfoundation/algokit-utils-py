from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .simulate_transaction_result import SimulateTransactionResult
from .simulate_unnamed_resources_accessed import SimulateUnnamedResourcesAccessed


@dataclass(slots=True)
class SimulateTransactionGroupResult:
    """
    Simulation result for an atomic transaction group
    """

    txn_results: list[SimulateTransactionResult] = field(
        metadata=wire(
            "txn-results",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulateTransactionResult, raw),
        ),
    )
    app_budget_added: int | None = field(
        default=None,
        metadata=wire("app-budget-added"),
    )
    app_budget_consumed: int | None = field(
        default=None,
        metadata=wire("app-budget-consumed"),
    )
    failed_at: list[int] | None = field(
        default=None,
        metadata=wire("failed-at"),
    )
    failure_message: str | None = field(
        default=None,
        metadata=wire("failure-message"),
    )
    unnamed_resources_accessed: SimulateUnnamedResourcesAccessed | None = field(
        default=None,
        metadata=nested("unnamed-resources-accessed", lambda: SimulateUnnamedResourcesAccessed),
    )
