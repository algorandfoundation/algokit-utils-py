"""Python port of ``transaction_asserts.ts`` stubs.

Functions in this module will gradually replace their TypeScript
counterparts. For now they raise ``NotImplementedError`` to make the
missing coverage explicit when individual tests are enabled.
"""

from __future__ import annotations

from typing import Any


class PendingPort(NotImplementedError):
    """Raised when a TypeScript helper has not yet been ported."""


def _pending(name: str) -> PendingPort:
    return PendingPort(f"TODO: port {name} from TypeScript suite")


def assert_example(label: str, test_data: Any) -> None:
    raise _pending("assert_example")


def assert_transaction_id(label: str, test_data: Any) -> None:
    raise _pending("assert_transaction_id")


def assert_encoded_transaction_type(label: str, test_data: Any) -> None:
    raise _pending("assert_encoded_transaction_type")


def assert_decode_without_prefix(label: str, test_data: Any) -> None:
    raise _pending("assert_decode_without_prefix")


def assert_decode_with_prefix(label: str, test_data: Any) -> None:
    raise _pending("assert_decode_with_prefix")


def assert_encode_with_auth_address(label: str, test_data: Any) -> None:
    raise _pending("assert_encode_with_auth_address")


def assert_encode_with_signature(label: str, test_data: Any) -> None:
    raise _pending("assert_encode_with_signature")


def assert_encode(label: str, test_data: Any) -> None:
    raise _pending("assert_encode")


def assert_assign_fee(label: str, test_data: Any) -> None:
    raise _pending("assert_assign_fee")


def assert_multisig_example(label: str, test_data: Any) -> None:
    raise _pending("assert_multisig_example")
