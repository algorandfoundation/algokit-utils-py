from dataclasses import dataclass

from algokit_algod_client.models import SimulationTransactionExecTrace

__all__ = ["SimulationTrace"]


@dataclass(slots=True)
class SimulationTrace:
    """Trace information from a simulated transaction.

    Aligned with TypeScript algokit-utils SimulationTrace structure.
    """

    trace: SimulationTransactionExecTrace | None
    """The execution trace of the transaction."""
    app_budget_consumed: int | None
    """Budget used during execution of an app call transaction."""
    logic_sig_budget_consumed: int | None
    """Budget used during execution of a logic sig transaction."""
    logs: list[bytes] | None
    """Logs from the transaction execution."""
    failure_message: str | None
    """The failure message if the transaction failed."""
