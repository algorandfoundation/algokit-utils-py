import base64
import json
import logging
import typing
from dataclasses import asdict, dataclass, field
from pathlib import Path

from algosdk.encoding import checksum
from algosdk.source_map import SourceMap

from algokit_utils import deploy
from algokit_utils.config import config

if typing.TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient

logger = logging.getLogger(__name__)

ALGOKIT_DIR = ".algokit"
DEBUGGER_DIR = "sourcemaps"
SOURCES_FILE = "avm.sources"


@dataclass
class AVMDebuggerSourceMapEntry:
    location: str = field(metadata={"json": "sourcemap-location"})
    program_hash: str = field(metadata={"json": "hash"})

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AVMDebuggerSourceMapEntry):
            return self.location == other.location and self.program_hash == other.program_hash
        return False

    def __str__(self) -> str:
        return json.dumps({"sourcemap-location": self.location, "hash": self.program_hash})


@dataclass
class AVMDebuggerSourceMap:
    txn_group_sources: list[AVMDebuggerSourceMapEntry] = field(metadata={"json": "txn-group-sources"})

    @classmethod
    def from_dict(cls, data: dict) -> "AVMDebuggerSourceMap":
        return cls(txn_group_sources=[AVMDebuggerSourceMapEntry(**item) for item in data.get("txn_group_sources", [])])

    def __str__(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class PersistSourceMapInput:
    file_name: str
    teal: str
    app_name: str


def _load_or_create_sources(project_root: Path) -> AVMDebuggerSourceMap:
    sources_path = project_root / ALGOKIT_DIR / DEBUGGER_DIR / SOURCES_FILE
    if not sources_path.exists():
        return AVMDebuggerSourceMap(txn_group_sources=[])

    with sources_path.open() as f:
        return AVMDebuggerSourceMap.from_dict(json.load(f))


def _upsert_debug_sourcemaps(sourcemaps: list[AVMDebuggerSourceMapEntry]) -> None:
    if not config.project_root:
        logger.warning("Project root not specified; skipping sourcemap persistence")
        return

    sources_path = Path(str(config.project_root)) / ALGOKIT_DIR / DEBUGGER_DIR / SOURCES_FILE
    sources = _load_or_create_sources(sources_path)

    for sourcemap in sourcemaps:
        if sourcemap not in sources.txn_group_sources:
            sources.txn_group_sources.append(sourcemap)

    with sources_path.open("w") as f:
        json.dump(sources, f)


def _build_avm_sourcemap(
    teal_content: str, app_name: str, file_name: str, output_path: Path, client: "AlgodClient"
) -> AVMDebuggerSourceMapEntry:
    file_name = f"{file_name}.teal" if not file_name.endswith(".teal") else file_name
    result = client.compile(deploy.strip_comments(teal_content), source_map=True)
    program_hash = base64.b64encode(
        checksum(base64.b64decode(result["result"]))  # type: ignore[no-untyped-call]
    ).decode()
    source_map = SourceMap(result["sourcemap"]).__dict__
    source_map["sources"] = [file_name]

    output_dir = output_path / ALGOKIT_DIR / DEBUGGER_DIR / app_name
    source_map_output = output_dir / f'{file_name.replace(".teal", "")}.tok.map'
    source_map_output.parent.mkdir(parents=True, exist_ok=True)
    source_map_output.write_text(json.dumps(source_map))
    (output_dir / file_name).write_text(teal_content)

    return AVMDebuggerSourceMapEntry(str(source_map_output), program_hash)


def persist_sourcemaps(sources: list[PersistSourceMapInput], client: "AlgodClient") -> None:
    if not config.project_root:
        logger.warning("Project root not specified; skipping persisting sourcemaps")
        return

    sourcemaps = [
        _build_avm_sourcemap(source.teal, source.app_name, source.file_name, config.project_root, client)
        for source in sources
    ]

    _upsert_debug_sourcemaps(sourcemaps)
