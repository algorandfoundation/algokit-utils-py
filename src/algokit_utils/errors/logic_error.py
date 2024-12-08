import dataclasses
import re
from copy import copy
from typing import TYPE_CHECKING, TypedDict

from algosdk.atomic_transaction_composer import (
    SimulateAtomicTransactionResponse,
)

if TYPE_CHECKING:
    from algosdk.source_map import SourceMap as AlgoSourceMap

__all__ = [
    "LogicError",
    "parse_logic_error",
]

LOGIC_ERROR = (
    ".*transaction (?P<transaction_id>[A-Z0-9]+): logic eval error: (?P<message>.*). Details: .*pc=(?P<pc>[0-9]+).*"
)

DEFAULT_BLAST_RADIUS = 5


class LogicErrorData(TypedDict):
    transaction_id: str
    message: str
    pc: int


@dataclasses.dataclass
class SimulationTrace:
    app_budget_added: int | None
    app_budget_consumed: int | None
    failure_message: str | None
    exec_trace: dict[str, object]


def parse_logic_error(
    error_str: str,
) -> LogicErrorData | None:
    match = re.match(LOGIC_ERROR, error_str)
    if match is None:
        return None

    return {
        "transaction_id": match.group("transaction_id"),
        "message": match.group("message"),
        "pc": int(match.group("pc")),
    }


class LogicError(Exception):
    _blast_radius = DEFAULT_BLAST_RADIUS

    def __init__(
        self,
        *,
        logic_error_str: str,
        program: str,
        source_map: "AlgoSourceMap | None",
        transaction_id: str,
        message: str,
        pc: int,
        logic_error: Exception | None = None,
        traces: list[SimulationTrace] | None = None,
        blast_radius: int | None = None,
    ):
        self.logic_error = logic_error
        self.logic_error_str = logic_error_str
        self.program = program
        self.source_map = source_map
        self.lines = program.split("\n")
        self.transaction_id = transaction_id
        self.message = message
        self.pc = pc
        self.traces = traces
        self.line_no = self.source_map.get_line_for_pc(self.pc) if self.source_map else None
        self._blast_radius = blast_radius or self._blast_radius

        if self.line_no and self.line_no > 0:
            start = max(0, self.line_no - self._blast_radius)
            stop = min(len(self.program), self.line_no + self._blast_radius)

            stack_lines = self.program.splitlines()[start:stop]

            middle_index = len(stack_lines) // 2
            stack_lines[middle_index] += " <--- Error"

            self.stack = "\n".join(stack_lines)

    def __str__(self) -> str:
        return (
            f"Txn {self.transaction_id} had error '{self.message}' at PC {self.pc}"
            + (":" if self.line_no is None else f" and Source Line {self.line_no}:")
            + f"\n{self.trace()}"
        )

    def trace(self, lines: int = 5) -> str:
        if self.line_no is None:
            return """
Could not determine TEAL source line for the error as no approval source map was provided, to receive a trace of the
error please provide an approval SourceMap. Either by:
    1.Providing template_values when creating the ApplicationClient, so a SourceMap can be obtained automatically OR
    2.Set approval_source_map from a previously compiled approval program OR
    3.Import a previously exported source map using import_source_map"""

        program_lines = copy(self.lines)
        program_lines[self.line_no] += "\t\t<-- Error"
        lines_before = max(0, self.line_no - lines)
        lines_after = min(len(program_lines), self.line_no + lines)
        return "\n\t" + "\n\t".join(program_lines[lines_before:lines_after])


def create_simulate_traces_for_logic_error(simulate: SimulateAtomicTransactionResponse) -> list[SimulationTrace]:
    traces = []
    if hasattr(simulate, "simulate_response") and hasattr(simulate, "failed_at") and simulate.failed_at:
        for txn_group in simulate.simulate_response["txn-groups"]:
            app_budget_added = txn_group.get("app-budget-added", None)
            app_budget_consumed = txn_group.get("app-budget-consumed", None)
            failure_message = txn_group.get("failure-message", None)
            txn_result = txn_group.get("txn-results", [{}])[0]
            exec_trace = txn_result.get("exec-trace", {})
            traces.append(
                SimulationTrace(
                    app_budget_added=app_budget_added,
                    app_budget_consumed=app_budget_consumed,
                    failure_message=failure_message,
                    exec_trace=exec_trace,
                )
            )
    return traces
