import base64
import json
import logging
import typing
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from algokit_common import ProgramSourceMap, sha512_256
from algokit_common.serde import to_wire
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.config import config
from algokit_utils.models.application import CompiledTeal
from algokit_utils.transactions.transaction_composer import SendTransactionComposerResults, TransactionComposer

if typing.TYPE_CHECKING:
    from algosdk.atomic_transaction_composer import SimulateAtomicTransactionResponse  # type: ignore[import-not-found]

    from algokit_algod_client import AlgodClient
else:
    SimulateAtomicTransactionResponse = typing.Any  # type: ignore[assignment]
    AlgodClient = typing.Any  # type: ignore[assignment]

logger = logging.getLogger(__name__)

ALGOKIT_DIR = ".algokit"
SOURCES_DIR = "sources"
SOURCES_FILE = "sources.avm.json"
TRACES_FILE_EXT = ".trace.avm.json"
DEBUG_TRACES_DIR = "debug_traces"
TEAL_FILE_EXT = ".teal"
TEAL_SOURCEMAP_EXT = ".teal.map"
TRACE_FILENAME_DATE_FORMAT = "%Y%m%d_%H%M%S"


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
        compiled_teal: CompiledTeal | None = None,
    ):
        self.compiled_teal = compiled_teal
        self.app_name = app_name
        self._raw_teal = raw_teal
        self._file_name = self.strip_teal_extension(file_name)

    @classmethod
    def from_raw_teal(cls, raw_teal: str, app_name: str, file_name: str) -> "PersistSourceMapInput":
        return cls(app_name, file_name, raw_teal=raw_teal)

    @classmethod
    def from_compiled_teal(cls, compiled_teal: CompiledTeal, app_name: str, file_name: str) -> "PersistSourceMapInput":
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


def _write_to_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _compile_raw_teal(raw_teal: str, client: AlgodClient) -> tuple[bytes, ProgramSourceMap, str]:
    teal_to_compile = AppManager.strip_teal_comments(raw_teal)
    compiled = client.teal_compile(teal_to_compile.encode("utf-8"), sourcemap=True)
    compiled_bytes = base64.b64decode(compiled.result)
    sourcemap_dict = to_wire(compiled.sourcemap) if compiled.sourcemap else {}
    return compiled_bytes, ProgramSourceMap(sourcemap_dict), raw_teal


def _build_avm_sourcemap(
    *,
    app_name: str,
    file_name: str,
    output_path: Path,
    client: AlgodClient,
    raw_teal: str | None = None,
    compiled_teal: CompiledTeal | None = None,
    with_sources: bool = True,
) -> AVMDebuggerSourceMapEntry:
    if not raw_teal and not compiled_teal:
        raise ValueError("Either raw teal or compiled teal must be provided")

    if isinstance(compiled_teal, CompiledTeal):
        program_hash = base64.b64encode(sha512_256(compiled_teal.compiled_base64_to_bytes)).decode()
        source_map = compiled_teal.source_map.__dict__ if compiled_teal.source_map else {}
        teal_content = compiled_teal.teal
    else:
        compiled_bytes, source_map_obj, teal_content = _compile_raw_teal(str(raw_teal), client)
        program_hash = base64.b64encode(sha512_256(compiled_bytes)).decode()
        source_map = source_map_obj.__dict__

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


def _summarize_txn_types(trace: dict[str, Any]) -> str:
    counts: dict[str, int] = {}
    for group in trace.get("txn-groups", []):
        for txn_result in group.get("txn-results", []):
            txn = txn_result.get("txn-result", {}).get("txn", {}).get("txn", {})
            txn_type = txn.get("type")
            if txn_type and not isinstance(txn_type, str):
                txn_type = getattr(txn_type, "value", str(txn_type))
            if not txn_type:
                continue
            counts[txn_type] = counts.get(txn_type, 0) + 1
    return "_".join(f"{count}{txn_type}" for txn_type, count in counts.items())


def _persist_simulation_trace(
    trace: dict[str, Any],
    project_root: Path,
    *,
    timestamp: datetime | None = None,
    buffer_size_mb: float | None = None,
) -> Path:
    project_root.mkdir(parents=True, exist_ok=True)
    trace_dir = project_root / DEBUG_TRACES_DIR
    trace_dir.mkdir(parents=True, exist_ok=True)

    now = timestamp or datetime.now(timezone.utc)
    last_round = trace.get("last-round", 0)
    txn_part = _summarize_txn_types(trace)
    filename = (
        f"{now.astimezone(timezone.utc).strftime(TRACE_FILENAME_DATE_FORMAT)}_lr{last_round}_{txn_part}"
        f"{TRACES_FILE_EXT}"
    )
    output_path = trace_dir / filename

    def _default_encoder(value: object) -> str:
        if isinstance(value, (bytes | bytearray | memoryview)):
            return base64.b64encode(bytes(value)).decode("utf-8")
        return getattr(value, "value", str(value))

    _write_to_file(output_path, json.dumps(trace, default=_default_encoder))

    if buffer_size_mb is not None:
        cleanup_old_trace_files(trace_dir, buffer_size_mb)

    return output_path


def _extract_simulation_trace_from_algokit(result: SendTransactionComposerResults) -> dict[str, Any]:
    if result.simulate_response is None:
        raise ValueError("No simulate_response available to persist")
    return to_wire(result.simulate_response)


def _extract_simulation_trace_from_atc(response: SimulateAtomicTransactionResponse) -> dict[str, Any]:
    # algosdk simulate responses are already dict-like
    return dict(response.simulate_response) if hasattr(response, "simulate_response") else dict(response)


def simulate_and_persist_response(
    composer: TransactionComposer | object,
    project_root: Path,
    algod: AlgodClient,
    *,
    buffer_size_mb: float | None = None,
    result: SendTransactionComposerResults | SimulateAtomicTransactionResponse | None = None,
) -> Path:
    """
    Run a simulation on the provided composer and persist the trace to disk.

    :param composer: Transaction composer (AlgoKit or algosdk AtomicTransactionComposer)
    :param project_root: Root directory where traces should be stored
    :param algod: Algod client to use for simulation
    :param buffer_size_mb: Optional buffer size to enforce via cleanup_old_trace_files
    :param result: Optional existing simulation result to persist instead of re-running simulation
    :return: Path to the persisted trace file
    :raises TypeError: If the composer does not implement a compatible ``simulate`` method
    """
    if result is None and isinstance(composer, TransactionComposer):
        result = composer.simulate(_persist_trace=False)
        trace = _extract_simulation_trace_from_algokit(result)
    elif result is None and hasattr(composer, "simulate"):
        result = composer.simulate(algod)
        trace = _extract_simulation_trace_from_atc(result)
    elif result is not None:
        trace = (
            _extract_simulation_trace_from_algokit(result)
            if isinstance(result, SendTransactionComposerResults)
            else _extract_simulation_trace_from_atc(result)
        )
    else:
        raise TypeError("Composer must support simulate()")

    effective_root = config.project_root or project_root
    effective_buffer = buffer_size_mb
    if config.trace_all and buffer_size_mb is None:
        effective_buffer = config.trace_buffer_size_mb

    return _persist_simulation_trace(
        trace,
        effective_root,
        buffer_size_mb=effective_buffer,
    )


def persist_sourcemaps(
    *,
    sources: list[PersistSourceMapInput],
    project_root: Path,
    client: AlgodClient,
    with_sources: bool = True,
) -> None:
    """
    Persist the sourcemaps for the given sources as an AlgoKit AVM Debugger compliant artifacts.

    :param sources: A list of PersistSourceMapInput objects.
    :param project_root: The root directory of the project.
    :param client: An AlgodClient instance for interacting with the Algorand blockchain.
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
