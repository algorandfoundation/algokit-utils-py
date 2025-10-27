from __future__ import annotations

import keyword
import re
from dataclasses import dataclass


_NON_WORD = re.compile(r"[^0-9a-zA-Z]+")
_LOWER_TO_UPPER = re.compile(r"([a-z0-9])([A-Z])")

_PY_RESERVED = set(keyword.kwlist) | {
    "self",
    "cls",
    "async",
    "await",
    "match",
    "case",
    "type",
    "format",
    "min",
    "max",
    "round",
    "next",
    "id",
}


@dataclass(slots=True)
class IdentifierSanitizer:
    """Deterministic naming helper shared across generator stages."""

    suffix: str = "_"

    def _words(self, raw: str) -> list[str]:
        cleaned = _NON_WORD.sub(" ", raw)
        spaced = _LOWER_TO_UPPER.sub(r"\1 \2", cleaned)
        parts = [part for part in spaced.strip().split() if part]
        return parts or ["value"]

    def pascal(self, raw: str) -> str:
        words = self._words(raw)
        return "".join(word.capitalize() for word in words)

    def camel(self, raw: str) -> str:
        pascal = self.pascal(raw)
        return pascal[0:1].lower() + pascal[1:] if pascal else pascal

    def snake(self, raw: str) -> str:
        words = self._words(raw)
        candidate = "_".join(word.lower() for word in words)
        if candidate in _PY_RESERVED:
            candidate = f"{candidate}{self.suffix}"
        return candidate

    def const(self, raw: str) -> str:
        return self.snake(raw).upper()

    def module(self, raw: str) -> str:
        return self.snake(raw)

    def distribution(self, package_name: str) -> str:
        return package_name.replace("_", "-")
