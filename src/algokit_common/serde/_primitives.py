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
            return value
        case int():
            return int(value)
        case _:
            return None


_TYPE_PRIORITY = {int: 0, str: 1, bytes: 2}


def sort_msgpack_value(value: object) -> object:
    """
    Recursively sort msgpack values with canonical key ordering.

    Implements canonical msgpack encoding where map keys are ordered by type:
    - Integer keys first (sorted numerically)
    - String keys second (sorted lexicographically)
    - Binary keys third (sorted by byte value)

    This ensures deterministic, canonical msgpack encoding that matches
    the behavior of Algorand's protocol layer (Go's msgp library and Rust's rmpv).

    Args:
        value: A Python object (dict, list, or scalar) to sort recursively.

    Returns:
        The value with all dictionaries sorted according to msgpack canonical rules.
    """
    if isinstance(value, dict):
        return {
            k: sort_msgpack_value(v)
            for k, v in sorted(
                value.items(),
                key=lambda kv: (_TYPE_PRIORITY.get(type(kv[0]), 3), kv[0]),
            )
        }
    elif isinstance(value, list | tuple):
        return [sort_msgpack_value(v) for v in value]
    return value


def omit_defaults_and_sort(value: object) -> object:
    """
    Recursively omit default-like values and sort with canonical msgpack ordering.

    Combines two operations:
    1. Filters out default-like values (None, 0, "", empty bytes, empty collections)
    2. Sorts dictionaries by key using canonical msgpack ordering (int → str → bytes)

    This is used by to_wire_canonical() for protocol wire format encoding.
    """
    if isinstance(value, dict):
        filtered = {
            k: omit_defaults_and_sort(v) for k, v in value.items() if not is_default_like(omit_defaults_and_sort(v))
        }
        # Use sort_msgpack_value for canonical ordering instead of simple lexicographic sort
        return sort_msgpack_value(filtered)
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
