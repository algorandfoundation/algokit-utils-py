from pathlib import Path
from typing import Any

from oas_generator.loader import SpecLoader
from oas_generator.models import ParsedSpec


class SpecParser:
    """Parse OpenAPI spec dictionaries into dataclasses used by the generator."""

    def __init__(self) -> None:
        self.loader = SpecLoader()

    def parse(self, path: Path) -> ParsedSpec:
        self.loader.load(path)
        return self.parse_dict(self.loader.data)

    def parse_dict(self, payload: dict[str, Any]) -> ParsedSpec:
        info = payload.get("info", {})
        return ParsedSpec(
            title=str(info.get("title", "AlgoKit Client")),
            version=str(info.get("version", "0.0.0")),
            description=info.get("description"),
            paths=payload.get("paths", {}) or {},
            components=payload.get("components", {}) or {},
        )
