"""Program validation utilities for TEAL bytecode.

This module provides sanity checks for compiled TEAL programs to help
detect common errors such as passing source code instead of bytecode,
or passing base64-encoded programs.
"""

import re

from algokit_common.address import public_key_from_address

# Regex pattern for valid base64 strings
_BASE64_REGEX = re.compile(r"^([0-9a-zA-Z+/]{4})*(([0-9a-zA-Z+/]{2}==)|([0-9a-zA-Z+/]{3}=))?$")

# ASCII character ordinals
_LINE_BREAK_ORD = ord("\n")
_BLANK_SPACE_ORD = ord(" ")
_TILDE_ORD = ord("~")


def _is_printable(x: int) -> bool:
    """Check if a byte value is a printable ASCII character (space to tilde)."""
    return _BLANK_SPACE_ORD <= x <= _TILDE_ORD


def _is_valid_address(address: str) -> bool:
    """Check if a string is a valid Algorand address.

    Args:
        address: The string to check.

    Returns:
        True if the string is a valid Algorand address, False otherwise.
    """
    try:
        public_key_from_address(address)
        return True
    except (ValueError, TypeError):
        return False


def sanity_check_program(program: bytes) -> None:
    """Perform sanity checks on a compiled TEAL program.

    This function validates that the provided bytes appear to be compiled
    TEAL bytecode rather than common mistakes like:
    - Empty program
    - An Algorand address string
    - A base64-encoded string
    - TEAL source code (ASCII text)

    Args:
        program: The compiled TEAL program bytes to validate.

    Raises:
        ValueError: If the program fails any sanity check:
            - "empty program" if the program is None or empty
            - "requesting program bytes, get Algorand address" if the bytes
              decode to a valid Algorand address
            - "program should not be b64 encoded" if the bytes appear to be
              a base64-encoded string
            - "program bytes are all ASCII printable characters, not looking
              like Teal byte code" if all bytes are printable ASCII
    """
    if not program or len(program) == 0:
        raise ValueError("empty program")

    # Check if all bytes are ASCII printable (newlines allowed)
    is_ascii_printable = all(byte == _LINE_BREAK_ORD or _is_printable(byte) for byte in program)

    if is_ascii_printable:
        program_str = program.decode("utf-8")

        if _is_valid_address(program_str):
            raise ValueError("requesting program bytes, get Algorand address")

        if _BASE64_REGEX.match(program_str):
            raise ValueError("program should not be b64 encoded")

        raise ValueError("program bytes are all ASCII printable characters, not looking like Teal byte code")
