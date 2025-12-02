import json
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

# Default remote spec source
OAS_REPO_URL = "https://raw.githubusercontent.com/algorandfoundation/algokit-oas-generator"
DEFAULT_BRANCH = "main"


def resolve_spec(spec: str) -> Path:
    """Resolve a spec reference to a local path, downloading if needed.

    Supports:
        - Local paths: "api/specs/algod.oas3.json"
        - Remote URLs: "https://example.com/spec.json"
        - Shorthand: "oas://algod" or "oas://algod@branch"
    """
    # Shorthand: oas://algod or oas://algod@branch
    if spec.startswith("oas://"):
        name = spec[6:]
        branch = DEFAULT_BRANCH
        if "@" in name:
            name, branch = name.split("@", 1)
        url = f"{OAS_REPO_URL}/{branch}/specs/{name}.oas3.json"
        return _download_to_temp(url)

    # Remote URL
    if spec.startswith(("http://", "https://")):
        return _download_to_temp(spec)

    # Local path
    return Path(spec)


def _download_to_temp(url: str) -> Path:
    """Download URL to a temporary file and return the path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)  # noqa: SIM115
    try:
        urllib.request.urlretrieve(url, tmp.name)  # noqa: S310
    except urllib.error.URLError as e:
        msg = f"Failed to download spec from {url}: {e}"
        raise RuntimeError(msg) from e
    return Path(tmp.name)


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
