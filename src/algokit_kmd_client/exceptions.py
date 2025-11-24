# AUTO-GENERATED: oas_generator

from http import HTTPStatus
from json import JSONDecodeError, loads


class ApiError(RuntimeError):
    """Base exception for errors raised by generated clients."""


def _format_payload(payload: object) -> str | None:  # noqa: C901, PLR0912
    """Extract a human-friendly message from a payload."""
    if payload is None:
        return None

    text: str | None = None
    if isinstance(payload, (bytes | bytearray | memoryview)):
        try:
            text = bytes(payload).decode("utf-8", errors="ignore")
        except Exception:
            text = None
    if text is None:
        text = str(payload)

    result = text.strip()
    if not result:
        return None

    try:
        decoded = loads(result)
    except (JSONDecodeError, TypeError):
        return result

    if isinstance(decoded, dict):
        for key in ("message", "msg", "error", "detail", "description", "data"):
            value = decoded.get(key)
            if isinstance(value, str):
                candidate = value.strip()
                if candidate:
                    result = candidate
                    break

    if isinstance(decoded, list) and decoded:
        first = decoded[0]
        if isinstance(first, str):
            candidate = first.strip()
            if candidate:
                result = candidate

    return result


class UnexpectedStatusError(ApiError):
    def __init__(self, status_code: int, payload: object) -> None:
        message = _format_payload(payload)
        description = f" {message}" if message else ""
        super().__init__(f"Unexpected status code {status_code}{description}")
        self.status_code = HTTPStatus(status_code)
        self.payload = payload
