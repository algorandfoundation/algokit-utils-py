from __future__ import annotations

from typing import Protocol


class _SupportsSetItem(Protocol):
    def __setitem__(self, key: str, value: object) -> None: ...


def set_if(mapping: _SupportsSetItem, key: str, value: object | None) -> None:
    """Assign `value` to `mapping[key]` when the value is not ``None``."""
    if value is not None:
        mapping[key] = value


def require_bytes(value: object | None, *, field: str) -> bytes:
    """Ensure `value` is bytes-like, raising a helpful error otherwise."""
    if not isinstance(value, bytes | bytearray):
        raise ValueError(f"{field} must be bytes")
    return bytes(value)
