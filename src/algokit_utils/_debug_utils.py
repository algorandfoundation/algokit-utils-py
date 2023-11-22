import base64
import json
import logging
import typing
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    EmptySigner,
    SimulateAtomicTransactionResponse,
)
from algosdk.encoding import checksum
from algosdk.source_map import SourceMap
from algosdk.v2client.models import SimulateRequest, SimulateRequestTransactionGroup, SimulateTraceConfig

from algokit_utils import deploy

if typing.TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient

logger = logging.getLogger(__name__)

ALGOKIT_DIR = ".algokit"
DEBUGGER_DIR = "sourcemaps"
SOURCES_FILE = "avm.sources"
TRACES_FILE_EXT = ".avm.trace"
DEBUG_TRACES_DIR = "debug_traces"


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
        return cls(
            txn_group_sources=[
                AVMDebuggerSourceMapEntry(location=item["sourcemap-location"], program_hash=item["hash"])
                for item in data.get("txn-group-sources", [])
            ]
        )

    def to_dict(self) -> dict:
        return {"txn-group-sources": [json.loads(str(item)) for item in self.txn_group_sources]}


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


def _upsert_debug_sourcemaps(sourcemaps: list[AVMDebuggerSourceMapEntry], project_root: Path) -> None:
    sources_path = project_root / ALGOKIT_DIR / DEBUGGER_DIR / SOURCES_FILE
    sources = _load_or_create_sources(sources_path)

    for sourcemap in sourcemaps:
        if sourcemap not in sources.txn_group_sources:
            sources.txn_group_sources.append(sourcemap)

    with sources_path.open("w") as f:
        json.dump(sources.to_dict(), f)


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


def persist_sourcemaps(
    sources: list[PersistSourceMapInput],
    project_root: Path,
    client: "AlgodClient",
) -> None:
    sourcemaps = [
        _build_avm_sourcemap(source.teal, source.app_name, source.file_name, project_root, client) for source in sources
    ]

    _upsert_debug_sourcemaps(sourcemaps, project_root)


def simulate_response(atc: AtomicTransactionComposer, algod_client: "AlgodClient") -> SimulateAtomicTransactionResponse:
    unsigned_txn_groups = atc.build_group()
    empty_signer = EmptySigner()
    txn_list = [txn_group.txn for txn_group in unsigned_txn_groups]
    fake_signed_transactions = empty_signer.sign_transactions(txn_list, [])
    txn_group = [SimulateRequestTransactionGroup(txns=fake_signed_transactions)]
    trace_config = SimulateTraceConfig(enable=True, stack_change=True, scratch_change=True)

    simulate_request = SimulateRequest(
        txn_groups=txn_group, allow_more_logs=True, allow_empty_signatures=True, exec_trace_config=trace_config
    )
    return atc.simulate(algod_client, simulate_request)


def simulate_and_persist_response(
    atc: AtomicTransactionComposer, project_root: Path, algod_client: "AlgodClient"
) -> None:
    atc_to_simulate = atc.clone()
    for txn_with_sign in atc_to_simulate.txn_list:
        sp = algod_client.suggested_params()
        txn_with_sign.txn.first_valid_round = sp.first
        txn_with_sign.txn.last_valid_round = sp.last
        txn_with_sign.txn.genesis_hash = sp.gh
    response = simulate_response(atc_to_simulate, algod_client)
    txn_types = [
        txn_result["txn-results"][0]["txn-result"]["txn"]["txn"]["type"]
        for txn_result in response.simulate_response["txn-groups"]
    ]
    txn_types_count = {txn_type: txn_types.count(txn_type) for txn_type in set(txn_types)}
    txn_types_str = "_".join([f"{count}#{txn_type}" for txn_type, count in txn_types_count.items()])
    last_round = response.simulate_response["last-round"]
    output_file = (
        project_root
        / DEBUG_TRACES_DIR
        / f'{datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")}_lr{last_round}_{txn_types_str}{TRACES_FILE_EXT}'
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(response.simulate_response, indent=2))
