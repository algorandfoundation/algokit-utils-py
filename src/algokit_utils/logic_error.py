import re
from copy import copy
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from algosdk.source_map import SourceMap as AlgoSourceMap

__all__ = [
    "LogicError",
    "parse_logic_error",
]

LOGIC_ERROR = (
    ".*transaction (?P<transaction_id>[A-Z0-9]+): "
    "logic eval error: (?P<message>.*). Details: pc=(?P<pc>[0-9]+), opcodes=.*"
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
        traces: list | None = None,
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
    1.) Providing template_values when creating the ApplicationClient, so a SourceMap can be obtained automatically OR
    2.) Set approval_source_map from a previously compiled approval program OR
    3.) Import a previously exported source map using import_source_map"""

        program_lines = copy(self.lines)
        program_lines[self.line_no] += "\t\t<-- Error"
        lines_before = max(0, self.line_no - lines)
        lines_after = min(len(program_lines), self.line_no + lines)
        return "\n\t" + "\n\t".join(program_lines[lines_before:lines_after])
