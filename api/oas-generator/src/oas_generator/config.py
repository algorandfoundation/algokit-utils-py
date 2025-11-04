from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GeneratorConfig:
    """Configuration resolved from CLI arguments."""

    spec_path: Path
    output_root: Path
    package_name: str
    template_root: Path | None = None
    description_override: str | None = None

    @property
    def target_package_dir(self) -> Path:
        """Fully qualified target directory for generated files."""

        return self.output_root.joinpath(*self.package_name.split("."))
