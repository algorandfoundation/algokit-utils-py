from __future__ import annotations

from pathlib import Path


def write_files(file_map: dict[Path, str]) -> None:
    for path, contents in file_map.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
