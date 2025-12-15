"""
Source map utilities for mapping PC values to TEAL source code lines.

Provides VLQ-encoded source map decoding per the Source Map Revision 3 spec.
"""

from dataclasses import dataclass
from typing import Any, Final, cast

# Source Map Revision 3 - the only supported version
# https://sourcemaps.info/spec.html
SOURCE_MAP_VERSION: Final[int] = 3


class SourceMapVersionError(Exception):
    """Raised when an unsupported source map version is encountered."""

    def __init__(self, version: int) -> None:
        super().__init__(f"unsupported source map version: {version}")


@dataclass
class SourceLocation:
    """Represents a location in source code.

    Attributes:
        line: The 0-based line number in the source file.
        column: The 0-based column number in the source file (optional).
    """

    line: int
    column: int | None = None


@dataclass
class PcLineLocation:
    """Represents a mapping from PC (program counter) to source location.

    Attributes:
        pc: The program counter value.
        line: The 0-based line number in the source file.
    """

    pc: int
    line: int


class ProgramSourceMap:
    """
    Decodes a VLQ-encoded source mapping between PC values and TEAL source code lines.
    Spec available here: https://sourcemaps.info/spec.html

    Args:
        source_map: source map JSON from algod compile endpoint

    Attributes:
        version: The source map version (must be 3).
        sources: List of source file names.
        mappings: The raw VLQ-encoded mappings string.
        pc_to_line: Mapping from program counter to source line number.
        line_to_pc: Mapping from source line number to list of program counters.

    Raises:
        SourceMapVersionError: If the source map version is not 3.

    Example:
        >>> from algokit_common import ProgramSourceMap
        >>> source_map_data = {"version": 3, "sources": ["main.teal"], "mappings": "..."}
        >>> source_map = ProgramSourceMap(source_map_data)
        >>> line = source_map.get_line_for_pc(10)
        >>> pcs = source_map.get_pcs_for_line(5)
    """

    def __init__(self, source_map: dict[str, Any]) -> None:
        self.version: int = source_map["version"]

        if self.version != SOURCE_MAP_VERSION:
            raise SourceMapVersionError(self.version)

        self.sources: list[str] = source_map["sources"]

        self.mappings: str = source_map["mappings"]

        pc_list = [_decode_int_value(raw_val) for raw_val in self.mappings.split(";")]

        self.pc_to_line: dict[int, int] = {}
        self.line_to_pc: dict[int, list[int]] = {}

        last_line = 0
        for index, line_delta in enumerate(pc_list):
            # line_delta is None if the line number has not changed
            # or if the line is empty
            if line_delta is not None:
                last_line = last_line + line_delta

            if last_line not in self.line_to_pc:
                self.line_to_pc[last_line] = []

            self.line_to_pc[last_line].append(index)
            self.pc_to_line[index] = last_line

    def get_line_for_pc(self, pc: int) -> int | None:
        """Get the source line number for a given program counter.

        Args:
            pc: The program counter value.

        Returns:
            The source line number, or None if not found.
        """
        return self.pc_to_line.get(pc, None)

    def get_pcs_for_line(self, line: int) -> list[int] | None:
        """Get the program counter values for a given source line.

        Args:
            line: The source line number.

        Returns:
            A list of program counter values, or None if not found.
        """
        return self.line_to_pc.get(line, None)


def _decode_int_value(value: str) -> int | None:
    """Decode a VLQ segment to extract the line delta.

    Mappings may have up to 5 segments:
    Third segment represents the zero-based starting line in the original source represented.
    """
    decoded_value = _base64vlq_decode(value)
    return decoded_value[2] if decoded_value else None


# Source taken from: https://gist.github.com/mjpieters/86b0d152bb51d5f5979346d11005588b
_b64chars = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_b64table: Final[list[int | None]] = [None] * (max(_b64chars) + 1)
for _i, _b in enumerate(_b64chars):
    _b64table[_b] = _i

_shiftsize, _flag, _mask = 5, 1 << 5, (1 << 5) - 1


def _base64vlq_decode(vlqval: str) -> tuple[int, ...]:
    """Decode Base64 VLQ value."""
    results = []
    shift = value = 0
    # use byte values and a table to go from base64 characters to integers
    for v in map(_b64table.__getitem__, vlqval.encode("ascii")):
        v = cast(int, v)  # force int type given context
        value += (v & _mask) << shift
        if v & _flag:
            shift += _shiftsize
            continue
        # determine sign and add to results
        results.append((value >> 1) * (-1 if value & 1 else 1))
        shift = value = 0
    return tuple(results)
