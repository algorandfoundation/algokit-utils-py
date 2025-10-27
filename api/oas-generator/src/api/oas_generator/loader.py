from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SpecLoader:
    """Lightweight OpenAPI specification loader."""

    def __init__(self) -> None:
        self._data: dict[str, Any] | None = None

    @property
    def data(self) -> dict[str, Any]:
        if self._data is None:
            msg = "Specification has not been loaded"
            raise RuntimeError(msg)
        return self._data

    def load(self, path: Path) -> None:
        if not path.exists():
            msg = f"Specification file not found: {path!s}"
            raise FileNotFoundError(msg)
        self._data = self._load_json(path)

    def _load_json(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
