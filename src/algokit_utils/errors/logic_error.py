import base64
import re
from collections.abc import Callable, Mapping, Sequence
from copy import copy
from typing import TYPE_CHECKING, TypedDict

from algokit_algod_client.models import (
    PendingTransactionResponse,
    SimulateTransactionResult,
    SimulationTransactionExecTrace,
)
from algokit_common import ProgramSourceMap

if TYPE_CHECKING:
    pass
__all__ = [
    "LogicError",
    "LogicErrorData",
    "create_simulate_traces_for_logic_error",
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
        source_map: "ProgramSourceMap | None",
        transaction_id: str,
        message: str,
        pc: int,
        logic_error: Exception | None = None,
        traces: list[SimulateTransactionResult] | None = None,
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


def create_simulate_traces_for_logic_error(simulate: object) -> list[SimulateTransactionResult]:
    """Extract simulation traces from a simulate response for logic error debugging.

    Args:
        simulate: An object with simulate_response and failed_at attributes.

    Returns:
        A list of SimulateTransactionResult objects extracted from the simulation response.
    """
    traces: list[SimulateTransactionResult] = []
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
        txn_results = txn_group.get("txn-results", [])

        if not isinstance(txn_results, Sequence):
            continue

        for txn_result in txn_results:
            if not isinstance(txn_result, Mapping):
                continue
            exec_trace_raw = txn_result.get("exec-trace")
            app_budget_consumed = txn_result.get("app-budget-consumed")
            logic_sig_budget_consumed = txn_result.get("logic-sig-budget-consumed")
            txn_result_inner = txn_result.get("txn-result", {})
            logs_raw = txn_result_inner.get("logs", []) if isinstance(txn_result_inner, Mapping) else []
            logs = [base64.b64decode(log) if isinstance(log, str) else log for log in logs_raw] if logs_raw else None

            # Create PendingTransactionResponse with logs for the SimulateTransactionResult
            # Note: txn is required but we don't have it from raw JSON, use placeholder
            pending_response = PendingTransactionResponse(
                txn=None,  # type: ignore[arg-type]  # placeholder for raw response parsing
                logs=logs,
            )

            # Create SimulateTransactionResult with available data
            traces.append(
                SimulateTransactionResult(
                    txn_result=pending_response,
                    app_budget_consumed=app_budget_consumed,
                    logic_sig_budget_consumed=logic_sig_budget_consumed,
                    exec_trace=exec_trace_raw if isinstance(exec_trace_raw, SimulationTransactionExecTrace) else None,
                )
            )
    return traces
