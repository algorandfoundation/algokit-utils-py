import base64
import json
import logging
import typing
from dataclasses import dataclass
from pathlib import Path

from algosdk.encoding import checksum
from algosdk.source_map import SourceMap

from algokit_utils import deploy
from algokit_utils.config import config

if typing.TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient


logger = logging.getLogger(__name__)


@dataclass
class AVMDebuggerSourceMap:
    location: str
    program_hash: str

    # write to string that exports to json
    def __str__(self) -> str:
        return json.dumps({"sourcemap-location": self.location, "hash": self.program_hash})


def _upsert_debug_sourcemap(sourcemap: AVMDebuggerSourceMap) -> None:
    # load files from repository root directory
    if not config.project_root:
        logger.warning(
            f"Project root is not specified by user, skipping persisting sourcemaps \
                       for {sourcemap.program_hash}"
        )
        return

    sources_path = Path(str(config.project_root)) / ".algokit" / "debugger" / "sources.json"

    # check if exists
    if not sources_path.exists():
        # create empty file with empty json content, if folders don't exist, create them too
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text('{"txn-group-sources": []}')

    # load json
    try:
        sources = json.loads(sources_path.read_text())
    except Exception:
        sources = {"txn-group-sources": []}

    for source in sources["txn-group-sources"]:
        # if file not exists, remove from list
        if not Path(source["sourcemap-location"]).exists():
            sources["txn-group-sources"].remove(source)

    # add new source unless already exists
    if not any(
        source["sourcemap-location"] == sourcemap.location and source["hash"] == sourcemap.program_hash
        for source in sources["txn-group-sources"]
    ):
        sources["txn-group-sources"].append({"sourcemap-location": sourcemap.location, "hash": sourcemap.program_hash})
        # write back to file
        sources_path.write_text(json.dumps(sources))


def _build_avm_sourcemap(
    teal_content: str, app_name: str, file_name: str, output_path: Path, client: "AlgodClient"
) -> AVMDebuggerSourceMap:
    result: dict = client.compile(deploy.strip_comments(teal_content), source_map=True)
    raw_binary = base64.b64decode(result["result"])
    program_hash = base64.b64encode(checksum(raw_binary)).decode()  # type: ignore[no-untyped-call]
    source_map = SourceMap(result["sourcemap"]).__dict__

    source_map["sources"] = [file_name]

    # write source_map to file
    source_map_filename = f'{file_name.replace(".teal", "")}.tok.map'
    output = output_path / ".algokit" / "debugger" / app_name
    source_map_output = output / source_map_filename
    source_map_output.parent.mkdir(parents=True, exist_ok=True)
    source_map_output.write_text(json.dumps(source_map))
    source_output = output / file_name
    source_output.write_text(teal_content)

    # reload sources
    return AVMDebuggerSourceMap(str(source_map_output), program_hash)


def persist_sourcemaps(approval: str, clear: str, app_name: str, client: "AlgodClient") -> None:
    if not config.project_root:
        logger.warning(
            f"Project root is not specified by user, skipping persisting approval and clear\
                        sourcemaps for {app_name}"
        )
        return

    sources = [
        _build_avm_sourcemap(approval, app_name, "approval.teal", config.project_root, client),
        _build_avm_sourcemap(clear, app_name, "clear.teal", config.project_root, client),
    ]

    for source in sources:
        _upsert_debug_sourcemap(source)
