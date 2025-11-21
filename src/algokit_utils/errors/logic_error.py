import base64
import re
from collections.abc import Callable, Mapping, Sequence
from copy import copy
from typing import TYPE_CHECKING, TypedDict

from algokit_utils.models.simulate import SimulationTrace

if TYPE_CHECKING:
    from algokit_algosdk.source_map import SourceMap as AlgoSourceMap
__all__ = [
    "LogicError",
    "LogicErrorData",
    "parse_logic_error",
]


LOGIC_ERROR = (
    ".*transaction (?P<transaction_id>[A-Z0-9]+): logic eval error: (?P<message>.*). Details: .*pc=(?P<pc>[0-9]+).*"
)


class LogicErrorData(TypedDict):
    transaction_id: str
    message: str
    pc: int


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
        get_line_for_pc: Callable[[int], int | None] | None = None,
    ):
        self.logic_error = logic_error
        self.logic_error_str = logic_error_str
        try:
            self.program = base64.b64decode(program).decode("utf-8")
        except Exception:
            self.program = program
        self.source_map = source_map
        self.lines = self.program.split("\n")
        self.transaction_id = transaction_id
        self.message = message
        self.pc = pc
        self.traces = traces
        self.line_no = (
            self.source_map.get_line_for_pc(self.pc)
            if self.source_map
            else get_line_for_pc(self.pc)
            if get_line_for_pc
            else None
        )

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
    1.Providing template_values when creating the AppClient, so a SourceMap can be obtained automatically OR
    2.Set approval_source_map from a previously compiled approval program OR
    3.Import a previously exported source map using import_source_map"""

        program_lines = copy(self.lines)
        program_lines[self.line_no] += "\t\t<-- Error"
        lines_before = max(0, self.line_no - lines)
        lines_after = min(len(program_lines), self.line_no + lines)
        return "\n\t" + "\n\t".join(program_lines[lines_before:lines_after])


def create_simulate_traces_for_logic_error(simulate: object) -> list[SimulationTrace]:
    traces: list[SimulationTrace] = []
    simulate_response = getattr(simulate, "simulate_response", None)
    failed_at = getattr(simulate, "failed_at", None)

    if not failed_at or not isinstance(simulate_response, Mapping):
        return traces

    txn_groups = simulate_response.get("txn-groups", [])
    if not isinstance(txn_groups, Sequence):
        return traces

    for txn_group in txn_groups:
        if not isinstance(txn_group, Mapping):
            continue
        app_budget_added = txn_group.get("app-budget-added")
        app_budget_consumed = txn_group.get("app-budget-consumed")
        failure_message = txn_group.get("failure-message")
        txn_results = txn_group.get("txn-results", [])
        txn_result = txn_results[0] if isinstance(txn_results, Sequence) and txn_results else {}
        exec_trace_mapping = txn_result.get("exec-trace", {}) if isinstance(txn_result, Mapping) else {}
        exec_trace: dict[str, object] = {}
        if isinstance(exec_trace_mapping, Mapping):
            exec_trace = {str(key): value for key, value in exec_trace_mapping.items()}
        traces.append(
            SimulationTrace(
                app_budget_added=app_budget_added,
                app_budget_consumed=app_budget_consumed,
                failure_message=failure_message,
                exec_trace=exec_trace,
            )
        )
    return traces
