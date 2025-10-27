from __future__ import annotations

from algokit_common import address_from_public_key, public_key_from_address


def encode_address(addr: str | None) -> bytes | None:
    if addr is None:
        return None
    return public_key_from_address(addr)


def decode_address(pk: bytes | None) -> str | None:
    if pk is None:
        return None
    return address_from_public_key(pk)


def encode_bytes(b: bytes | None) -> bytes | None:
    return b if b not in (None, b"") else None


def encode_int(n: int | None, *, keep_zero: bool = False) -> int | None:
    match n:
        case None:
            return None
        case 0 if not keep_zero:
            return None
        case _:
            return n


def encode_bool(v: bool | None) -> bool | None:
    return None if v in (None, False) else v


def encode_bytes_sequence(seq: tuple[bytes, ...] | None) -> list[bytes] | None:
    if not seq:
        return None
    return [bytes(item) for item in seq]


def encode_int_sequence(seq: tuple[int, ...] | None) -> list[int] | None:
    if not seq:
        return None
    return [int(item) for item in seq]


def decode_bytes_like(value: object | None) -> bytes | None:
    if isinstance(value, bytes | bytearray):
        return bytes(value)
    return None


def decode_int_like(value: object | None) -> int | None:
    match value:
        case None:
            return None
        case bool():
            return int(value)
        case int():
            return int(value)
        case _:
            return None


def omit_defaults_and_sort(value: object) -> object:
    if isinstance(value, dict):
        filtered = {
            k: omit_defaults_and_sort(v) for k, v in value.items() if not is_default_like(omit_defaults_and_sort(v))
        }
        return dict(sorted(filtered.items()))
    if isinstance(value, list | tuple):
        return [omit_defaults_and_sort(v) for v in value]
    return value


def is_default_like(value: object) -> bool:  # noqa: PLR0911
    match value:
        case None:
            return True
        case int() as i if i == 0:
            return True
        case str() as s if s == "":
            return True
        case (bytes() | bytearray()) as b if len(b) == 0:
            return True
        case list() as l if len(l) == 0:
            return True
        case dict() as d:
            # omit-empty-object
            return all(is_default_like(v) for v in d.values())
        case _:
            return False
