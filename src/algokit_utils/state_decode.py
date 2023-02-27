from base64 import b64decode
from typing import Any


def str_or_hex(v: bytes) -> str:
    decoded: str
    try:
        decoded = v.decode("utf-8")
    except UnicodeDecodeError:
        decoded = v.hex()

    return decoded


def decode_state(state: list[dict[str, Any]], *, raw: bool = False) -> dict[str | bytes, bytes | str | int | None]:
    decoded_state: dict[str | bytes, bytes | str | int | None] = {}

    for state_value in state:
        raw_key = b64decode(state_value["key"])

        key: str | bytes = raw_key if raw else str_or_hex(raw_key)
        val: str | bytes | int | None

        action = state_value["value"]["action"] if "action" in state_value["value"] else state_value["value"]["type"]

        match action:
            case 1:
                raw_val = b64decode(state_value["value"]["bytes"])
                val = raw_val if raw else str_or_hex(raw_val)
            case 2:
                val = state_value["value"]["uint"]
            case 3:
                val = None
            case _:
                raise NotImplementedError()

        decoded_state[key] = val
    return decoded_state
