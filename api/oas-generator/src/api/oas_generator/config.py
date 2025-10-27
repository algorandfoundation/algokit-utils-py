from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GeneratorConfig:
    """Configuration resolved from CLI arguments."""

    spec_path: Path
    output_root: Path
    package_name: str
    distribution_name: str
    template_root: Path | None = None
    description_override: str | None = None

    @property
    def target_package_dir(self) -> Path:
        """packages/<distribution>/src/<package>"""

        return self.output_root / self.distribution_name / "src" / self.package_name
