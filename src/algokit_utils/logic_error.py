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
    "TransactionPool.Remember: transaction (?P<transaction_id>[A-Z0-9]+): "
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
        logic_error: Exception,
        program: str,
        source_map: "AlgoSourceMap",
        transaction_id: str,
        message: str,
        pc: int,
    ):
        self.logic_error = logic_error
        self.logic_error_str = str(logic_error)
        self.program = program
        self.source_map = source_map
        self.lines = program.split("\n")
        self.transaction_id = transaction_id
        self.message = message
        self.pc = pc

        line = self.source_map.get_line_for_pc(self.pc)
        self.line_no = line if line is not None else 0

    def __str__(self) -> str:
        return (
            f"Txn {self.transaction_id} had error '{self.message}' at PC {self.pc} and Source Line {self.line_no}: "
            f"\n\n\t{self.trace()}"
        )

    def trace(self, lines: int = 5) -> str:
        program_lines = copy(self.lines)
        program_lines[self.line_no] += "\t\t<-- Error"
        lines_before = max(0, self.line_no - lines)
        lines_after = min(len(program_lines), self.line_no + lines)
        return "\n\t".join(program_lines[lines_before:lines_after])
