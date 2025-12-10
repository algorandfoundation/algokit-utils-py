"""Program validation utilities for TEAL bytecode.

This module provides sanity checks for compiled TEAL programs to help
detect common errors such as passing source code instead of bytecode,
or passing base64-encoded programs.
"""

import base64

from algokit_common.address import public_key_from_address


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
    if not program:
        raise ValueError("empty program")

    try:
        ascii_str = program.decode("ascii")
    except UnicodeDecodeError:
        # not ascii, probably bytecode
        return

    if any(not line.isprintable() for line in ascii_str.splitlines()):
        # not printable, probably bytecode
        return

    try:
        public_key_from_address(ascii_str)
    except (TypeError, ValueError):
        pass
    else:
        raise ValueError("requesting program bytes, get Algorand address")

    try:
        base64.b64decode(ascii_str)
    except (TypeError, ValueError):
        pass
    else:
        raise ValueError("program should not be b64 encoded")

    raise ValueError("program bytes are all ASCII printable characters, not looking like Teal byte code")
