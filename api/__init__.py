"""Shared namespace for internal generator utilities."""

from __future__ import annotations

import pkgutil
from pathlib import Path

__path__ = pkgutil.extend_path(__path__, __name__)  # type: ignore[name-defined]

_HERE = Path(__file__).resolve().parent
_GENERATOR_API = _HERE / "oas-generator" / "src" / "api"
if _GENERATOR_API.exists():
    __path__.append(str(_GENERATOR_API))  # type: ignore[attr-defined]
