from dataclasses import dataclass


@dataclass
class SimulationTrace:
    app_budget_added: int | None
    app_budget_consumed: int | None
    failure_message: str | None
    exec_trace: dict[str, object]
