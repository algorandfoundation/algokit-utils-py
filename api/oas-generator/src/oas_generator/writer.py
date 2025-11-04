from collections.abc import Iterable
from pathlib import Path

_SENTINEL = "# AUTO-GENERATED: oas_generator"


def write_files(file_map: dict[Path, str], target_root: Path) -> None:
    target_root.mkdir(parents=True, exist_ok=True)
    legacy_manifest = target_root / ".generated-files"
    if legacy_manifest.exists():
        legacy_manifest.unlink()
    relative_map = _map_relative_paths(file_map, target_root)
    existing_generated = _discover_generated_files(target_root)
    new_files = set(relative_map.values())
    _remove_stale_files(target_root, existing_generated - new_files)
    for path, contents in file_map.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_ensure_sentinel(contents), encoding="utf-8")
    _remove_empty_directories(target_root)


def _map_relative_paths(file_map: dict[Path, str], target_root: Path) -> dict[Path, Path]:
    relative: dict[Path, Path] = {}
    for absolute_path in file_map:
        try:
            relative_path = absolute_path.relative_to(target_root)
        except ValueError as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"Generated file {absolute_path} is outside of target root {target_root}") from exc
        relative[absolute_path] = relative_path
    return relative


def _ensure_sentinel(contents: str) -> str:
    text = contents.lstrip("\ufeff")
    if _SENTINEL in text.splitlines()[:3]:
        return text
    if not text:
        return f"{_SENTINEL}\n"
    return f"{_SENTINEL}\n{text}"


def _discover_generated_files(target_root: Path) -> set[Path]:
    generated: set[Path] = set()
    if not target_root.exists():
        return generated
    for path in target_root.rglob("*"):
        if not path.is_file():
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                for _ in range(3):
                    line = handle.readline()
                    if not line:
                        break
                    if _SENTINEL in line:
                        generated.add(path.relative_to(target_root))
                        break
        except UnicodeDecodeError:
            continue
    return generated


def _remove_stale_files(target_root: Path, stale_paths: Iterable[Path]) -> None:
    for relative_path in sorted(stale_paths, key=lambda p: len(p.parts), reverse=True):
        absolute_path = target_root / relative_path
        if absolute_path.is_file():
            absolute_path.unlink(missing_ok=True)


def _remove_empty_directories(target_root: Path) -> None:
    directories = sorted(
        {path for path in target_root.rglob("*") if path.is_dir()},
        key=lambda p: len(p.parts),
        reverse=True,
    )
    for directory in directories:
        if directory == target_root:
            continue
        try:
            directory.rmdir()
        except OSError:
            continue
