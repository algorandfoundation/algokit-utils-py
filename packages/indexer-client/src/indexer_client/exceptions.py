from __future__ import annotations

from http import HTTPStatus


class ApiError(RuntimeError):
    """Base exception for errors raised by generated clients."""


class UnexpectedStatusError(ApiError):
    def __init__(self, status_code: int, payload: object) -> None:
        super().__init__(f"Unexpected status code: {status_code}")
        self.status_code = HTTPStatus(status_code)
        self.payload = payload
