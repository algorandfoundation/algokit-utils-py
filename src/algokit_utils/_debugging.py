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
from algosdk.v2client.models import SimulateRequest, SimulateRequestTransactionGroup, SimulateTraceConfig

from algokit_utils._legacy_v2.common import Program
from algokit_utils.models.application import CompiledTeal

if typing.TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient

logger = logging.getLogger(__name__)

ALGOKIT_DIR = ".algokit"
SOURCES_DIR = "sources"
SOURCES_FILE = "sources.avm.json"
TRACES_FILE_EXT = ".trace.avm.json"
DEBUG_TRACES_DIR = "debug_traces"
TEAL_FILE_EXT = ".teal"
TEAL_SOURCEMAP_EXT = ".teal.map"


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
    def __init__(
        self,
        app_name: str,
        file_name: str,
        raw_teal: str | None = None,
        compiled_teal: CompiledTeal | Program | None = None,
    ):
        self.compiled_teal = compiled_teal
        self.app_name = app_name
        self._raw_teal = raw_teal
        self._file_name = self.strip_teal_extension(file_name)

    @classmethod
    def from_raw_teal(cls, raw_teal: str, app_name: str, file_name: str) -> "PersistSourceMapInput":
        return cls(app_name, file_name, raw_teal=raw_teal)

    @classmethod
    def from_compiled_teal(
        cls, compiled_teal: CompiledTeal | Program, app_name: str, file_name: str
    ) -> "PersistSourceMapInput":
        return cls(app_name, file_name, compiled_teal=compiled_teal)

    @property
    def raw_teal(self) -> str:
        if self._raw_teal:
            return self._raw_teal
        elif self.compiled_teal:
            return self.compiled_teal.teal
        else:
            raise ValueError("No teal content found")

    @property
    def file_name(self) -> str:
        return self._file_name

    @staticmethod
    def strip_teal_extension(file_name: str) -> str:
        if file_name.endswith(".teal"):
            return file_name[:-5]
        return file_name


def _load_or_create_sources(sources_path: Path) -> AVMDebuggerSourceMap:
    if not sources_path.exists():
        return AVMDebuggerSourceMap(txn_group_sources=[])

    with sources_path.open() as f:
        return AVMDebuggerSourceMap.from_dict(json.load(f))


def _write_to_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _build_avm_sourcemap(
    *,
    app_name: str,
    file_name: str,
    output_path: Path,
    client: "AlgodClient",
    raw_teal: str | None = None,
    compiled_teal: CompiledTeal | Program | None = None,
    with_sources: bool = True,
) -> AVMDebuggerSourceMapEntry:
    if not raw_teal and not compiled_teal:
        raise ValueError("Either raw teal or compiled teal must be provided")

    # Handle both legacy Program and new CompiledTeal
    if isinstance(compiled_teal, Program):
        program_hash = base64.b64encode(checksum(compiled_teal.raw_binary)).decode()
        source_map = compiled_teal.source_map.__dict__
        teal_content = compiled_teal.teal
    elif isinstance(compiled_teal, CompiledTeal):
        program_hash = base64.b64encode(checksum(compiled_teal.compiled_base64_to_bytes)).decode()
        source_map = compiled_teal.source_map.__dict__ if compiled_teal.source_map else {}
        teal_content = compiled_teal.teal
    else:
        # Handle raw TEAL case
        result = Program(str(raw_teal), client=client)
        program_hash = base64.b64encode(checksum(result.raw_binary)).decode()
        source_map = result.source_map.__dict__
        teal_content = result.teal

    source_map["sources"] = [f"{file_name}{TEAL_FILE_EXT}"] if with_sources else []

    output_dir_path = output_path / ALGOKIT_DIR / SOURCES_DIR / app_name
    source_map_output_path = output_dir_path / f"{file_name}{TEAL_SOURCEMAP_EXT}"
    teal_output_path = output_dir_path / f"{file_name}{TEAL_FILE_EXT}"
    _write_to_file(source_map_output_path, json.dumps(source_map))

    if with_sources:
        _write_to_file(teal_output_path, teal_content)

    return AVMDebuggerSourceMapEntry(str(source_map_output_path), program_hash)


def cleanup_old_trace_files(output_dir: Path, buffer_size_mb: float) -> None:
    """
    Cleanup old trace files if total size exceeds buffer size limit.

    Args:
        output_dir (Path): Directory containing trace files
        buffer_size_mb (float): Maximum allowed size in megabytes
    """
    total_size = sum(f.stat().st_size for f in output_dir.glob("*") if f.is_file())
    if total_size > buffer_size_mb * 1024 * 1024:
        sorted_files = sorted(output_dir.glob("*"), key=lambda p: p.stat().st_mtime)
        while total_size > buffer_size_mb * 1024 * 1024 and sorted_files:
            oldest_file = sorted_files.pop(0)
            total_size -= oldest_file.stat().st_size
            oldest_file.unlink()


def persist_sourcemaps(
    *,
    sources: list[PersistSourceMapInput],
    project_root: Path,
    client: "AlgodClient",
    with_sources: bool = True,
) -> None:
    """
    Persist the sourcemaps for the given sources as an AlgoKit AVM Debugger compliant artifacts.

    :param sources: A list of PersistSourceMapInput objects.
    :param project_root: The root directory of the project.
    :param client: An AlgodClient object for interacting with the Algorand blockchain.
    :param with_sources: If True, it will dump teal source files along with sourcemaps.
    """

    for source in sources:
        _build_avm_sourcemap(
            raw_teal=source.raw_teal,
            compiled_teal=source.compiled_teal,
            app_name=source.app_name,
            file_name=source.file_name,
            output_path=project_root,
            client=client,
            with_sources=with_sources,
        )


def simulate_response(
    atc: AtomicTransactionComposer,
    algod_client: "AlgodClient",
    allow_more_logs: bool | None = None,
    allow_empty_signatures: bool | None = None,
    allow_unnamed_resources: bool | None = None,
    extra_opcode_budget: int | None = None,
    exec_trace_config: SimulateTraceConfig | None = None,
    simulation_round: int | None = None,
) -> SimulateAtomicTransactionResponse:
    """Simulate atomic transaction group execution"""

    unsigned_txn_groups = atc.build_group()
    empty_signer = EmptySigner()
    txn_list = [txn_group.txn for txn_group in unsigned_txn_groups]
    fake_signed_transactions = empty_signer.sign_transactions(txn_list, [])
    txn_group = [SimulateRequestTransactionGroup(txns=fake_signed_transactions)]
    trace_config = SimulateTraceConfig(enable=True, stack_change=True, scratch_change=True, state_change=True)

    simulate_request = SimulateRequest(
        txn_groups=txn_group,
        allow_more_logs=allow_more_logs if allow_more_logs is not None else True,
        round=simulation_round,
        extra_opcode_budget=extra_opcode_budget if extra_opcode_budget is not None else 0,
        allow_unnamed_resources=allow_unnamed_resources if allow_unnamed_resources is not None else True,
        allow_empty_signatures=allow_empty_signatures if allow_empty_signatures is not None else True,
        exec_trace_config=exec_trace_config if exec_trace_config is not None else trace_config,
    )

    return atc.simulate(algod_client, simulate_request)


def simulate_and_persist_response(
    atc: AtomicTransactionComposer,
    project_root: Path,
    algod_client: "AlgodClient",
    buffer_size_mb: float = 256,
    allow_more_logs: bool | None = None,
    allow_empty_signatures: bool | None = None,
    allow_unnamed_resources: bool | None = None,
    extra_opcode_budget: int | None = None,
    exec_trace_config: SimulateTraceConfig | None = None,
    simulation_round: int | None = None,
) -> SimulateAtomicTransactionResponse:
    """Simulates atomic transactions and persists simulation response to a JSON file.

    Simulates the atomic transactions using the provided AtomicTransactionComposer and AlgodClient,
    then persists the simulation response to an AlgoKit AVM Debugger compliant JSON file.

    :param atc: AtomicTransactionComposer containing transactions to simulate and persist
    :param project_root: Root directory path of the project
    :param algod_client: Algorand client instance
    :param buffer_size_mb: Size of trace buffer in megabytes, defaults to 256
    :param allow_more_logs: Flag to allow additional logs, defaults to None
    :param allow_empty_signatures: Flag to allow empty signatures, defaults to None
    :param allow_unnamed_resources: Flag to allow unnamed resources, defaults to None
    :param extra_opcode_budget: Additional opcode budget, defaults to None
    :param exec_trace_config: Execution trace configuration, defaults to None
    :param simulation_round: Round number for simulation, defa  ults to None
    :return: Simulated response after persisting for AlgoKit AVM Debugger consumption
    """
    atc_to_simulate = atc.clone()
    sp = algod_client.suggested_params()

    for txn_with_sign in atc_to_simulate.txn_list:
        txn_with_sign.txn.first_valid_round = sp.first
        txn_with_sign.txn.last_valid_round = sp.last
        txn_with_sign.txn.genesis_hash = sp.gh

    response = simulate_response(
        atc_to_simulate,
        algod_client,
        allow_more_logs,
        allow_empty_signatures,
        allow_unnamed_resources,
        extra_opcode_budget,
        exec_trace_config,
        simulation_round,
    )
    txn_results = response.simulate_response["txn-groups"]

    txn_types = [
        txn["txn-result"]["txn"]["txn"]["type"] for txn_result in txn_results for txn in txn_result["txn-results"]
    ]
    txn_types_count = {}
    for txn_type in txn_types:
        if txn_type not in txn_types_count:
            txn_types_count[txn_type] = txn_types.count(txn_type)
    txn_types_str = "_".join([f"{count}{txn_type}" for txn_type, count in txn_types_count.items()])

    last_round = response.simulate_response["last-round"]
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = project_root / DEBUG_TRACES_DIR / f"{timestamp}_lr{last_round}_{txn_types_str}{TRACES_FILE_EXT}"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    cleanup_old_trace_files(output_file.parent, buffer_size_mb)
    output_file.write_text(json.dumps(response.simulate_response, indent=2))
    return response
