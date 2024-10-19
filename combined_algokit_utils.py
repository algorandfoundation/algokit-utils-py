# === File: algokit_utils/_debugging.py ===
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
from deprecated import deprecated

from algokit_utils.common import Program

if typing.TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient

logger = logging.getLogger(__name__)

ALGOKIT_DIR = ".algokit"
SOURCES_DIR = "sources"
SOURCES_FILE = "sources.avm.json"
TRACES_FILE_EXT = ".trace.avm.json"
DEBUG_TRACES_DIR = "debug_traces"
TEAL_FILE_EXT = ".teal"
TEAL_SOURCEMAP_EXT = ".teal.tok.map"


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
        self, app_name: str, file_name: str, raw_teal: str | None = None, compiled_teal: Program | None = None
    ):
        self.compiled_teal = compiled_teal
        self.app_name = app_name
        self._raw_teal = raw_teal
        self._file_name = self.strip_teal_extension(file_name)

    @classmethod
    def from_raw_teal(cls, raw_teal: str, app_name: str, file_name: str) -> "PersistSourceMapInput":
        return cls(app_name, file_name, raw_teal=raw_teal)

    @classmethod
    def from_compiled_teal(cls, compiled_teal: Program, app_name: str, file_name: str) -> "PersistSourceMapInput":
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


def _upsert_debug_sourcemaps(sourcemaps: list[AVMDebuggerSourceMapEntry], project_root: Path) -> None:
    """
    This function updates or inserts debug sourcemaps. If path in the sourcemap during iteration leads to non
    existing file, removes it. Otherwise upserts.

    Args:
        sourcemaps (list[AVMDebuggerSourceMapEntry]): A list of AVMDebuggerSourceMapEntry objects.
        project_root (Path): The root directory of the project.

    Returns:
        None
    """

    sources_path = project_root / ALGOKIT_DIR / SOURCES_DIR / SOURCES_FILE
    sources = _load_or_create_sources(sources_path)

    for sourcemap in sourcemaps:
        source_file_path = Path(sourcemap.location)
        if not source_file_path.exists() and sourcemap in sources.txn_group_sources:
            sources.txn_group_sources.remove(sourcemap)
        elif source_file_path.exists():
            if sourcemap not in sources.txn_group_sources:
                sources.txn_group_sources.append(sourcemap)
            else:
                index = sources.txn_group_sources.index(sourcemap)
                sources.txn_group_sources[index] = sourcemap

    with sources_path.open("w") as f:
        json.dump(sources.to_dict(), f)


def _write_to_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _build_avm_sourcemap(  # noqa: PLR0913
    *,
    app_name: str,
    file_name: str,
    output_path: Path,
    client: "AlgodClient",
    raw_teal: str | None = None,
    compiled_teal: Program | None = None,
    with_sources: bool = True,
) -> AVMDebuggerSourceMapEntry:
    if not raw_teal and not compiled_teal:
        raise ValueError("Either raw teal or compiled teal must be provided")

    result = compiled_teal if compiled_teal else Program(str(raw_teal), client=client)
    program_hash = base64.b64encode(
        checksum(result.raw_binary)  # type: ignore[no-untyped-call]
    ).decode()
    source_map = result.source_map.__dict__
    source_map["sources"] = [f"{file_name}{TEAL_FILE_EXT}"] if with_sources else []

    output_dir_path = output_path / ALGOKIT_DIR / SOURCES_DIR / app_name
    source_map_output_path = output_dir_path / f"{file_name}{TEAL_SOURCEMAP_EXT}"
    teal_output_path = output_dir_path / f"{file_name}{TEAL_FILE_EXT}"
    _write_to_file(source_map_output_path, json.dumps(source_map))

    if with_sources:
        _write_to_file(teal_output_path, result.teal)

    return AVMDebuggerSourceMapEntry(str(source_map_output_path), program_hash)


@deprecated(
    reason="Use latest version of `AlgoKit AVM Debugger` VSCode extension instead. "
    "It will automatically manage your sourcemaps.",
    version="3.0.0",
)
def persist_sourcemaps(
    *,
    sources: list[PersistSourceMapInput],
    project_root: Path,
    client: "AlgodClient",
    with_sources: bool = True,
    persist_mappings: bool = False,
) -> None:
    """
    Persist the sourcemaps for the given sources as an AlgoKit AVM Debugger compliant artifacts.
    Args:
        sources (list[PersistSourceMapInput]): A list of PersistSourceMapInput objects.
        project_root (Path): The root directory of the project.
        client (AlgodClient): An AlgodClient object for interacting with the Algorand blockchain.
        with_sources (bool): If True, it will dump teal source files along with sourcemaps.
        Default is True, as needed by an AlgoKit AVM debugger.
        persist_mappings (bool): Enables legacy behavior of persisting the `sources.avm.json` mappings to
        the project root. Default is False, given that the AlgoKit AVM VSCode extension will manage the mappings.
    """

    sourcemaps = [
        _build_avm_sourcemap(
            raw_teal=source.raw_teal,
            compiled_teal=source.compiled_teal,
            app_name=source.app_name,
            file_name=source.file_name,
            output_path=project_root,
            client=client,
            with_sources=with_sources,
        )
        for source in sources
    ]

    if persist_mappings:
        _upsert_debug_sourcemaps(sourcemaps, project_root)


def simulate_response(atc: AtomicTransactionComposer, algod_client: "AlgodClient") -> SimulateAtomicTransactionResponse:
    """
    Simulate and fetch response for the given AtomicTransactionComposer and AlgodClient.

    Args:
        atc (AtomicTransactionComposer): An AtomicTransactionComposer object.
        algod_client (AlgodClient): An AlgodClient object for interacting with the Algorand blockchain.

    Returns:
        SimulateAtomicTransactionResponse: The simulated response.
    """

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
    atc: AtomicTransactionComposer, project_root: Path, algod_client: "AlgodClient", buffer_size_mb: float = 256
) -> SimulateAtomicTransactionResponse:
    """
    Simulates the atomic transactions using the provided `AtomicTransactionComposer` object and `AlgodClient` object,
    and persists the simulation response to an AlgoKit AVM Debugger compliant JSON file.

    :param atc: An `AtomicTransactionComposer` object representing the atomic transactions to be
    simulated and persisted.
    :param project_root: A `Path` object representing the root directory of the project.
    :param algod_client: An `AlgodClient` object representing the Algorand client.
    :param buffer_size_mb: The size of the trace buffer in megabytes. Defaults to 256mb.
    :return: None

    Returns:
        SimulateAtomicTransactionResponse: The simulated response after persisting it
        for AlgoKit AVM Debugger consumption.
    """
    atc_to_simulate = atc.clone()
    sp = algod_client.suggested_params()

    for txn_with_sign in atc_to_simulate.txn_list:
        txn_with_sign.txn.first_valid_round = sp.first
        txn_with_sign.txn.last_valid_round = sp.last
        txn_with_sign.txn.genesis_hash = sp.gh

    response = simulate_response(atc_to_simulate, algod_client)
    txn_results = response.simulate_response["txn-groups"]

    txn_types = [txn_result["txn-results"][0]["txn-result"]["txn"]["txn"]["type"] for txn_result in txn_results]
    txn_types_count = {txn_type: txn_types.count(txn_type) for txn_type in set(txn_types)}
    txn_types_str = "_".join([f"{count}#{txn_type}" for txn_type, count in txn_types_count.items()])

    last_round = response.simulate_response["last-round"]
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = project_root / DEBUG_TRACES_DIR / f"{timestamp}_lr{last_round}_{txn_types_str}{TRACES_FILE_EXT}"

    output_file.parent.mkdir(parents=True, exist_ok=True)

    # cleanup old files if buffer size is exceeded
    total_size = sum(f.stat().st_size for f in output_file.parent.glob("*") if f.is_file())
    if total_size > buffer_size_mb * 1024 * 1024:
        sorted_files = sorted(output_file.parent.glob("*"), key=lambda p: p.stat().st_mtime)
        while total_size > buffer_size_mb * 1024 * 1024:
            oldest_file = sorted_files.pop(0)
            total_size -= oldest_file.stat().st_size
            oldest_file.unlink()

    output_file.write_text(json.dumps(response.simulate_response, indent=2))
    return response

# === File: algokit_utils/config.py ===
import logging
import os
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)

# Environment variable to override the project root
ALGOKIT_PROJECT_ROOT = os.getenv("ALGOKIT_PROJECT_ROOT")
ALGOKIT_CONFIG_FILENAME = ".algokit.toml"


class UpdatableConfig:
    """Class to manage and update configuration settings for the AlgoKit project.

    Attributes:
        debug (bool): Indicates whether debug mode is enabled.
        project_root (Path | None): The path to the project root directory.
        trace_all (bool): Indicates whether to trace all operations.
        trace_buffer_size_mb (int): The size of the trace buffer in megabytes.
        max_search_depth (int): The maximum depth to search for a specific file.
    """

    def __init__(self) -> None:
        self._debug: bool = False
        self._project_root: Path | None = None
        self._trace_all: bool = False
        self._trace_buffer_size_mb: int | float = 256  # megabytes
        self._max_search_depth: int = 10
        self._configure_project_root()

    def _configure_project_root(self) -> None:
        """Configures the project root by searching for a specific file within a depth limit."""
        current_path = Path(__file__).resolve()
        for _ in range(self._max_search_depth):
            logger.debug(f"Searching in: {current_path}")
            if (current_path / ALGOKIT_CONFIG_FILENAME).exists():
                self._project_root = current_path
                break
            current_path = current_path.parent

    @property
    def debug(self) -> bool:
        """Returns the debug status."""
        return self._debug

    @property
    def project_root(self) -> Path | None:
        """Returns the project root path."""
        return self._project_root

    @property
    def trace_all(self) -> bool:
        """Indicates whether to store simulation traces for all operations."""
        return self._trace_all

    @property
    def trace_buffer_size_mb(self) -> int | float:
        """Returns the size of the trace buffer in megabytes."""
        return self._trace_buffer_size_mb

    def with_debug(self, func: Callable[[], str | None]) -> None:
        """Executes a function with debug mode temporarily enabled."""
        original_debug = self._debug
        try:
            self._debug = True
            func()
        finally:
            self._debug = original_debug

    def configure(  # noqa: PLR0913
        self,
        *,
        debug: bool,
        project_root: Path | None = None,
        trace_all: bool = False,
        trace_buffer_size_mb: float = 256,
        max_search_depth: int = 10,
    ) -> None:
        """
        Configures various settings for the application.
        Please note, when `project_root` is not specified, by default config will attempt to find the `algokit.toml` by
        scanning the parent directories according to the `max_search_depth` parameter.
        Alternatively value can also be set via the `ALGOKIT_PROJECT_ROOT` environment variable.
        If you are executing the config from an algokit compliant project, you can simply call
        `config.configure(debug=True)`.

        Args:
            debug (bool): Indicates whether debug mode is enabled.
            project_root (Path | None, optional): The path to the project root directory. Defaults to None.
            trace_all (bool, optional): Indicates whether to trace all operations. Defaults to False. Which implies that
                only the operations that are failed will be traced by default.
            trace_buffer_size_mb (float, optional): The size of the trace buffer in megabytes. Defaults to 512mb.
            max_search_depth (int, optional): The maximum depth to search for a specific file. Defaults to 10.

        Returns:
            None
        """

        self._debug = debug

        if project_root:
            self._project_root = project_root.resolve(strict=True)
        elif debug and ALGOKIT_PROJECT_ROOT:
            self._project_root = Path(ALGOKIT_PROJECT_ROOT).resolve(strict=True)

        self._trace_all = trace_all
        self._trace_buffer_size_mb = trace_buffer_size_mb
        self._max_search_depth = max_search_depth


config = UpdatableConfig()

# === File: algokit_utils/deploy.py ===
import base64
import dataclasses
import json
import logging
import re
from collections.abc import Iterable, Mapping, Sequence
from enum import Enum
from typing import TYPE_CHECKING, TypeAlias, TypedDict

from algosdk import transaction
from algosdk.atomic_transaction_composer import AtomicTransactionComposer, TransactionSigner
from algosdk.logic import get_application_address
from algosdk.transaction import StateSchema

from algokit_utils.application_specification import (
    ApplicationSpecification,
    CallConfig,
    MethodConfigDict,
    OnCompleteActionName,
)
from algokit_utils.models import (
    ABIArgsDict,
    ABIMethod,
    Account,
    CreateCallParameters,
    TransactionResponse,
)

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient
    from algosdk.v2client.indexer import IndexerClient

    from algokit_utils.application_client import ApplicationClient


__all__ = [
    "UPDATABLE_TEMPLATE_NAME",
    "DELETABLE_TEMPLATE_NAME",
    "NOTE_PREFIX",
    "ABICallArgs",
    "ABICreateCallArgs",
    "ABICallArgsDict",
    "ABICreateCallArgsDict",
    "DeploymentFailedError",
    "AppReference",
    "AppDeployMetaData",
    "AppMetaData",
    "AppLookup",
    "DeployCallArgs",
    "DeployCreateCallArgs",
    "DeployCallArgsDict",
    "DeployCreateCallArgsDict",
    "Deployer",
    "DeployResponse",
    "OnUpdate",
    "OnSchemaBreak",
    "OperationPerformed",
    "TemplateValueDict",
    "TemplateValueMapping",
    "get_app_id_from_tx_id",
    "get_creator_apps",
    "replace_template_variables",
]

logger = logging.getLogger(__name__)

DEFAULT_INDEXER_MAX_API_RESOURCES_PER_ACCOUNT = 1000
_UPDATABLE = "UPDATABLE"
_DELETABLE = "DELETABLE"
UPDATABLE_TEMPLATE_NAME = f"TMPL_{_UPDATABLE}"
"""Template variable name used to control if a smart contract is updatable or not at deployment"""
DELETABLE_TEMPLATE_NAME = f"TMPL_{_DELETABLE}"
"""Template variable name used to control if a smart contract is deletable or not at deployment"""
_TOKEN_PATTERN = re.compile(r"TMPL_[A-Z_]+")
TemplateValue: TypeAlias = int | str | bytes
TemplateValueDict: TypeAlias = dict[str, TemplateValue]
"""Dictionary of `dict[str, int | str | bytes]` representing template variable names and values"""
TemplateValueMapping: TypeAlias = Mapping[str, TemplateValue]
"""Mapping of `str` to `int | str | bytes` representing template variable names and values"""

NOTE_PREFIX = "ALGOKIT_DEPLOYER:j"
"""ARC-0002 compliant note prefix for algokit_utils deployed applications"""
# This prefix is also used to filter for parsable transaction notes in get_creator_apps.
# However, as the note is base64 encoded first we need to consider it's base64 representation.
# When base64 encoding bytes, 3 bytes are stored in every 4 characters.
# So then we don't need to worry about the padding/changing characters of the prefix if it was followed by
# additional characters, assert the NOTE_PREFIX length is a multiple of 3.
assert len(NOTE_PREFIX) % 3 == 0


class DeploymentFailedError(Exception):
    pass


@dataclasses.dataclass
class AppReference:
    """Information about an Algorand app"""

    app_id: int
    app_address: str


@dataclasses.dataclass
class AppDeployMetaData:
    """Metadata about an application stored in a transaction note during creation.

    The note is serialized as JSON and prefixed with {py:data}`NOTE_PREFIX` and stored in the transaction note field
    as part of {py:meth}`ApplicationClient.deploy`
    """

    name: str
    version: str
    deletable: bool | None
    updatable: bool | None

    @staticmethod
    def from_json(value: str) -> "AppDeployMetaData":
        json_value: dict = json.loads(value)
        json_value.setdefault("deletable", None)
        json_value.setdefault("updatable", None)
        return AppDeployMetaData(**json_value)

    @classmethod
    def from_b64(cls: type["AppDeployMetaData"], b64: str) -> "AppDeployMetaData":
        return cls.decode(base64.b64decode(b64))

    @classmethod
    def decode(cls: type["AppDeployMetaData"], value: bytes) -> "AppDeployMetaData":
        note = value.decode("utf-8")
        assert note.startswith(NOTE_PREFIX)
        return cls.from_json(note[len(NOTE_PREFIX) :])

    def encode(self) -> bytes:
        json_str = json.dumps(self.__dict__)
        return f"{NOTE_PREFIX}{json_str}".encode()


@dataclasses.dataclass
class AppMetaData(AppReference, AppDeployMetaData):
    """Metadata about a deployed app"""

    created_round: int
    updated_round: int
    created_metadata: AppDeployMetaData
    deleted: bool


@dataclasses.dataclass
class AppLookup:
    """Cache of {py:class}`AppMetaData` for a specific `creator`

    Can be used as an argument to {py:class}`ApplicationClient` to reduce the number of calls when deploying multiple
    apps or discovering multiple app_ids
    """

    creator: str
    apps: dict[str, AppMetaData] = dataclasses.field(default_factory=dict)


def _sort_by_round(txn: dict) -> tuple[int, int]:
    confirmed = txn["confirmed-round"]
    offset = txn["intra-round-offset"]
    return confirmed, offset


def _parse_note(metadata_b64: str | None) -> AppDeployMetaData | None:
    if not metadata_b64:
        return None
    # noinspection PyBroadException
    try:
        return AppDeployMetaData.from_b64(metadata_b64)
    except Exception:
        return None


def get_creator_apps(indexer: "IndexerClient", creator_account: Account | str) -> AppLookup:
    """Returns a mapping of Application names to {py:class}`AppMetaData` for all Applications created by specified
    creator that have a transaction note containing {py:class}`AppDeployMetaData`
    """
    apps: dict[str, AppMetaData] = {}

    creator_address = creator_account if isinstance(creator_account, str) else creator_account.address
    token = None
    # TODO: paginated indexer call instead of N + 1 calls
    while True:
        response = indexer.lookup_account_application_by_creator(
            creator_address, limit=DEFAULT_INDEXER_MAX_API_RESOURCES_PER_ACCOUNT, next_page=token
        )  # type: ignore[no-untyped-call]
        if "message" in response:  # an error occurred
            raise Exception(f"Error querying applications for {creator_address}: {response}")
        for app in response["applications"]:
            app_id = app["id"]
            app_created_at_round = app["created-at-round"]
            app_deleted = app.get("deleted", False)
            search_transactions_response = indexer.search_transactions(
                min_round=app_created_at_round,
                txn_type="appl",
                application_id=app_id,
                address=creator_address,
                address_role="sender",
                note_prefix=NOTE_PREFIX.encode("utf-8"),
            )  # type: ignore[no-untyped-call]
            transactions: list[dict] = search_transactions_response["transactions"]
            if not transactions:
                continue

            created_transaction = next(
                t
                for t in transactions
                if t["application-transaction"]["application-id"] == 0 and t["sender"] == creator_address
            )

            transactions.sort(key=_sort_by_round, reverse=True)
            latest_transaction = transactions[0]
            app_updated_at_round = latest_transaction["confirmed-round"]

            create_metadata = _parse_note(created_transaction.get("note"))
            update_metadata = _parse_note(latest_transaction.get("note"))

            if create_metadata and create_metadata.name:
                apps[create_metadata.name] = AppMetaData(
                    app_id=app_id,
                    app_address=get_application_address(app_id),
                    created_metadata=create_metadata,
                    created_round=app_created_at_round,
                    **(update_metadata or create_metadata).__dict__,
                    updated_round=app_updated_at_round,
                    deleted=app_deleted,
                )

        token = response.get("next-token")
        if not token:
            break

    return AppLookup(creator_address, apps)


def _state_schema(schema: dict[str, int]) -> StateSchema:
    return StateSchema(schema.get("num-uint", 0), schema.get("num-byte-slice", 0))  # type: ignore[no-untyped-call]


def _describe_schema_breaks(prefix: str, from_schema: StateSchema, to_schema: StateSchema) -> Iterable[str]:
    if to_schema.num_uints > from_schema.num_uints:
        yield f"{prefix} uints increased from {from_schema.num_uints} to {to_schema.num_uints}"
    if to_schema.num_byte_slices > from_schema.num_byte_slices:
        yield f"{prefix} byte slices increased from {from_schema.num_byte_slices} to {to_schema.num_byte_slices}"


@dataclasses.dataclass(kw_only=True)
class AppChanges:
    app_updated: bool
    schema_breaking_change: bool
    schema_change_description: str | None


def check_for_app_changes(  # noqa: PLR0913
    algod_client: "AlgodClient",
    *,
    new_approval: bytes,
    new_clear: bytes,
    new_global_schema: StateSchema,
    new_local_schema: StateSchema,
    app_id: int,
) -> AppChanges:
    application_info = algod_client.application_info(app_id)
    assert isinstance(application_info, dict)
    application_create_params = application_info["params"]

    current_approval = base64.b64decode(application_create_params["approval-program"])
    current_clear = base64.b64decode(application_create_params["clear-state-program"])
    current_global_schema = _state_schema(application_create_params["global-state-schema"])
    current_local_schema = _state_schema(application_create_params["local-state-schema"])

    app_updated = current_approval != new_approval or current_clear != new_clear

    schema_changes: list[str] = []
    schema_changes.extend(_describe_schema_breaks("Global", current_global_schema, new_global_schema))
    schema_changes.extend(_describe_schema_breaks("Local", current_local_schema, new_local_schema))

    return AppChanges(
        app_updated=app_updated,
        schema_breaking_change=bool(schema_changes),
        schema_change_description=", ".join(schema_changes),
    )


def _is_valid_token_character(char: str) -> bool:
    return char.isalnum() or char == "_"


def _replace_template_variable(program_lines: list[str], template_variable: str, value: str) -> tuple[list[str], int]:
    result: list[str] = []
    match_count = 0
    token = f"TMPL_{template_variable}"
    token_idx_offset = len(value) - len(token)
    for line in program_lines:
        comment_idx = _find_unquoted_string(line, "//")
        if comment_idx is None:
            comment_idx = len(line)
        code = line[:comment_idx]
        comment = line[comment_idx:]
        trailing_idx = 0
        while True:
            token_idx = _find_template_token(code, token, trailing_idx)
            if token_idx is None:
                break

            trailing_idx = token_idx + len(token)
            prefix = code[:token_idx]
            suffix = code[trailing_idx:]
            code = f"{prefix}{value}{suffix}"
            match_count += 1
            trailing_idx += token_idx_offset
        result.append(code + comment)
    return result, match_count


def add_deploy_template_variables(
    template_values: TemplateValueDict, allow_update: bool | None, allow_delete: bool | None
) -> None:
    if allow_update is not None:
        template_values[_UPDATABLE] = int(allow_update)
    if allow_delete is not None:
        template_values[_DELETABLE] = int(allow_delete)


def _find_unquoted_string(line: str, token: str, start: int = 0, end: int = -1) -> int | None:
    """Find the first string within a line of TEAL. Only matches outside of quotes and base64 are returned.
    Returns None if not found"""

    if end < 0:
        end = len(line)
    idx = start
    in_quotes = in_base64 = False
    while idx < end:
        current_char = line[idx]
        match current_char:
            # enter base64
            case " " | "(" if not in_quotes and _last_token_base64(line, idx):
                in_base64 = True
            # exit base64
            case " " | ")" if not in_quotes and in_base64:
                in_base64 = False
            # escaped char
            case "\\" if in_quotes:
                # skip next character
                idx += 1
            # quote boundary
            case '"':
                in_quotes = not in_quotes
            # can test for match
            case _ if not in_quotes and not in_base64 and line.startswith(token, idx):
                # only match if not in quotes and string matches
                return idx
        idx += 1
    return None


def _last_token_base64(line: str, idx: int) -> bool:
    try:
        *_, last = line[:idx].split()
    except ValueError:
        return False
    return last in ("base64", "b64")


def _find_template_token(line: str, token: str, start: int = 0, end: int = -1) -> int | None:
    """Find the first template token within a line of TEAL. Only matches outside of quotes are returned.
    Only full token matches are returned, i.e. TMPL_STR will not match against TMPL_STRING
    Returns None if not found"""
    if end < 0:
        end = len(line)

    idx = start
    while idx < end:
        token_idx = _find_unquoted_string(line, token, idx, end)
        if token_idx is None:
            break
        trailing_idx = token_idx + len(token)
        if (token_idx == 0 or not _is_valid_token_character(line[token_idx - 1])) and (  # word boundary at start
            trailing_idx >= len(line) or not _is_valid_token_character(line[trailing_idx])  # word boundary at end
        ):
            return token_idx
        idx = trailing_idx
    return None


def _strip_comment(line: str) -> str:
    comment_idx = _find_unquoted_string(line, "//")
    if comment_idx is None:
        return line
    return line[:comment_idx].rstrip()


def strip_comments(program: str) -> str:
    return "\n".join(_strip_comment(line) for line in program.splitlines())


def _has_token(program_without_comments: str, token: str) -> bool:
    for line in program_without_comments.splitlines():
        token_idx = _find_template_token(line, token)
        if token_idx is not None:
            return True
    return False


def _find_tokens(stripped_approval_program: str) -> list[str]:
    return _TOKEN_PATTERN.findall(stripped_approval_program)


def check_template_variables(approval_program: str, template_values: TemplateValueDict) -> None:
    approval_program = strip_comments(approval_program)
    if _has_token(approval_program, UPDATABLE_TEMPLATE_NAME) and _UPDATABLE not in template_values:
        raise DeploymentFailedError(
            "allow_update must be specified if deploy time configuration of update is being used"
        )
    if _has_token(approval_program, DELETABLE_TEMPLATE_NAME) and _DELETABLE not in template_values:
        raise DeploymentFailedError(
            "allow_delete must be specified if deploy time configuration of delete is being used"
        )
    all_tokens = _find_tokens(approval_program)
    missing_values = [token for token in all_tokens if token[len("TMPL_") :] not in template_values]
    if missing_values:
        raise DeploymentFailedError(f"The following template values were not provided: {', '.join(missing_values)}")

    for template_variable_name in template_values:
        tmpl_variable = f"TMPL_{template_variable_name}"
        if not _has_token(approval_program, tmpl_variable):
            if template_variable_name == _UPDATABLE:
                raise DeploymentFailedError(
                    "allow_update must only be specified if deploy time configuration of update is being used"
                )
            if template_variable_name == _DELETABLE:
                raise DeploymentFailedError(
                    "allow_delete must only be specified if deploy time configuration of delete is being used"
                )
            logger.warning(f"{tmpl_variable} not found in approval program, but variable was provided")


def replace_template_variables(program: str, template_values: TemplateValueMapping) -> str:
    """Replaces `TMPL_*` variables in `program` with `template_values`

    ```{note}
    `template_values` keys should *NOT* be prefixed with `TMPL_`
    ```
    """
    program_lines = program.splitlines()
    for template_variable_name, template_value in template_values.items():
        match template_value:
            case int():
                value = str(template_value)
            case str():
                value = "0x" + template_value.encode("utf-8").hex()
            case bytes():
                value = "0x" + template_value.hex()
            case _:
                raise DeploymentFailedError(
                    f"Unexpected template value type {template_variable_name}: {template_value.__class__}"
                )

        program_lines, matches = _replace_template_variable(program_lines, template_variable_name, value)

    return "\n".join(program_lines)


def has_template_vars(app_spec: ApplicationSpecification) -> bool:
    return "TMPL_" in strip_comments(app_spec.approval_program) or "TMPL_" in strip_comments(app_spec.clear_program)


def get_deploy_control(
    app_spec: ApplicationSpecification, template_var: str, on_complete: transaction.OnComplete
) -> bool | None:
    if template_var not in strip_comments(app_spec.approval_program):
        return None
    return get_call_config(app_spec.bare_call_config, on_complete) != CallConfig.NEVER or any(
        h for h in app_spec.hints.values() if get_call_config(h.call_config, on_complete) != CallConfig.NEVER
    )


def get_call_config(method_config: MethodConfigDict, on_complete: transaction.OnComplete) -> CallConfig:
    def get(key: OnCompleteActionName) -> CallConfig:
        return method_config.get(key, CallConfig.NEVER)

    match on_complete:
        case transaction.OnComplete.NoOpOC:
            return get("no_op")
        case transaction.OnComplete.UpdateApplicationOC:
            return get("update_application")
        case transaction.OnComplete.DeleteApplicationOC:
            return get("delete_application")
        case transaction.OnComplete.OptInOC:
            return get("opt_in")
        case transaction.OnComplete.CloseOutOC:
            return get("close_out")
        case transaction.OnComplete.ClearStateOC:
            return get("clear_state")


class OnUpdate(Enum):
    """Action to take if an Application has been updated"""

    Fail = 0
    """Fail the deployment"""
    UpdateApp = 1
    """Update the Application with the new approval and clear programs"""
    ReplaceApp = 2
    """Create a new Application and delete the old Application in a single transaction"""
    AppendApp = 3
    """Create a new application"""


class OnSchemaBreak(Enum):
    """Action to take if an Application's schema has breaking changes"""

    Fail = 0
    """Fail the deployment"""
    ReplaceApp = 2
    """Create a new Application and delete the old Application in a single transaction"""
    AppendApp = 3
    """Create a new Application"""


class OperationPerformed(Enum):
    """Describes the actions taken during deployment"""

    Nothing = 0
    """An existing Application was found"""
    Create = 1
    """No existing Application was found, created a new Application"""
    Update = 2
    """An existing Application was found, but was out of date, updated to latest version"""
    Replace = 3
    """An existing Application was found, but was out of date, created a new Application and deleted the original"""


@dataclasses.dataclass(kw_only=True)
class DeployResponse:
    """Describes the action taken during deployment, related transactions and the {py:class}`AppMetaData`"""

    app: AppMetaData
    create_response: TransactionResponse | None = None
    delete_response: TransactionResponse | None = None
    update_response: TransactionResponse | None = None
    action_taken: OperationPerformed = OperationPerformed.Nothing


@dataclasses.dataclass(kw_only=True)
class DeployCallArgs:
    """Parameters used to update or delete an application when calling
    {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    suggested_params: transaction.SuggestedParams | None = None
    lease: bytes | str | None = None
    accounts: list[str] | None = None
    foreign_apps: list[int] | None = None
    foreign_assets: list[int] | None = None
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]] | None = None
    rekey_to: str | None = None


@dataclasses.dataclass(kw_only=True)
class ABICall:
    method: ABIMethod | bool | None = None
    args: ABIArgsDict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(kw_only=True)
class DeployCreateCallArgs(DeployCallArgs):
    """Parameters used to create an application when calling {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    extra_pages: int | None = None
    on_complete: transaction.OnComplete | None = None


@dataclasses.dataclass(kw_only=True)
class ABICallArgs(DeployCallArgs, ABICall):
    """ABI Parameters used to update or delete an application when calling
    {py:meth}`~algokit_utils.ApplicationClient.deploy`"""


@dataclasses.dataclass(kw_only=True)
class ABICreateCallArgs(DeployCreateCallArgs, ABICall):
    """ABI Parameters used to create an application when calling {py:meth}`~algokit_utils.ApplicationClient.deploy`"""


class DeployCallArgsDict(TypedDict, total=False):
    """Parameters used to update or delete an application when calling
    {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    suggested_params: transaction.SuggestedParams
    lease: bytes | str
    accounts: list[str]
    foreign_apps: list[int]
    foreign_assets: list[int]
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]]
    rekey_to: str


class ABICallArgsDict(DeployCallArgsDict, TypedDict, total=False):
    """ABI Parameters used to update or delete an application when calling
    {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    method: ABIMethod | bool
    args: ABIArgsDict


class DeployCreateCallArgsDict(DeployCallArgsDict, TypedDict, total=False):
    """Parameters used to create an application when calling {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    extra_pages: int | None
    on_complete: transaction.OnComplete


class ABICreateCallArgsDict(DeployCreateCallArgsDict, TypedDict, total=False):
    """ABI Parameters used to create an application when calling {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    method: ABIMethod | bool
    args: ABIArgsDict


@dataclasses.dataclass(kw_only=True)
class Deployer:
    app_client: "ApplicationClient"
    creator: str
    signer: TransactionSigner
    sender: str
    existing_app_metadata_or_reference: AppReference | AppMetaData
    new_app_metadata: AppDeployMetaData
    on_update: OnUpdate
    on_schema_break: OnSchemaBreak
    create_args: ABICreateCallArgs | ABICreateCallArgsDict | DeployCreateCallArgs | None
    update_args: ABICallArgs | ABICallArgsDict | DeployCallArgs | None
    delete_args: ABICallArgs | ABICallArgsDict | DeployCallArgs | None

    def deploy(self) -> DeployResponse:
        """Ensures app associated with app client's creator is present and up to date"""
        assert self.app_client.approval
        assert self.app_client.clear

        if self.existing_app_metadata_or_reference.app_id == 0:
            logger.info(f"{self.new_app_metadata.name} not found in {self.creator} account, deploying app.")
            return self._create_app()

        assert isinstance(self.existing_app_metadata_or_reference, AppMetaData)
        logger.debug(
            f"{self.existing_app_metadata_or_reference.name} found in {self.creator} account, "
            f"with app id {self.existing_app_metadata_or_reference.app_id}, "
            f"version={self.existing_app_metadata_or_reference.version}."
        )

        app_changes = check_for_app_changes(
            self.app_client.algod_client,
            new_approval=self.app_client.approval.raw_binary,
            new_clear=self.app_client.clear.raw_binary,
            new_global_schema=self.app_client.app_spec.global_state_schema,
            new_local_schema=self.app_client.app_spec.local_state_schema,
            app_id=self.existing_app_metadata_or_reference.app_id,
        )

        if app_changes.schema_breaking_change:
            logger.warning(f"Detected a breaking app schema change: {app_changes.schema_change_description}")
            return self._deploy_breaking_change()

        if app_changes.app_updated:
            logger.info(f"Detected a TEAL update in app id {self.existing_app_metadata_or_reference.app_id}")
            return self._deploy_update()

        logger.info("No detected changes in app, nothing to do.")
        return DeployResponse(app=self.existing_app_metadata_or_reference)

    def _deploy_breaking_change(self) -> DeployResponse:
        assert isinstance(self.existing_app_metadata_or_reference, AppMetaData)
        if self.on_schema_break == OnSchemaBreak.Fail:
            raise DeploymentFailedError(
                "Schema break detected and on_schema_break=OnSchemaBreak.Fail, stopping deployment. "
                "If you want to try deleting and recreating the app then "
                "re-run with on_schema_break=OnSchemaBreak.ReplaceApp"
            )
        if self.on_schema_break == OnSchemaBreak.AppendApp:
            logger.info("Schema break detected and on_schema_break=AppendApp, will attempt to create new app")
            return self._create_app()

        if self.existing_app_metadata_or_reference.deletable:
            logger.info(
                "App is deletable and on_schema_break=ReplaceApp, will attempt to create new app and delete old app"
            )
        elif self.existing_app_metadata_or_reference.deletable is False:
            logger.warning(
                "App is not deletable but on_schema_break=ReplaceApp, "
                "will attempt to delete app, delete will most likely fail"
            )
        else:
            logger.warning(
                "Cannot determine if App is deletable but on_schema_break=ReplaceApp, will attempt to delete app"
            )
        return self._create_and_delete_app()

    def _deploy_update(self) -> DeployResponse:
        assert isinstance(self.existing_app_metadata_or_reference, AppMetaData)
        if self.on_update == OnUpdate.Fail:
            raise DeploymentFailedError(
                "Update detected and on_update=Fail, stopping deployment. "
                "If you want to try updating the app then re-run with on_update=UpdateApp"
            )
        if self.on_update == OnUpdate.AppendApp:
            logger.info("Update detected and on_update=AppendApp, will attempt to create new app")
            return self._create_app()
        elif self.existing_app_metadata_or_reference.updatable and self.on_update == OnUpdate.UpdateApp:
            logger.info("App is updatable and on_update=UpdateApp, will update app")
            return self._update_app()
        elif self.existing_app_metadata_or_reference.updatable and self.on_update == OnUpdate.ReplaceApp:
            logger.warning(
                "App is updatable but on_update=ReplaceApp, will attempt to create new app and delete old app"
            )
            return self._create_and_delete_app()
        elif self.on_update == OnUpdate.ReplaceApp:
            if self.existing_app_metadata_or_reference.updatable is False:
                logger.warning(
                    "App is not updatable and on_update=ReplaceApp, "
                    "will attempt to create new app and delete old app"
                )
            else:
                logger.warning(
                    "Cannot determine if App is updatable and on_update=ReplaceApp, "
                    "will attempt to create new app and delete old app"
                )
            return self._create_and_delete_app()
        else:
            if self.existing_app_metadata_or_reference.updatable is False:
                logger.warning(
                    "App is not updatable but on_update=UpdateApp, "
                    "will attempt to update app, update will most likely fail"
                )
            else:
                logger.warning(
                    "Cannot determine if App is updatable and on_update=UpdateApp, will attempt to update app"
                )
            return self._update_app()

    def _create_app(self) -> DeployResponse:
        assert self.app_client.existing_deployments

        method, abi_args, parameters = _convert_deploy_args(
            self.create_args, self.new_app_metadata, self.signer, self.sender
        )
        create_response = self.app_client.create(
            method,
            parameters,
            **abi_args,
        )
        logger.info(
            f"{self.new_app_metadata.name} ({self.new_app_metadata.version}) deployed successfully, "
            f"with app id {self.app_client.app_id}."
        )
        assert create_response.confirmed_round is not None
        app_metadata = _create_metadata(self.new_app_metadata, self.app_client.app_id, create_response.confirmed_round)
        self.app_client.existing_deployments.apps[self.new_app_metadata.name] = app_metadata
        return DeployResponse(app=app_metadata, create_response=create_response, action_taken=OperationPerformed.Create)

    def _create_and_delete_app(self) -> DeployResponse:
        assert self.app_client.existing_deployments
        assert isinstance(self.existing_app_metadata_or_reference, AppMetaData)

        logger.info(
            f"Replacing {self.existing_app_metadata_or_reference.name} "
            f"({self.existing_app_metadata_or_reference.version}) with "
            f"{self.new_app_metadata.name} ({self.new_app_metadata.version}) in {self.creator} account."
        )
        atc = AtomicTransactionComposer()
        create_method, create_abi_args, create_parameters = _convert_deploy_args(
            self.create_args, self.new_app_metadata, self.signer, self.sender
        )
        self.app_client.compose_create(
            atc,
            create_method,
            create_parameters,
            **create_abi_args,
        )
        create_txn_index = len(atc.txn_list) - 1
        delete_method, delete_abi_args, delete_parameters = _convert_deploy_args(
            self.delete_args, self.new_app_metadata, self.signer, self.sender
        )
        self.app_client.compose_delete(
            atc,
            delete_method,
            delete_parameters,
            **delete_abi_args,
        )
        delete_txn_index = len(atc.txn_list) - 1
        create_delete_response = self.app_client.execute_atc(atc)
        create_response = TransactionResponse.from_atr(create_delete_response, create_txn_index)
        delete_response = TransactionResponse.from_atr(create_delete_response, delete_txn_index)
        self.app_client.app_id = get_app_id_from_tx_id(self.app_client.algod_client, create_response.tx_id)
        logger.info(
            f"{self.new_app_metadata.name} ({self.new_app_metadata.version}) deployed successfully, "
            f"with app id {self.app_client.app_id}."
        )
        logger.info(
            f"{self.existing_app_metadata_or_reference.name} "
            f"({self.existing_app_metadata_or_reference.version}) with app id "
            f"{self.existing_app_metadata_or_reference.app_id}, deleted successfully."
        )

        app_metadata = _create_metadata(
            self.new_app_metadata, self.app_client.app_id, create_delete_response.confirmed_round
        )
        self.app_client.existing_deployments.apps[self.new_app_metadata.name] = app_metadata

        return DeployResponse(
            app=app_metadata,
            create_response=create_response,
            delete_response=delete_response,
            action_taken=OperationPerformed.Replace,
        )

    def _update_app(self) -> DeployResponse:
        assert self.app_client.existing_deployments
        assert isinstance(self.existing_app_metadata_or_reference, AppMetaData)

        logger.info(
            f"Updating {self.existing_app_metadata_or_reference.name} to {self.new_app_metadata.version} in "
            f"{self.creator} account, with app id {self.existing_app_metadata_or_reference.app_id}"
        )
        method, abi_args, parameters = _convert_deploy_args(
            self.update_args, self.new_app_metadata, self.signer, self.sender
        )
        update_response = self.app_client.update(
            method,
            parameters,
            **abi_args,
        )
        app_metadata = _create_metadata(
            self.new_app_metadata,
            self.app_client.app_id,
            self.existing_app_metadata_or_reference.created_round,
            updated_round=update_response.confirmed_round,
            original_metadata=self.existing_app_metadata_or_reference.created_metadata,
        )
        self.app_client.existing_deployments.apps[self.new_app_metadata.name] = app_metadata
        return DeployResponse(app=app_metadata, update_response=update_response, action_taken=OperationPerformed.Update)


def _create_metadata(
    app_spec_note: AppDeployMetaData,
    app_id: int,
    created_round: int,
    updated_round: int | None = None,
    original_metadata: AppDeployMetaData | None = None,
) -> AppMetaData:
    return AppMetaData(
        app_id=app_id,
        app_address=get_application_address(app_id),
        created_metadata=original_metadata or app_spec_note,
        created_round=created_round,
        updated_round=updated_round or created_round,
        name=app_spec_note.name,
        version=app_spec_note.version,
        deletable=app_spec_note.deletable,
        updatable=app_spec_note.updatable,
        deleted=False,
    )


def _convert_deploy_args(
    _args: DeployCallArgs | DeployCallArgsDict | None,
    note: AppDeployMetaData,
    signer: TransactionSigner | None,
    sender: str | None,
) -> tuple[ABIMethod | bool | None, ABIArgsDict, CreateCallParameters]:
    args = _args.__dict__ if isinstance(_args, DeployCallArgs) else dict(_args or {})

    # return most derived type, unused parameters are ignored
    parameters = CreateCallParameters(
        note=note.encode(),
        signer=signer,
        sender=sender,
        suggested_params=args.get("suggested_params"),
        lease=args.get("lease"),
        accounts=args.get("accounts"),
        foreign_assets=args.get("foreign_assets"),
        foreign_apps=args.get("foreign_apps"),
        boxes=args.get("boxes"),
        rekey_to=args.get("rekey_to"),
        extra_pages=args.get("extra_pages"),
        on_complete=args.get("on_complete"),
    )

    return args.get("method"), args.get("args") or {}, parameters


def get_app_id_from_tx_id(algod_client: "AlgodClient", tx_id: str) -> int:
    """Finds the app_id for provided transaction id"""
    result = algod_client.pending_transaction_info(tx_id)
    assert isinstance(result, dict)
    app_id = result["application-index"]
    assert isinstance(app_id, int)
    return app_id

# === File: algokit_utils/models.py ===
import dataclasses
from collections.abc import Sequence
from typing import Any, Generic, Protocol, TypeAlias, TypedDict, TypeVar

import algosdk.account
from algosdk import transaction
from algosdk.abi import Method
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionResponse,
    SimulateAtomicTransactionResponse,
    TransactionSigner,
)
from algosdk.encoding import decode_address
from deprecated import deprecated

__all__ = [
    "ABIArgsDict",
    "ABIMethod",
    "ABITransactionResponse",
    "Account",
    "CreateCallParameters",
    "CreateCallParametersDict",
    "CreateTransactionParameters",
    "OnCompleteCallParameters",
    "OnCompleteCallParametersDict",
    "TransactionParameters",
    "TransactionResponse",
]

ReturnType = TypeVar("ReturnType")


@dataclasses.dataclass(kw_only=True)
class Account:
    """Holds the private_key and address for an account"""

    private_key: str
    """Base64 encoded private key"""
    address: str = dataclasses.field(default="")
    """Address for this account"""

    def __post_init__(self) -> None:
        if not self.address:
            self.address = algosdk.account.address_from_private_key(self.private_key)  # type: ignore[no-untyped-call]

    @property
    def public_key(self) -> bytes:
        """The public key for this account"""
        public_key = decode_address(self.address)  # type: ignore[no-untyped-call]
        assert isinstance(public_key, bytes)
        return public_key

    @property
    def signer(self) -> AccountTransactionSigner:
        """An AccountTransactionSigner for this account"""
        return AccountTransactionSigner(self.private_key)

    @staticmethod
    def new_account() -> "Account":
        private_key, address = algosdk.account.generate_account()  # type: ignore[no-untyped-call]
        return Account(private_key=private_key)


@dataclasses.dataclass(kw_only=True)
class TransactionResponse:
    """Response for a non ABI call"""

    tx_id: str
    """Transaction Id"""
    confirmed_round: int | None
    """Round transaction was confirmed, `None` if call was a from a dry-run"""

    @staticmethod
    def from_atr(
        result: AtomicTransactionResponse | SimulateAtomicTransactionResponse, transaction_index: int = -1
    ) -> "TransactionResponse":
        """Returns either an ABITransactionResponse or a TransactionResponse based on the type of the transaction
        referred to by transaction_index
        :param AtomicTransactionResponse result: Result containing one or more transactions
        :param int transaction_index: Which transaction in the result to return, defaults to -1 (the last transaction)
        """
        tx_id = result.tx_ids[transaction_index]
        abi_result = next((r for r in result.abi_results if r.tx_id == tx_id), None)
        confirmed_round = None if isinstance(result, SimulateAtomicTransactionResponse) else result.confirmed_round
        if abi_result:
            return ABITransactionResponse(
                tx_id=tx_id,
                raw_value=abi_result.raw_value,
                return_value=abi_result.return_value,
                decode_error=abi_result.decode_error,
                tx_info=abi_result.tx_info,
                method=abi_result.method,
                confirmed_round=confirmed_round,
            )
        else:
            return TransactionResponse(
                tx_id=tx_id,
                confirmed_round=confirmed_round,
            )


@dataclasses.dataclass(kw_only=True)
class ABITransactionResponse(TransactionResponse, Generic[ReturnType]):
    """Response for an ABI call"""

    raw_value: bytes
    """The raw response before ABI decoding"""
    return_value: ReturnType
    """Decoded ABI result"""
    decode_error: Exception | None
    """Details of error that occurred when attempting to decode raw_value"""
    tx_info: dict
    """Details of transaction"""
    method: Method
    """ABI method used to make call"""


ABIArgType = Any
ABIArgsDict = dict[str, ABIArgType]


class ABIReturnSubroutine(Protocol):
    def method_spec(self) -> Method: ...


ABIMethod: TypeAlias = ABIReturnSubroutine | Method | str


@dataclasses.dataclass(kw_only=True)
class TransactionParameters:
    """Additional parameters that can be included in a transaction"""

    signer: TransactionSigner | None = None
    """Signer to use when signing this transaction"""
    sender: str | None = None
    """Sender of this transaction"""
    suggested_params: transaction.SuggestedParams | None = None
    """SuggestedParams to use for this transaction"""
    note: bytes | str | None = None
    """Note for this transaction"""
    lease: bytes | str | None = None
    """Lease value for this transaction"""
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]] | None = None
    """Box references to include in transaction. A sequence of (app id, box key) tuples"""
    accounts: list[str] | None = None
    """Accounts to include in transaction"""
    foreign_apps: list[int] | None = None
    """List of foreign apps (by app id) to include in transaction"""
    foreign_assets: list[int] | None = None
    """List of foreign assets (by asset id) to include in transaction"""
    rekey_to: str | None = None
    """Address to rekey to"""


# CreateTransactionParameters is used by algokit-client-generator clients
@dataclasses.dataclass(kw_only=True)
class CreateTransactionParameters(TransactionParameters):
    """Additional parameters that can be included in a transaction when calling a create method"""

    extra_pages: int | None = None


@dataclasses.dataclass(kw_only=True)
class OnCompleteCallParameters(TransactionParameters):
    """Additional parameters that can be included in a transaction when using the
    ApplicationClient.call/compose_call methods"""

    on_complete: transaction.OnComplete | None = None


@dataclasses.dataclass(kw_only=True)
class CreateCallParameters(OnCompleteCallParameters):
    """Additional parameters that can be included in a transaction when using the
    ApplicationClient.create/compose_create methods"""

    extra_pages: int | None = None


class TransactionParametersDict(TypedDict, total=False):
    """Additional parameters that can be included in a transaction"""

    signer: TransactionSigner
    """Signer to use when signing this transaction"""
    sender: str
    """Sender of this transaction"""
    suggested_params: transaction.SuggestedParams
    """SuggestedParams to use for this transaction"""
    note: bytes | str
    """Note for this transaction"""
    lease: bytes | str
    """Lease value for this transaction"""
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]]
    """Box references to include in transaction. A sequence of (app id, box key) tuples"""
    accounts: list[str]
    """Accounts to include in transaction"""
    foreign_apps: list[int]
    """List of foreign apps (by app id) to include in transaction"""
    foreign_assets: list[int]
    """List of foreign assets (by asset id) to include in transaction"""
    rekey_to: str
    """Address to rekey to"""


class OnCompleteCallParametersDict(TypedDict, TransactionParametersDict, total=False):
    """Additional parameters that can be included in a transaction when using the
    ApplicationClient.call/compose_call methods"""

    on_complete: transaction.OnComplete


class CreateCallParametersDict(TypedDict, OnCompleteCallParametersDict, total=False):
    """Additional parameters that can be included in a transaction when using the
    ApplicationClient.create/compose_create methods"""

    extra_pages: int


# Pre 1.3.1 backwards compatibility
@deprecated(reason="Use TransactionParameters instead", version="1.3.1")
class RawTransactionParameters(TransactionParameters):
    """Deprecated, use TransactionParameters instead"""


@deprecated(reason="Use TransactionParameters instead", version="1.3.1")
class CommonCallParameters(TransactionParameters):
    """Deprecated, use TransactionParameters instead"""


@deprecated(reason="Use TransactionParametersDict instead", version="1.3.1")
class CommonCallParametersDict(TransactionParametersDict):
    """Deprecated, use TransactionParametersDict instead"""


@dataclasses.dataclass
class SimulationTrace:
    app_budget_added: int | None
    app_budget_consumed: int | None
    failure_message: str | None
    exec_trace: dict[str, object]

# === File: algokit_utils/asset.py ===
import logging
from typing import TYPE_CHECKING

from algosdk.atomic_transaction_composer import AtomicTransactionComposer, TransactionWithSigner
from algosdk.constants import TX_GROUP_LIMIT
from algosdk.transaction import AssetTransferTxn

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient

from enum import Enum, auto

from algokit_utils.models import Account

__all__ = ["opt_in", "opt_out"]
logger = logging.getLogger(__name__)


class ValidationType(Enum):
    OPTIN = auto()
    OPTOUT = auto()


def _ensure_account_is_valid(algod_client: "AlgodClient", account: Account) -> None:
    try:
        algod_client.account_info(account.address)
    except Exception as err:
        error_message = f"Account address{account.address}  does not exist"
        logger.debug(error_message)
        raise err


def _ensure_asset_balance_conditions(
    algod_client: "AlgodClient", account: Account, asset_ids: list, validation_type: ValidationType
) -> None:
    invalid_asset_ids = []
    account_info = algod_client.account_info(account.address)
    account_assets = account_info.get("assets", [])  # type: ignore  # noqa: PGH003
    for asset_id in asset_ids:
        asset_exists_in_account_info = any(asset["asset-id"] == asset_id for asset in account_assets)
        if validation_type == ValidationType.OPTIN:
            if asset_exists_in_account_info:
                logger.debug(f"Asset {asset_id} is already opted in for account {account.address}")
                invalid_asset_ids.append(asset_id)

        elif validation_type == ValidationType.OPTOUT:
            if not account_assets or not asset_exists_in_account_info:
                logger.debug(f"Account {account.address} does not have asset {asset_id}")
                invalid_asset_ids.append(asset_id)
            else:
                asset_balance = next((asset["amount"] for asset in account_assets if asset["asset-id"] == asset_id), 0)
                if asset_balance != 0:
                    logger.debug(f"Asset {asset_id} balance is not zero")
                    invalid_asset_ids.append(asset_id)

    if len(invalid_asset_ids) > 0:
        action = "opted out" if validation_type == ValidationType.OPTOUT else "opted in"
        condition_message = (
            "their amount is zero and that the account has"
            if validation_type == ValidationType.OPTOUT
            else "they are valid and that the account has not"
        )

        error_message = (
            f"Assets {invalid_asset_ids} cannot be {action}. Ensure that "
            f"{condition_message} previously opted into them."
        )
        raise ValueError(error_message)


def opt_in(algod_client: "AlgodClient", account: Account, asset_ids: list[int]) -> dict[int, str]:
    """
    Opt-in to a list of assets on the Algorand blockchain. Before an account can receive a specific asset,
    it must `opt-in` to receive it. An opt-in transaction places an asset holding of 0 into the account and increases
    its minimum balance by [100,000 microAlgos](https://developer.algorand.org/docs/get-details/asa/#assets-overview).

    Args:
        algod_client (AlgodClient): An instance of the AlgodClient class from the algosdk library.
        account (Account): An instance of the Account class representing the account that wants to opt-in to the assets.
        asset_ids (list[int]): A list of integers representing the asset IDs to opt-in to.
    Returns:
        dict[int, str]: A dictionary where the keys are the asset IDs and the values
        are the transaction IDs for opting-in to each asset.
    """
    _ensure_account_is_valid(algod_client, account)
    _ensure_asset_balance_conditions(algod_client, account, asset_ids, ValidationType.OPTIN)
    suggested_params = algod_client.suggested_params()
    result = {}
    for i in range(0, len(asset_ids), TX_GROUP_LIMIT):
        atc = AtomicTransactionComposer()
        chunk = asset_ids[i : i + TX_GROUP_LIMIT]
        for asset_id in chunk:
            asset = algod_client.asset_info(asset_id)
            xfer_txn = AssetTransferTxn(
                sp=suggested_params,
                sender=account.address,
                receiver=account.address,
                close_assets_to=None,
                revocation_target=None,
                amt=0,
                note=f"opt in asset id ${asset_id}",
                index=asset["index"],  # type: ignore  # noqa: PGH003
                rekey_to=None,
            )

            transaction_with_signer = TransactionWithSigner(
                txn=xfer_txn,
                signer=account.signer,
            )
            atc.add_transaction(transaction_with_signer)
        atc.execute(algod_client, 4)

        for index, asset_id in enumerate(chunk):
            result[asset_id] = atc.tx_ids[index]

    return result


def opt_out(algod_client: "AlgodClient", account: Account, asset_ids: list[int]) -> dict[int, str]:
    """
    Opt out from a list of Algorand Standard Assets (ASAs) by transferring them back to their creators.
    The account also recovers the Minimum Balance Requirement for the asset (100,000 microAlgos)
    The `optOut` function manages the opt-out process, permitting the account to discontinue holding a group of assets.

    It's essential to note that an account can only opt_out of an asset if its balance of that asset is zero.

    Args:
        algod_client (AlgodClient): An instance of the AlgodClient class from the `algosdk` library.
        account (Account): An instance of the Account class that holds the private key and address for an account.
        asset_ids (list[int]): A list of integers representing the asset IDs of the ASAs to opt out from.
    Returns:
        dict[int, str]: A dictionary where the keys are the asset IDs and the values are the transaction IDs of
        the executed transactions.

    """
    _ensure_account_is_valid(algod_client, account)
    _ensure_asset_balance_conditions(algod_client, account, asset_ids, ValidationType.OPTOUT)
    suggested_params = algod_client.suggested_params()
    result = {}
    for i in range(0, len(asset_ids), TX_GROUP_LIMIT):
        atc = AtomicTransactionComposer()
        chunk = asset_ids[i : i + TX_GROUP_LIMIT]
        for asset_id in chunk:
            asset = algod_client.asset_info(asset_id)
            asset_creator = asset["params"]["creator"]  # type: ignore  # noqa: PGH003
            xfer_txn = AssetTransferTxn(
                sp=suggested_params,
                sender=account.address,
                receiver=account.address,
                close_assets_to=asset_creator,
                revocation_target=None,
                amt=0,
                note=f"opt out asset id ${asset_id}",
                index=asset["index"],  # type: ignore  # noqa: PGH003
                rekey_to=None,
            )

            transaction_with_signer = TransactionWithSigner(
                txn=xfer_txn,
                signer=account.signer,
            )
            atc.add_transaction(transaction_with_signer)
        atc.execute(algod_client, 4)

        for index, asset_id in enumerate(chunk):
            result[asset_id] = atc.tx_ids[index]

    return result

# === File: algokit_utils/network_clients.py ===
import dataclasses
import os
from typing import Literal
from urllib import parse

from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

__all__ = [
    "AlgoClientConfig",
    "get_algod_client",
    "get_algonode_config",
    "get_default_localnet_config",
    "get_indexer_client",
    "get_kmd_client_from_algod_client",
    "is_localnet",
    "is_mainnet",
    "is_testnet",
    "AlgoConfig",
    "get_kmd_client",
]


@dataclasses.dataclass
class AlgoClientConfig:
    """Connection details for connecting to an {py:class}`algosdk.v2client.algod.AlgodClient` or
    {py:class}`algosdk.v2client.indexer.IndexerClient`"""

    server: str
    port: str | int | None = None
    token: str | None = None


@dataclasses.dataclass
class NetworkDetails:
    genesis_id: str
    genesis_hash: str
    is_testnet: bool
    is_mainnet: bool
    is_localnet: bool


@dataclasses.dataclass
class AlgoConfig:
    algod_config: AlgoClientConfig
    indexer_config: AlgoClientConfig | None = None
    kmd_config: AlgoClientConfig | None = None


def get_default_localnet_config(config: Literal["algod", "indexer", "kmd"]) -> AlgoClientConfig:
    """Returns the client configuration to point to the default LocalNet"""
    port = {"algod": 4001, "indexer": 8980, "kmd": 4002}[config]
    return AlgoClientConfig(server=f"http://localhost:{port}", token="a" * 64)


def get_algonode_config(
    network: Literal["testnet", "mainnet"], config: Literal["algod", "indexer"], token: str
) -> AlgoClientConfig:
    client = "api" if config == "algod" else "idx"
    return AlgoClientConfig(
        server=f"https://{network}-{client}.algonode.cloud",
        token=token,
    )


def get_algod_client(config: AlgoClientConfig | None = None) -> AlgodClient:
    """Returns an {py:class}`algosdk.v2client.algod.AlgodClient` from `config` or environment

    If no configuration provided will use environment variables `ALGOD_SERVER`, `ALGOD_PORT` and `ALGOD_TOKEN`"""
    config = config or _get_config_from_environment("ALGOD")
    headers = {"X-Algo-API-Token": config.token}
    return AlgodClient(
        config.token or "", config.server, {key: value for key, value in headers.items() if value is not None}
    )  # type: ignore[no-untyped-call]


def get_kmd_client(config: AlgoClientConfig | None = None) -> KMDClient:
    """Returns an {py:class}`algosdk.kmd.KMDClient` from `config` or environment

    If no configuration provided will use environment variables `KMD_SERVER`, `KMD_PORT` and `KMD_TOKEN`"""
    config = config or _get_config_from_environment("KMD")
    return KMDClient(config.token, config.server)  # type: ignore[no-untyped-call]


def get_indexer_client(config: AlgoClientConfig | None = None) -> IndexerClient:
    """Returns an {py:class}`algosdk.v2client.indexer.IndexerClient` from `config` or environment.

    If no configuration provided will use environment variables `INDEXER_SERVER`, `INDEXER_PORT` and `INDEXER_TOKEN`"""
    config = config or _get_config_from_environment("INDEXER")
    headers = {"X-Indexer-API-Token": config.token}
    return IndexerClient(config.token, config.server, headers)  # type: ignore[no-untyped-call]


def is_localnet(client: AlgodClient) -> bool:
    """Returns True if client genesis is `devnet-v1` or `sandnet-v1`"""
    params = client.suggested_params()
    return params.gen in ["devnet-v1", "sandnet-v1", "dockernet-v1"]


def is_mainnet(client: AlgodClient) -> bool:
    """Returns True if client genesis is `mainnet-v1`"""
    params = client.suggested_params()
    return params.gen in ["mainnet-v1.0", "mainnet-v1", "mainnet"]


def is_testnet(client: AlgodClient) -> bool:
    """Returns True if client genesis is `testnet-v1`"""
    params = client.suggested_params()
    return params.gen in ["testnet-v1.0", "testnet-v1", "testnet"]


def get_kmd_client_from_algod_client(client: AlgodClient) -> KMDClient:
    """Returns an {py:class}`algosdk.kmd.KMDClient` from supplied `client`

    Will use the same address as provided `client` but on port specified by `KMD_PORT` environment variable,
    or 4002 by default"""
    # We can only use Kmd on the LocalNet otherwise it's not exposed so this makes some assumptions
    # (e.g. same token and server as algod and port 4002 by default)
    port = os.getenv("KMD_PORT", "4002")
    server = _replace_kmd_port(client.algod_address, port)
    return KMDClient(client.algod_token, server)  # type: ignore[no-untyped-call]


def _replace_kmd_port(address: str, port: str) -> str:
    parsed_algod = parse.urlparse(address)
    kmd_host = parsed_algod.netloc.split(":", maxsplit=1)[0] + f":{port}"
    kmd_parsed = parsed_algod._replace(netloc=kmd_host)
    return parse.urlunparse(kmd_parsed)


def _get_config_from_environment(environment_prefix: str) -> AlgoClientConfig:
    server = os.getenv(f"{environment_prefix}_SERVER")
    if server is None:
        raise Exception(f"Server environment variable not set: {environment_prefix}_SERVER")
    port = os.getenv(f"{environment_prefix}_PORT")
    if port:
        parsed = parse.urlparse(server)
        server = parsed._replace(netloc=f"{parsed.hostname}:{port}").geturl()
    return AlgoClientConfig(server, os.getenv(f"{environment_prefix}_TOKEN", ""))

# === File: algokit_utils/__init__.py ===
from algokit_utils._debugging import PersistSourceMapInput, persist_sourcemaps, simulate_and_persist_response
from algokit_utils._ensure_funded import EnsureBalanceParameters, EnsureFundedResponse, ensure_funded
from algokit_utils._transfer import TransferAssetParameters, TransferParameters, transfer, transfer_asset
from algokit_utils.account import (
    create_kmd_wallet_account,
    get_account,
    get_account_from_mnemonic,
    get_dispenser_account,
    get_kmd_wallet_account,
    get_localnet_default_account,
    get_or_create_kmd_wallet_account,
)
from algokit_utils.application_client import (
    ApplicationClient,
    execute_atc_with_logic_error,
    get_next_version,
    get_sender_from_signer,
    num_extra_program_pages,
)
from algokit_utils.application_specification import (
    ApplicationSpecification,
    AppSpecStateDict,
    CallConfig,
    DefaultArgumentDict,
    DefaultArgumentType,
    MethodConfigDict,
    MethodHints,
    OnCompleteActionName,
)
from algokit_utils.asset import opt_in, opt_out
from algokit_utils.common import Program
from algokit_utils.deploy import (
    DELETABLE_TEMPLATE_NAME,
    NOTE_PREFIX,
    UPDATABLE_TEMPLATE_NAME,
    ABICallArgs,
    ABICallArgsDict,
    ABICreateCallArgs,
    ABICreateCallArgsDict,
    AppDeployMetaData,
    AppLookup,
    AppMetaData,
    AppReference,
    DeployCallArgs,
    DeployCallArgsDict,
    DeployCreateCallArgs,
    DeployCreateCallArgsDict,
    DeploymentFailedError,
    DeployResponse,
    OnSchemaBreak,
    OnUpdate,
    OperationPerformed,
    TemplateValueDict,
    TemplateValueMapping,
    get_app_id_from_tx_id,
    get_creator_apps,
    replace_template_variables,
)
from algokit_utils.dispenser_api import (
    DISPENSER_ACCESS_TOKEN_KEY,
    DISPENSER_REQUEST_TIMEOUT,
    DispenserFundResponse,
    DispenserLimitResponse,
    TestNetDispenserApiClient,
)
from algokit_utils.logic_error import LogicError
from algokit_utils.models import (
    ABIArgsDict,
    ABIMethod,
    ABITransactionResponse,
    Account,
    CommonCallParameters,  # noqa: F401
    CommonCallParametersDict,  # noqa: F401
    CreateCallParameters,
    CreateCallParametersDict,
    CreateTransactionParameters,
    OnCompleteCallParameters,
    OnCompleteCallParametersDict,
    RawTransactionParameters,  # noqa: F401
    TransactionParameters,
    TransactionParametersDict,
    TransactionResponse,
)
from algokit_utils.network_clients import (
    AlgoClientConfig,
    get_algod_client,
    get_algonode_config,
    get_default_localnet_config,
    get_indexer_client,
    get_kmd_client_from_algod_client,
    is_localnet,
    is_mainnet,
    is_testnet,
)

__all__ = [
    "create_kmd_wallet_account",
    "get_account_from_mnemonic",
    "get_or_create_kmd_wallet_account",
    "get_localnet_default_account",
    "get_dispenser_account",
    "get_kmd_wallet_account",
    "get_account",
    "UPDATABLE_TEMPLATE_NAME",
    "DELETABLE_TEMPLATE_NAME",
    "NOTE_PREFIX",
    "DeploymentFailedError",
    "AppReference",
    "AppDeployMetaData",
    "AppMetaData",
    "AppLookup",
    "get_creator_apps",
    "replace_template_variables",
    "ABIArgsDict",
    "ABICallArgs",
    "ABICallArgsDict",
    "ABICreateCallArgs",
    "ABICreateCallArgsDict",
    "ABIMethod",
    "CreateCallParameters",
    "CreateCallParametersDict",
    "CreateTransactionParameters",
    "DeployCallArgs",
    "DeployCreateCallArgs",
    "DeployCallArgsDict",
    "DeployCreateCallArgsDict",
    "OnCompleteCallParameters",
    "OnCompleteCallParametersDict",
    "TransactionParameters",
    "TransactionParametersDict",
    "ApplicationClient",
    "DeployResponse",
    "OnUpdate",
    "OnSchemaBreak",
    "OperationPerformed",
    "TemplateValueDict",
    "TemplateValueMapping",
    "Program",
    "execute_atc_with_logic_error",
    "get_app_id_from_tx_id",
    "get_next_version",
    "get_sender_from_signer",
    "num_extra_program_pages",
    "AppSpecStateDict",
    "ApplicationSpecification",
    "CallConfig",
    "DefaultArgumentDict",
    "DefaultArgumentType",
    "MethodConfigDict",
    "OnCompleteActionName",
    "MethodHints",
    "LogicError",
    "ABITransactionResponse",
    "Account",
    "TransactionResponse",
    "AlgoClientConfig",
    "get_algod_client",
    "get_algonode_config",
    "get_default_localnet_config",
    "get_indexer_client",
    "get_kmd_client_from_algod_client",
    "is_localnet",
    "is_mainnet",
    "is_testnet",
    "TestNetDispenserApiClient",
    "DispenserFundResponse",
    "DispenserLimitResponse",
    "DISPENSER_ACCESS_TOKEN_KEY",
    "DISPENSER_REQUEST_TIMEOUT",
    "EnsureBalanceParameters",
    "EnsureFundedResponse",
    "TransferParameters",
    "ensure_funded",
    "transfer",
    "TransferAssetParameters",
    "transfer_asset",
    "opt_in",
    "opt_out",
    "persist_sourcemaps",
    "PersistSourceMapInput",
    "simulate_and_persist_response",
]

# === File: algokit_utils/client_manager.py ===
import dataclasses
import os
from typing import Literal

from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from algokit_utils.dispenser_api import (
    BaseDispenserApiClientParams,
    TestNetDispenserApiClient,
    TestNetDispenserApiClientParams,
)
from algokit_utils.network_clients import AlgoClientConfig, AlgoConfig, NetworkDetails


@dataclasses.dataclass
class AlgoSdkClients:
    algod: AlgodClient
    indexer: IndexerClient | None = None
    kmd: KMDClient | None = None


class ClientManager:
    def __init__(self, config: AlgoConfig | AlgoSdkClients):
        if isinstance(config, AlgoSdkClients):
            self._algod = config.algod
            self._indexer = config.indexer
            self._kmd = config.kmd
        else:
            self._algod = self.get_algod_client(config.algod_config)
            self._indexer = self.get_indexer_client(config.indexer_config) if config.indexer_config else None
            self._kmd = self.get_kmd_client(config.kmd_config) if config.kmd_config else None

    @property
    def algod(self) -> AlgodClient:
        return self._algod

    @property
    def indexer(self) -> IndexerClient:
        if not self._indexer:
            raise ValueError("Attempt to use Indexer client in AlgoKit instance with no Indexer configured")
        return self._indexer

    @property
    def kmd(self) -> KMDClient:
        if not self._kmd:
            raise ValueError("Attempt to use Kmd client in AlgoKit instance with no Kmd configured")
        return self._kmd

    def network(self) -> NetworkDetails:
        params = self._algod.suggested_params()
        genesis_id = str(params.gen)
        genesis_hash = str(params.gh)
        is_testnet = "testnet" in genesis_id
        is_mainnet = "mainnet" in genesis_id
        is_localnet = self.genesis_id_is_localnet(genesis_id)
        return NetworkDetails(
            genesis_id=genesis_id,
            genesis_hash=genesis_hash,
            is_testnet=is_testnet,
            is_mainnet=is_mainnet,
            is_localnet=is_localnet,
        )

    async def is_localnet(self) -> bool:
        return self.network().is_localnet

    def is_testnet(self) -> bool:
        return self.network().is_testnet

    def is_mainnet(self) -> bool:
        return self.network().is_mainnet

    def get_testnet_dispenser(self, params: TestNetDispenserApiClientParams) -> TestNetDispenserApiClient:
        return TestNetDispenserApiClient(params)

    def get_test_net_dispenser_from_environment(
        self, params: BaseDispenserApiClientParams | None = None
    ) -> TestNetDispenserApiClient:
        if params is None:
            params = BaseDispenserApiClientParams()

        return TestNetDispenserApiClient(
            TestNetDispenserApiClientParams(auth_token="", request_timeout=params.request_timeout)
        )

    # def get_app_factory(self) -> None:
    #     # TODO: implement
    #     pass

    # def get_app_client_by_creator_and_name(self) -> None:
    #     # TODO: implement
    #     pass

    # def get_app_client_by_id(self, params: ClientAppClientParams) -> None:
    #     # TODO: implement
    #     pass

    # async def get_app_client_by_network(self, params: ClientAppClientByNetworkParams) -> None:
    #     # TODO: implement
    #     pass

    # async def get_typed_app_client_by_creator_and_name(
    #     self, typed_client: TypedAppClient, params: ClientTypedAppClientByCreatorAndNameParams
    # ) -> None:
    #     # TODO: implement
    #     pass

    # def get_typed_app_client_by_id(self, typed_client: TypedAppClient, params: ClientTypedAppClientParams) -> None:
    #     # TODO: implement
    #     pass

    # def get_typed_app_client_by_network(
    #     self, typed_client: TypedAppClient, params: ClientTypedAppClientByNetworkParams | None = None
    # ) -> None:
    #     # TODO: implement
    #     pass

    # def get_typed_app_factory(
    #     self, typed_factory: TypedAppFactory, params: ClientTypedAppFactoryParams | None = None
    # ) -> None:
    #     # TODO: implement
    #     pass

    @staticmethod
    def get_config_from_environment_or_localnet() -> AlgoConfig:
        if os.getenv("ALGOD_SERVER"):
            algod_config = ClientManager.get_algod_config_from_environment()
            indexer_config = (
                ClientManager.get_indexer_config_from_environment() if os.getenv("INDEXER_SERVER") else None
            )
            kmd_config = (
                AlgoClientConfig(
                    server=algod_config.server, port=os.getenv("KMD_PORT", "4002"), token=algod_config.token
                )
                if not any(net in algod_config.server for net in ["mainnet", "testnet"])
                else None
            )
        else:
            algod_config = ClientManager.get_default_localnet_config("algod")
            indexer_config = ClientManager.get_default_localnet_config("indexer")
            kmd_config = ClientManager.get_default_localnet_config("kmd")

        return AlgoConfig(algod_config=algod_config, indexer_config=indexer_config, kmd_config=kmd_config)

    @staticmethod
    def get_algod_config_from_environment() -> AlgoClientConfig:
        return ClientManager._get_config_from_environment("ALGOD")

    @staticmethod
    def get_indexer_config_from_environment() -> AlgoClientConfig:
        return ClientManager._get_config_from_environment("INDEXER")

    @staticmethod
    def get_algonode_config(
        network: Literal["testnet", "mainnet"], config: Literal["algod", "indexer"]
    ) -> AlgoClientConfig:
        return AlgoClientConfig(
            server=f"https://{network}-{ 'api' if config == 'algod' else 'idx'}.algonode.cloud/",
            token="",
        )

    @staticmethod
    def get_default_localnet_config(config_type: Literal["algod", "indexer", "kmd"]) -> AlgoClientConfig:
        return AlgoClientConfig(
            server="http://localhost",
            port=4001 if config_type == "algod" else 8980 if config_type == "indexer" else 4002,
            token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )

    @staticmethod
    def get_algod_client(config: AlgoClientConfig) -> AlgodClient:
        headers = {"X-Algo-API-Token": config.token} if config.token else None
        return AlgodClient(config.token or "", config.server, headers)

    @staticmethod
    def get_algod_client_from_environment() -> AlgodClient:
        return ClientManager.get_algod_client(ClientManager.get_algod_config_from_environment())

    @staticmethod
    def get_indexer_client(config: AlgoClientConfig) -> IndexerClient:
        headers = {"X-Indexer-API-Token": config.token} if config.token else None
        return IndexerClient(config.token or "", config.server, headers)  # type: ignore[no-untyped-call]

    @staticmethod
    def get_indexer_client_from_environment() -> IndexerClient:
        return ClientManager.get_indexer_client(ClientManager.get_indexer_config_from_environment())

    @staticmethod
    def get_kmd_client(config: AlgoClientConfig) -> KMDClient:
        return KMDClient(kmd_token=config.token, kmd_address=config.server)  # type: ignore[no-untyped-call]

    @staticmethod
    def get_kmd_client_from_environment() -> KMDClient:
        algod_config = ClientManager.get_algod_config_from_environment()
        algod_config.port = os.getenv("KMD_PORT", "4002")
        return ClientManager.get_kmd_client(algod_config)

    @staticmethod
    def genesis_id_is_localnet(genesis_id: str) -> bool:
        return genesis_id in ["devnet-v1", "sandnet-v1", "dockernet-v1"]

    @staticmethod
    def _get_config_from_environment(environment_prefix: str) -> AlgoClientConfig:
        server = os.getenv(f"{environment_prefix}_SERVER")
        if server is None:
            raise ValueError(f"Server environment variable not set: {environment_prefix}_SERVER")
        port = os.getenv(f"{environment_prefix}_PORT")
        token = os.getenv(f"{environment_prefix}_TOKEN", "")
        return AlgoClientConfig(server=server, port=port, token=token)

# === File: algokit_utils/common.py ===
"""
This module contains common classes and methods that are reused in more than one file.
"""

import base64
import typing

from algosdk.source_map import SourceMap

from algokit_utils import deploy

if typing.TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient


class Program:
    """A compiled TEAL program"""

    def __init__(self, program: str, client: "AlgodClient"):
        """
        Fully compile the program source to binary and generate a
        source map for matching pc to line number
        """
        self.teal = program
        result: dict = client.compile(deploy.strip_comments(self.teal), source_map=True)
        self.raw_binary = base64.b64decode(result["result"])
        self.binary_hash: str = result["hash"]
        self.source_map = SourceMap(result["sourcemap"])

# === File: algokit_utils/application_specification.py ===
import base64
import dataclasses
import json
from enum import IntFlag
from pathlib import Path
from typing import Any, Literal, TypeAlias, TypedDict

from algosdk.abi import Contract
from algosdk.abi.method import MethodDict
from algosdk.transaction import StateSchema

__all__ = [
    "CallConfig",
    "DefaultArgumentDict",
    "DefaultArgumentType",
    "MethodConfigDict",
    "OnCompleteActionName",
    "MethodHints",
    "ApplicationSpecification",
    "AppSpecStateDict",
]


AppSpecStateDict: TypeAlias = dict[str, dict[str, dict]]
"""Type defining Application Specification state entries"""


class CallConfig(IntFlag):
    """Describes the type of calls a method can be used for based on {py:class}`algosdk.transaction.OnComplete` type"""

    NEVER = 0
    """Never handle the specified on completion type"""
    CALL = 1
    """Only handle the specified on completion type for application calls"""
    CREATE = 2
    """Only handle the specified on completion type for application create calls"""
    ALL = 3
    """Handle the specified on completion type for both create and normal application calls"""


class StructArgDict(TypedDict):
    name: str
    elements: list[list[str]]


OnCompleteActionName: TypeAlias = Literal[
    "no_op", "opt_in", "close_out", "clear_state", "update_application", "delete_application"
]
"""String literals representing on completion transaction types"""
MethodConfigDict: TypeAlias = dict[OnCompleteActionName, CallConfig]
"""Dictionary of `dict[OnCompletionActionName, CallConfig]` representing allowed actions for each on completion type"""
DefaultArgumentType: TypeAlias = Literal["abi-method", "local-state", "global-state", "constant"]
"""Literal values describing the types of default argument sources"""


class DefaultArgumentDict(TypedDict):
    """
    DefaultArgument is a container for any arguments that may
    be resolved prior to calling some target method
    """

    source: DefaultArgumentType
    data: int | str | bytes | MethodDict


StateDict = TypedDict(  # need to use function-form of TypedDict here since "global" is a reserved keyword
    "StateDict", {"global": AppSpecStateDict, "local": AppSpecStateDict}
)


@dataclasses.dataclass(kw_only=True)
class MethodHints:
    """MethodHints provides hints to the caller about how to call the method"""

    #: hint to indicate this method can be called through Dryrun
    read_only: bool = False
    #: hint to provide names for tuple argument indices
    #: method_name=>param_name=>{name:str, elements:[str,str]}
    structs: dict[str, StructArgDict] = dataclasses.field(default_factory=dict)
    #: defaults
    default_arguments: dict[str, DefaultArgumentDict] = dataclasses.field(default_factory=dict)
    call_config: MethodConfigDict = dataclasses.field(default_factory=dict)

    def empty(self) -> bool:
        return not self.dictify()

    def dictify(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.read_only:
            d["read_only"] = True
        if self.default_arguments:
            d["default_arguments"] = self.default_arguments
        if self.structs:
            d["structs"] = self.structs
        if any(v for v in self.call_config.values() if v != CallConfig.NEVER):
            d["call_config"] = _encode_method_config(self.call_config)
        return d

    @staticmethod
    def undictify(data: dict[str, Any]) -> "MethodHints":
        return MethodHints(
            read_only=data.get("read_only", False),
            default_arguments=data.get("default_arguments", {}),
            structs=data.get("structs", {}),
            call_config=_decode_method_config(data.get("call_config", {})),
        )


def _encode_method_config(mc: MethodConfigDict) -> dict[str, str | None]:
    return {k: mc[k].name for k in sorted(mc) if mc[k] != CallConfig.NEVER}


def _decode_method_config(data: dict[OnCompleteActionName, Any]) -> MethodConfigDict:
    return {k: CallConfig[v] for k, v in data.items()}


def _encode_source(teal_text: str) -> str:
    return base64.b64encode(teal_text.encode()).decode("utf-8")


def _decode_source(b64_text: str) -> str:
    return base64.b64decode(b64_text).decode("utf-8")


def _encode_state_schema(schema: StateSchema) -> dict[str, int]:
    return {
        "num_byte_slices": schema.num_byte_slices,
        "num_uints": schema.num_uints,
    }


def _decode_state_schema(data: dict[str, int]) -> StateSchema:
    return StateSchema(  # type: ignore[no-untyped-call]
        num_byte_slices=data.get("num_byte_slices", 0),
        num_uints=data.get("num_uints", 0),
    )


@dataclasses.dataclass(kw_only=True)
class ApplicationSpecification:
    """ARC-0032 application specification

    See <https://github.com/algorandfoundation/ARCs/pull/150>"""

    approval_program: str
    clear_program: str
    contract: Contract
    hints: dict[str, MethodHints]
    schema: StateDict
    global_state_schema: StateSchema
    local_state_schema: StateSchema
    bare_call_config: MethodConfigDict

    def dictify(self) -> dict:
        return {
            "hints": {k: v.dictify() for k, v in self.hints.items() if not v.empty()},
            "source": {
                "approval": _encode_source(self.approval_program),
                "clear": _encode_source(self.clear_program),
            },
            "state": {
                "global": _encode_state_schema(self.global_state_schema),
                "local": _encode_state_schema(self.local_state_schema),
            },
            "schema": self.schema,
            "contract": self.contract.dictify(),
            "bare_call_config": _encode_method_config(self.bare_call_config),
        }

    def to_json(self) -> str:
        return json.dumps(self.dictify(), indent=4)

    @staticmethod
    def from_json(application_spec: str) -> "ApplicationSpecification":
        json_spec = json.loads(application_spec)
        return ApplicationSpecification(
            approval_program=_decode_source(json_spec["source"]["approval"]),
            clear_program=_decode_source(json_spec["source"]["clear"]),
            schema=json_spec["schema"],
            global_state_schema=_decode_state_schema(json_spec["state"]["global"]),
            local_state_schema=_decode_state_schema(json_spec["state"]["local"]),
            contract=Contract.undictify(json_spec["contract"]),
            hints={k: MethodHints.undictify(v) for k, v in json_spec["hints"].items()},
            bare_call_config=_decode_method_config(json_spec.get("bare_call_config", {})),
        )

    def export(self, directory: Path | str | None = None) -> None:
        """write out the artifacts generated by the application to disk

        Args:
            directory(optional): path to the directory where the artifacts should be written
        """
        if directory is None:
            output_dir = Path.cwd()
        else:
            output_dir = Path(directory)
            output_dir.mkdir(exist_ok=True, parents=True)

        (output_dir / "approval.teal").write_text(self.approval_program)
        (output_dir / "clear.teal").write_text(self.clear_program)
        (output_dir / "contract.json").write_text(json.dumps(self.contract.dictify(), indent=4))
        (output_dir / "application.json").write_text(self.to_json())


def _state_schema(schema: dict[str, int]) -> StateSchema:
    return StateSchema(schema.get("num-uint", 0), schema.get("num-byte-slice", 0))  # type: ignore[no-untyped-call]

# === File: algokit_utils/_transfer.py ===
import dataclasses
import logging
from typing import TYPE_CHECKING

import algosdk.transaction
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.transaction import AssetTransferTxn, PaymentTxn, SuggestedParams

from algokit_utils.models import Account

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient

__all__ = ["TransferParameters", "transfer", "TransferAssetParameters", "transfer_asset"]
logger = logging.getLogger(__name__)


@dataclasses.dataclass(kw_only=True)
class TransferParametersBase:
    """Parameters for transferring µALGOs between accounts

    Args:
        from_account (Account | AccountTransactionSigner): The account (with private key) or signer that will send
            the µALGOs
        to_address (str): The account address that will receive the µALGOs
        suggested_params (SuggestedParams | None): (optional) transaction parameters
        note (str | bytes | None): (optional) transaction note
        fee_micro_algos (int | None): (optional) The flat fee you want to pay, useful for covering extra fees in a
            transaction group or app call
        max_fee_micro_algos (int | None): (optional) The maximum fee that you are happy to pay (default: unbounded)
            - if this is set it's possible the transaction could get rejected during network congestion
    """

    from_account: Account | AccountTransactionSigner
    to_address: str
    suggested_params: SuggestedParams | None = None
    note: str | bytes | None = None
    fee_micro_algos: int | None = None
    max_fee_micro_algos: int | None = None


@dataclasses.dataclass(kw_only=True)
class TransferParameters(TransferParametersBase):
    """Parameters for transferring µALGOs between accounts"""

    micro_algos: int


@dataclasses.dataclass(kw_only=True)
class TransferAssetParameters(TransferParametersBase):
    """Parameters for transferring assets between accounts

    Args:
       asset_id (int): The asset id that will be transfered
       amount (int): The amount to send
       clawback_from (str | None): An address of a target account from which to perform a clawback operation. Please
           note, in such cases senderAccount must be equal to clawback field on ASA metadata.
    """

    asset_id: int
    amount: int
    clawback_from: str | None = None


def _check_fee(transaction: PaymentTxn | AssetTransferTxn, max_fee: int | None) -> None:
    if max_fee is not None:
        # Once a transaction has been constructed by algosdk, transaction.fee indicates what the total transaction fee
        # Will be based on the current suggested fee-per-byte value.
        if transaction.fee > max_fee:
            raise Exception(
                f"Cancelled transaction due to high network congestion fees. "
                f"Algorand suggested fees would cause this transaction to cost {transaction.fee} µALGOs. "
                f"Cap for this transaction is {max_fee} µALGOs."
            )
        if transaction.fee > algosdk.constants.MIN_TXN_FEE:
            logger.warning(
                f"Algorand network congestion fees are in effect. "
                f"This transaction will incur a fee of {transaction.fee} µALGOs."
            )


def transfer(client: "AlgodClient", parameters: TransferParameters) -> PaymentTxn:
    """Transfer µALGOs between accounts"""

    params = parameters
    params.suggested_params = parameters.suggested_params or client.suggested_params()
    from_account = params.from_account
    sender = _get_address(from_account)
    transaction = PaymentTxn(
        sender=sender,
        receiver=params.to_address,
        amt=params.micro_algos,
        note=params.note.encode("utf-8") if isinstance(params.note, str) else params.note,
        sp=params.suggested_params,
    )  # type: ignore[no-untyped-call]

    result = _send_transaction(client=client, transaction=transaction, parameters=params)
    assert isinstance(result, PaymentTxn)
    return result


def transfer_asset(client: "AlgodClient", parameters: TransferAssetParameters) -> AssetTransferTxn:
    """Transfer assets between accounts"""

    params = parameters
    params.suggested_params = parameters.suggested_params or client.suggested_params()
    sender = _get_address(parameters.from_account)
    suggested_params = parameters.suggested_params or client.suggested_params()
    xfer_txn = AssetTransferTxn(
        sp=suggested_params,
        sender=sender,
        receiver=params.to_address,
        close_assets_to=None,
        revocation_target=params.clawback_from,
        amt=params.amount,
        note=params.note,
        index=params.asset_id,
        rekey_to=None,
    )  # type: ignore[no-untyped-call]

    result = _send_transaction(client=client, transaction=xfer_txn, parameters=params)
    assert isinstance(result, AssetTransferTxn)
    return result


def _send_transaction(
    client: "AlgodClient",
    transaction: PaymentTxn | AssetTransferTxn,
    parameters: TransferAssetParameters | TransferParameters,
) -> PaymentTxn | AssetTransferTxn:
    if parameters.fee_micro_algos:
        transaction.fee = parameters.fee_micro_algos

    if parameters.suggested_params is not None and not parameters.suggested_params.flat_fee:
        _check_fee(transaction, parameters.max_fee_micro_algos)

    signed_transaction = transaction.sign(parameters.from_account.private_key)  # type: ignore[no-untyped-call]
    client.send_transaction(signed_transaction)

    txid = transaction.get_txid()  # type: ignore[no-untyped-call]
    logger.debug(f"Sent transaction {txid} type={transaction.type} from {_get_address(parameters.from_account)}")

    return transaction


def _get_address(account: Account | AccountTransactionSigner) -> str:
    if type(account) is Account:
        return account.address
    else:
        address = address_from_private_key(account.private_key)  # type: ignore[no-untyped-call]
        return str(address)

# === File: algokit_utils/dispenser_api.py ===
import contextlib
import enum
import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


class DispenserApiConfig:
    BASE_URL = "https://api.dispenser.algorandfoundation.tools"


class DispenserAssetName(enum.IntEnum):
    ALGO = 0


@dataclass
class DispenserAsset:
    asset_id: int
    decimals: int
    description: str


@dataclass
class DispenserFundResponse:
    tx_id: str
    amount: int


@dataclass
class DispenserLimitResponse:
    amount: int


DISPENSER_ASSETS = {
    DispenserAssetName.ALGO: DispenserAsset(
        asset_id=0,
        decimals=6,
        description="Algo",
    ),
}
DISPENSER_REQUEST_TIMEOUT = 15
DISPENSER_ACCESS_TOKEN_KEY = "ALGOKIT_DISPENSER_ACCESS_TOKEN"


@dataclass
class BaseDispenserApiClientParams:
    request_timeout: int = DISPENSER_REQUEST_TIMEOUT


@dataclass
class TestNetDispenserApiClientParams(BaseDispenserApiClientParams):
    auth_token: str | None = None


class TestNetDispenserApiClient:
    """
    Client for interacting with the [AlgoKit TestNet Dispenser API](https://github.com/algorandfoundation/algokit/blob/main/docs/testnet_api.md).
    To get started create a new access token via `algokit dispenser login --ci`
    and pass it to the client constructor as `auth_token`.
    Alternatively set the access token as environment variable `ALGOKIT_DISPENSER_ACCESS_TOKEN`,
    and it will be auto loaded. If both are set, the constructor argument takes precedence.

    Default request timeout is 15 seconds. Modify by passing `request_timeout` to the constructor.
    """

    auth_token: str
    request_timeout: int

    def __init__(self, params: TestNetDispenserApiClientParams | None = None) -> None:
        auth_token_from_env = os.getenv(DISPENSER_ACCESS_TOKEN_KEY)

        if params and params.auth_token:
            self.auth_token = params.auth_token
        elif auth_token_from_env:
            self.auth_token = auth_token_from_env
        else:
            raise Exception(
                f"Can't init AlgoKit TestNet Dispenser API client "
                f"because neither environment variable {DISPENSER_ACCESS_TOKEN_KEY} or "
                "the auth_token were provided."
            )

        self.request_timeout = params.request_timeout if params else DISPENSER_REQUEST_TIMEOUT

    def _process_dispenser_request(
        self, *, auth_token: str, url_suffix: str, data: dict | None = None, method: str = "POST"
    ) -> httpx.Response:
        """
        Generalized method to process http requests to dispenser API
        """

        headers = {"Authorization": f"Bearer {(auth_token)}"}

        # Set request arguments
        request_args = {
            "url": f"{DispenserApiConfig.BASE_URL}/{url_suffix}",
            "headers": headers,
            "timeout": self.request_timeout,
        }

        if method.upper() != "GET" and data is not None:
            request_args["json"] = data

        try:
            response: httpx.Response = getattr(httpx, method.lower())(**request_args)
            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as err:
            error_message = f"Error processing dispenser API request: {err.response.status_code}"
            error_response = None
            with contextlib.suppress(Exception):
                error_response = err.response.json()

            if error_response and error_response.get("code"):
                error_message = error_response.get("code")

            elif err.response.status_code == httpx.codes.BAD_REQUEST:
                error_message = err.response.json()["message"]

            raise Exception(error_message) from err

        except Exception as err:
            error_message = "Error processing dispenser API request"
            logger.debug(f"{error_message}: {err}", exc_info=True)
            raise err

    def fund(self, address: str, amount: int, asset_id: int) -> DispenserFundResponse:
        """
        Fund an account with Algos from the dispenser API
        """

        try:
            response = self._process_dispenser_request(
                auth_token=self.auth_token,
                url_suffix=f"fund/{asset_id}",
                data={"receiver": address, "amount": amount, "assetID": asset_id},
                method="POST",
            )

            content = response.json()
            return DispenserFundResponse(tx_id=content["txID"], amount=content["amount"])

        except Exception as err:
            logger.exception(f"Error funding account {address}: {err}")
            raise err

    def refund(self, refund_txn_id: str) -> None:
        """
        Register a refund for a transaction with the dispenser API
        """

        try:
            self._process_dispenser_request(
                auth_token=self.auth_token,
                url_suffix="refund",
                data={"refundTransactionID": refund_txn_id},
                method="POST",
            )

        except Exception as err:
            logger.exception(f"Error issuing refund for txn_id {refund_txn_id}: {err}")
            raise err

    def get_limit(
        self,
        address: str,
    ) -> DispenserLimitResponse:
        """
        Get current limit for an account with Algos from the dispenser API
        """

        try:
            response = self._process_dispenser_request(
                auth_token=self.auth_token,
                url_suffix=f"fund/{DISPENSER_ASSETS[DispenserAssetName.ALGO].asset_id}/limit",
                method="GET",
            )
            content = response.json()

            return DispenserLimitResponse(amount=content["amount"])
        except Exception as err:
            logger.exception(f"Error setting limit for account {address}: {err}")
            raise err

# === File: algokit_utils/logic_error.py ===
import re
from copy import copy
from typing import TYPE_CHECKING, TypedDict

from algokit_utils.models import SimulationTrace

if TYPE_CHECKING:
    from algosdk.source_map import SourceMap as AlgoSourceMap

__all__ = [
    "LogicError",
    "parse_logic_error",
]

LOGIC_ERROR = (
    ".*transaction (?P<transaction_id>[A-Z0-9]+): logic eval error: (?P<message>.*). Details: .*pc=(?P<pc>[0-9]+).*"
)


class LogicErrorData(TypedDict):
    transaction_id: str
    message: str
    pc: int


def parse_logic_error(
    error_str: str,
) -> LogicErrorData | None:
    match = re.match(LOGIC_ERROR, error_str)
    if match is None:
        return None

    return {
        "transaction_id": match.group("transaction_id"),
        "message": match.group("message"),
        "pc": int(match.group("pc")),
    }


class LogicError(Exception):
    def __init__(  # noqa: PLR0913
        self,
        *,
        logic_error_str: str,
        program: str,
        source_map: "AlgoSourceMap | None",
        transaction_id: str,
        message: str,
        pc: int,
        logic_error: Exception | None = None,
        traces: list[SimulationTrace] | None = None,
    ):
        self.logic_error = logic_error
        self.logic_error_str = logic_error_str
        self.program = program
        self.source_map = source_map
        self.lines = program.split("\n")
        self.transaction_id = transaction_id
        self.message = message
        self.pc = pc
        self.traces = traces

        self.line_no = self.source_map.get_line_for_pc(self.pc) if self.source_map else None

    def __str__(self) -> str:
        return (
            f"Txn {self.transaction_id} had error '{self.message}' at PC {self.pc}"
            + (":" if self.line_no is None else f" and Source Line {self.line_no}:")
            + f"\n{self.trace()}"
        )

    def trace(self, lines: int = 5) -> str:
        if self.line_no is None:
            return """
Could not determine TEAL source line for the error as no approval source map was provided, to receive a trace of the
error please provide an approval SourceMap. Either by:
    1.) Providing template_values when creating the ApplicationClient, so a SourceMap can be obtained automatically OR
    2.) Set approval_source_map from a previously compiled approval program OR
    3.) Import a previously exported source map using import_source_map"""

        program_lines = copy(self.lines)
        program_lines[self.line_no] += "\t\t<-- Error"
        lines_before = max(0, self.line_no - lines)
        lines_after = min(len(program_lines), self.line_no + lines)
        return "\n\t" + "\n\t".join(program_lines[lines_before:lines_after])

# === File: algokit_utils/application_client.py ===
import base64
import copy
import json
import logging
import re
import typing
from math import ceil
from pathlib import Path
from typing import Any, Literal, cast, overload

import algosdk
from algosdk import transaction
from algosdk.abi import ABIType, Method, Returns
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import (
    ABI_RETURN_HASH,
    ABIResult,
    AccountTransactionSigner,
    AtomicTransactionComposer,
    AtomicTransactionResponse,
    LogicSigTransactionSigner,
    MultisigTransactionSigner,
    SimulateAtomicTransactionResponse,
    TransactionSigner,
    TransactionWithSigner,
)
from algosdk.constants import APP_PAGE_MAX_SIZE
from algosdk.logic import get_application_address
from algosdk.source_map import SourceMap

import algokit_utils.application_specification as au_spec
import algokit_utils.deploy as au_deploy
from algokit_utils._debugging import (
    PersistSourceMapInput,
    persist_sourcemaps,
    simulate_and_persist_response,
    simulate_response,
)
from algokit_utils.common import Program
from algokit_utils.config import config
from algokit_utils.logic_error import LogicError, parse_logic_error
from algokit_utils.models import (
    ABIArgsDict,
    ABIArgType,
    ABIMethod,
    ABITransactionResponse,
    Account,
    CreateCallParameters,
    CreateCallParametersDict,
    OnCompleteCallParameters,
    OnCompleteCallParametersDict,
    SimulationTrace,
    TransactionParameters,
    TransactionParametersDict,
    TransactionResponse,
)

if typing.TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient
    from algosdk.v2client.indexer import IndexerClient


logger = logging.getLogger(__name__)


"""A dictionary `dict[str, Any]` representing ABI argument names and values"""

__all__ = [
    "ApplicationClient",
    "execute_atc_with_logic_error",
    "get_next_version",
    "get_sender_from_signer",
    "num_extra_program_pages",
]

"""Alias for {py:class}`pyteal.ABIReturnSubroutine`, {py:class}`algosdk.abi.method.Method` or a {py:class}`str`
representing an ABI method name or signature"""


def num_extra_program_pages(approval: bytes, clear: bytes) -> int:
    """Calculate minimum number of extra_pages required for provided approval and clear programs"""

    return ceil(((len(approval) + len(clear)) - APP_PAGE_MAX_SIZE) / APP_PAGE_MAX_SIZE)


class ApplicationClient:
    """A class that wraps an ARC-0032 app spec and provides high productivity methods to deploy and call the app"""

    @overload
    def __init__(
        self,
        algod_client: "AlgodClient",
        app_spec: au_spec.ApplicationSpecification | Path,
        *,
        app_id: int = 0,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        template_values: au_deploy.TemplateValueMapping | None = None,
    ): ...

    @overload
    def __init__(
        self,
        algod_client: "AlgodClient",
        app_spec: au_spec.ApplicationSpecification | Path,
        *,
        creator: str | Account,
        indexer_client: "IndexerClient | None" = None,
        existing_deployments: au_deploy.AppLookup | None = None,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        template_values: au_deploy.TemplateValueMapping | None = None,
        app_name: str | None = None,
    ): ...

    def __init__(  # noqa: PLR0913
        self,
        algod_client: "AlgodClient",
        app_spec: au_spec.ApplicationSpecification | Path,
        *,
        app_id: int = 0,
        creator: str | Account | None = None,
        indexer_client: "IndexerClient | None" = None,
        existing_deployments: au_deploy.AppLookup | None = None,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        template_values: au_deploy.TemplateValueMapping | None = None,
        app_name: str | None = None,
    ):
        """ApplicationClient can be created with an app_id to interact with an existing application, alternatively
        it can be created with a creator and indexer_client specified to find existing applications by name and creator.

        :param AlgodClient algod_client: AlgoSDK algod client
        :param ApplicationSpecification | Path app_spec: An Application Specification or the path to one
        :param int app_id: The app_id of an existing application, to instead find the application by creator and name
        use the creator and indexer_client parameters
        :param str | Account creator: The address or Account of the app creator to resolve the app_id
        :param IndexerClient indexer_client: AlgoSDK indexer client, only required if deploying or finding app_id by
        creator and app name
        :param AppLookup existing_deployments:
        :param TransactionSigner | Account signer: Account or signer to use to sign transactions, if not specified and
        creator was passed as an Account will use that.
        :param str sender: Address to use as the sender for all transactions, will use the address associated with the
        signer if not specified.
        :param TemplateValueMapping template_values: Values to use for TMPL_* template variables, dictionary keys should
        *NOT* include the TMPL_ prefix
        :param str | None app_name: Name of application to use when deploying, defaults to name defined on the
        Application Specification
        """
        self.algod_client = algod_client
        self.app_spec = (
            au_spec.ApplicationSpecification.from_json(app_spec.read_text()) if isinstance(app_spec, Path) else app_spec
        )
        self._app_name = app_name
        self._approval_program: Program | None = None
        self._approval_source_map: SourceMap | None = None
        self._clear_program: Program | None = None

        self.template_values: au_deploy.TemplateValueMapping = template_values or {}
        self.existing_deployments = existing_deployments
        self._indexer_client = indexer_client
        if creator is not None:
            if not self.existing_deployments and not self._indexer_client:
                raise Exception(
                    "If using the creator parameter either existing_deployments or indexer_client must also be provided"
                )
            self._creator: str | None = creator.address if isinstance(creator, Account) else creator
            if self.existing_deployments and self.existing_deployments.creator != self._creator:
                raise Exception(
                    "Attempt to create application client with invalid existing_deployments against"
                    f"a different creator ({self.existing_deployments.creator} instead of "
                    f"expected creator {self._creator}"
                )
            self.app_id = 0
        else:
            self.app_id = app_id
            self._creator = None

        self.signer: TransactionSigner | None
        if signer:
            self.signer = (
                signer if isinstance(signer, TransactionSigner) else AccountTransactionSigner(signer.private_key)
            )
        elif isinstance(creator, Account):
            self.signer = AccountTransactionSigner(creator.private_key)
        else:
            self.signer = None

        self.sender = sender
        self.suggested_params = suggested_params

    @property
    def app_name(self) -> str:
        return self._app_name or self.app_spec.contract.name

    @app_name.setter
    def app_name(self, value: str) -> None:
        self._app_name = value

    @property
    def app_address(self) -> str:
        return get_application_address(self.app_id)

    @property
    def approval(self) -> Program | None:
        return self._approval_program

    @property
    def approval_source_map(self) -> SourceMap | None:
        if self._approval_source_map:
            return self._approval_source_map
        if self._approval_program:
            return self._approval_program.source_map
        return None

    @approval_source_map.setter
    def approval_source_map(self, value: SourceMap) -> None:
        self._approval_source_map = value

    @property
    def clear(self) -> Program | None:
        return self._clear_program

    def prepare(
        self,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        app_id: int | None = None,
        template_values: au_deploy.TemplateValueDict | None = None,
    ) -> "ApplicationClient":
        """Creates a copy of this ApplicationClient, using the new signer, sender and app_id values if provided.
        Will also substitute provided template_values into the associated app_spec in the copy"""
        new_client: ApplicationClient = copy.copy(self)
        new_client._prepare(  # noqa: SLF001
            new_client, signer=signer, sender=sender, app_id=app_id, template_values=template_values
        )
        return new_client

    def _prepare(  # noqa: PLR0913
        self,
        target: "ApplicationClient",
        *,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        app_id: int | None = None,
        template_values: au_deploy.TemplateValueDict | None = None,
    ) -> None:
        target.app_id = self.app_id if app_id is None else app_id
        target.signer, target.sender = target.get_signer_sender(
            AccountTransactionSigner(signer.private_key) if isinstance(signer, Account) else signer, sender
        )
        target.template_values = {**self.template_values, **(template_values or {})}

    def deploy(  # noqa: PLR0913
        self,
        version: str | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        allow_update: bool | None = None,
        allow_delete: bool | None = None,
        on_update: au_deploy.OnUpdate = au_deploy.OnUpdate.Fail,
        on_schema_break: au_deploy.OnSchemaBreak = au_deploy.OnSchemaBreak.Fail,
        template_values: au_deploy.TemplateValueMapping | None = None,
        create_args: au_deploy.ABICreateCallArgs
        | au_deploy.ABICreateCallArgsDict
        | au_deploy.DeployCreateCallArgs
        | None = None,
        update_args: au_deploy.ABICallArgs | au_deploy.ABICallArgsDict | au_deploy.DeployCallArgs | None = None,
        delete_args: au_deploy.ABICallArgs | au_deploy.ABICallArgsDict | au_deploy.DeployCallArgs | None = None,
    ) -> au_deploy.DeployResponse:
        """Deploy an application and update client to reference it.

        Idempotently deploy (create, update/delete if changed) an app against the given name via the given creator
        account, including deploy-time template placeholder substitutions.
        To understand the architecture decisions behind this functionality please see
        <https://github.com/algorandfoundation/algokit-cli/blob/main/docs/architecture-decisions/2023-01-12_smart-contract-deployment.md>

        ```{note}
        If there is a breaking state schema change to an existing app (and `on_schema_break` is set to
        'ReplaceApp' the existing app will be deleted and re-created.
        ```

        ```{note}
        If there is an update (different TEAL code) to an existing app (and `on_update` is set to 'ReplaceApp')
        the existing app will be deleted and re-created.
        ```

        :param str version: version to use when creating or updating app, if None version will be auto incremented
        :param algosdk.atomic_transaction_composer.TransactionSigner signer: signer to use when deploying app
        , if None uses self.signer
        :param str sender: sender address to use when deploying app, if None uses self.sender
        :param bool allow_delete: Used to set the `TMPL_DELETABLE` template variable to conditionally control if an app
        can be deleted
        :param bool allow_update: Used to set the `TMPL_UPDATABLE` template variable to conditionally control if an app
        can be updated
        :param OnUpdate on_update: Determines what action to take if an application update is required
        :param OnSchemaBreak on_schema_break: Determines what action to take if an application schema requirements
        has increased beyond the current allocation
        :param dict[str, int|str|bytes] template_values: Values to use for `TMPL_*` template variables, dictionary keys
        should *NOT* include the TMPL_ prefix
        :param ABICreateCallArgs create_args: Arguments used when creating an application
        :param ABICallArgs | ABICallArgsDict update_args: Arguments used when updating an application
        :param ABICallArgs | ABICallArgsDict delete_args: Arguments used when deleting an application
        :return DeployResponse: details action taken and relevant transactions
        :raises DeploymentError: If the deployment failed
        """
        # check inputs
        if self.app_id:
            raise au_deploy.DeploymentFailedError(
                f"Attempt to deploy app which already has an app index of {self.app_id}"
            )
        try:
            resolved_signer, resolved_sender = self.resolve_signer_sender(signer, sender)
        except ValueError as ex:
            raise au_deploy.DeploymentFailedError(f"{ex}, unable to deploy app") from None
        if not self._creator:
            raise au_deploy.DeploymentFailedError("No creator provided, unable to deploy app")
        if self._creator != resolved_sender:
            raise au_deploy.DeploymentFailedError(
                f"Attempt to deploy contract with a sender address {resolved_sender} that differs "
                f"from the given creator address for this application client: {self._creator}"
            )

        # make a copy and prepare variables
        template_values = {**self.template_values, **(template_values or {})}
        au_deploy.add_deploy_template_variables(template_values, allow_update=allow_update, allow_delete=allow_delete)

        existing_app_metadata_or_reference = self._load_app_reference()

        self._approval_program, self._clear_program = substitute_template_and_compile(
            self.algod_client, self.app_spec, template_values
        )

        if config.debug and config.project_root:
            persist_sourcemaps(
                sources=[
                    PersistSourceMapInput(
                        compiled_teal=self._approval_program, app_name=self.app_name, file_name="approval.teal"
                    ),
                    PersistSourceMapInput(
                        compiled_teal=self._clear_program, app_name=self.app_name, file_name="clear.teal"
                    ),
                ],
                project_root=config.project_root,
                client=self.algod_client,
                with_sources=True,
            )

        deployer = au_deploy.Deployer(
            app_client=self,
            creator=self._creator,
            signer=resolved_signer,
            sender=resolved_sender,
            new_app_metadata=self._get_app_deploy_metadata(version, allow_update, allow_delete),
            existing_app_metadata_or_reference=existing_app_metadata_or_reference,
            on_update=on_update,
            on_schema_break=on_schema_break,
            create_args=create_args,
            update_args=update_args,
            delete_args=delete_args,
        )

        return deployer.deploy()

    def compose_create(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with application id == 0 and the schema and source of client's app_spec to atc"""
        approval_program, clear_program = self._check_is_compiled()
        transaction_parameters = _convert_transaction_parameters(transaction_parameters)

        extra_pages = transaction_parameters.extra_pages or num_extra_program_pages(
            approval_program.raw_binary, clear_program.raw_binary
        )

        self.add_method_call(
            atc,
            app_id=0,
            abi_method=call_abi_method,
            abi_args=abi_kwargs,
            on_complete=transaction_parameters.on_complete or transaction.OnComplete.NoOpOC,
            call_config=au_spec.CallConfig.CREATE,
            parameters=transaction_parameters,
            approval_program=approval_program.raw_binary,
            clear_program=clear_program.raw_binary,
            global_schema=self.app_spec.global_state_schema,
            local_schema=self.app_spec.local_state_schema,
            extra_pages=extra_pages,
        )

    @overload
    def create(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = ...,
    ) -> TransactionResponse: ...

    @overload
    def create(
        self,
        call_abi_method: ABIMethod | Literal[True],
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse: ...

    @overload
    def create(
        self,
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse: ...

    def create(
        self,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with application id == 0 and the schema and source of client's app_spec"""

        atc = AtomicTransactionComposer()

        self.compose_create(
            atc,
            call_abi_method,
            transaction_parameters,
            **abi_kwargs,
        )
        create_result = self._execute_atc_tr(atc)
        self.app_id = au_deploy.get_app_id_from_tx_id(self.algod_client, create_result.tx_id)
        return create_result

    def compose_update(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with on_complete=UpdateApplication to atc"""
        approval_program, clear_program = self._check_is_compiled()

        self.add_method_call(
            atc=atc,
            abi_method=call_abi_method,
            abi_args=abi_kwargs,
            parameters=transaction_parameters,
            on_complete=transaction.OnComplete.UpdateApplicationOC,
            approval_program=approval_program.raw_binary,
            clear_program=clear_program.raw_binary,
        )

    @overload
    def update(
        self,
        call_abi_method: ABIMethod | Literal[True],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse: ...

    @overload
    def update(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
    ) -> TransactionResponse: ...

    @overload
    def update(
        self,
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse: ...

    def update(
        self,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with on_complete=UpdateApplication"""

        atc = AtomicTransactionComposer()
        self.compose_update(
            atc,
            call_abi_method,
            transaction_parameters=transaction_parameters,
            **abi_kwargs,
        )
        return self._execute_atc_tr(atc)

    def compose_delete(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with on_complete=DeleteApplication to atc"""

        self.add_method_call(
            atc,
            call_abi_method,
            abi_args=abi_kwargs,
            parameters=transaction_parameters,
            on_complete=transaction.OnComplete.DeleteApplicationOC,
        )

    @overload
    def delete(
        self,
        call_abi_method: ABIMethod | Literal[True],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse: ...

    @overload
    def delete(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
    ) -> TransactionResponse: ...

    @overload
    def delete(
        self,
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse: ...

    def delete(
        self,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with on_complete=DeleteApplication"""

        atc = AtomicTransactionComposer()
        self.compose_delete(
            atc,
            call_abi_method,
            transaction_parameters=transaction_parameters,
            **abi_kwargs,
        )
        return self._execute_atc_tr(atc)

    def compose_call(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with specified parameters to atc"""
        _parameters = _convert_transaction_parameters(transaction_parameters)
        self.add_method_call(
            atc,
            abi_method=call_abi_method,
            abi_args=abi_kwargs,
            parameters=_parameters,
            on_complete=_parameters.on_complete or transaction.OnComplete.NoOpOC,
        )

    @overload
    def call(
        self,
        call_abi_method: ABIMethod | Literal[True],
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse: ...

    @overload
    def call(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = ...,
    ) -> TransactionResponse: ...

    @overload
    def call(
        self,
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse: ...

    def call(
        self,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with specified parameters"""
        atc = AtomicTransactionComposer()
        _parameters = _convert_transaction_parameters(transaction_parameters)
        self.compose_call(
            atc,
            call_abi_method=call_abi_method,
            transaction_parameters=_parameters,
            **abi_kwargs,
        )

        method = self._resolve_method(
            call_abi_method, abi_kwargs, _parameters.on_complete or transaction.OnComplete.NoOpOC
        )
        if method:
            hints = self._method_hints(method)
            if hints and hints.read_only:
                if config.debug and config.project_root and config.trace_all:
                    simulate_and_persist_response(
                        atc, config.project_root, self.algod_client, config.trace_buffer_size_mb
                    )

                return self._simulate_readonly_call(method, atc)

        return self._execute_atc_tr(atc)

    def compose_opt_in(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with on_complete=OptIn to atc"""
        self.add_method_call(
            atc,
            abi_method=call_abi_method,
            abi_args=abi_kwargs,
            parameters=transaction_parameters,
            on_complete=transaction.OnComplete.OptInOC,
        )

    @overload
    def opt_in(
        self,
        call_abi_method: ABIMethod | Literal[True] = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse: ...

    @overload
    def opt_in(
        self,
        call_abi_method: Literal[False] = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
    ) -> TransactionResponse: ...

    @overload
    def opt_in(
        self,
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse: ...

    def opt_in(
        self,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with on_complete=OptIn"""
        atc = AtomicTransactionComposer()
        self.compose_opt_in(
            atc,
            call_abi_method=call_abi_method,
            transaction_parameters=transaction_parameters,
            **abi_kwargs,
        )
        return self._execute_atc_tr(atc)

    def compose_close_out(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with on_complete=CloseOut to ac"""
        self.add_method_call(
            atc,
            abi_method=call_abi_method,
            abi_args=abi_kwargs,
            parameters=transaction_parameters,
            on_complete=transaction.OnComplete.CloseOutOC,
        )

    @overload
    def close_out(
        self,
        call_abi_method: ABIMethod | Literal[True],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse: ...

    @overload
    def close_out(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
    ) -> TransactionResponse: ...

    @overload
    def close_out(
        self,
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse: ...

    def close_out(
        self,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with on_complete=CloseOut"""
        atc = AtomicTransactionComposer()
        self.compose_close_out(
            atc,
            call_abi_method=call_abi_method,
            transaction_parameters=transaction_parameters,
            **abi_kwargs,
        )
        return self._execute_atc_tr(atc)

    def compose_clear_state(
        self,
        atc: AtomicTransactionComposer,
        /,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        app_args: list[bytes] | None = None,
    ) -> None:
        """Adds a signed transaction with on_complete=ClearState to atc"""
        return self.add_method_call(
            atc,
            parameters=transaction_parameters,
            on_complete=transaction.OnComplete.ClearStateOC,
            app_args=app_args,
        )

    def clear_state(
        self,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        app_args: list[bytes] | None = None,
    ) -> TransactionResponse:
        """Submits a signed transaction with on_complete=ClearState"""
        atc = AtomicTransactionComposer()
        self.compose_clear_state(
            atc,
            transaction_parameters=transaction_parameters,
            app_args=app_args,
        )
        return self._execute_atc_tr(atc)

    def get_global_state(self, *, raw: bool = False) -> dict[bytes | str, bytes | str | int]:
        """Gets the global state info associated with app_id"""
        global_state = self.algod_client.application_info(self.app_id)
        assert isinstance(global_state, dict)
        return cast(
            dict[bytes | str, bytes | str | int],
            _decode_state(global_state.get("params", {}).get("global-state", {}), raw=raw),
        )

    def get_local_state(self, account: str | None = None, *, raw: bool = False) -> dict[bytes | str, bytes | str | int]:
        """Gets the local state info for associated app_id and account/sender"""

        if account is None:
            _, account = self.resolve_signer_sender(self.signer, self.sender)

        acct_state = self.algod_client.account_application_info(account, self.app_id)
        assert isinstance(acct_state, dict)
        return cast(
            dict[bytes | str, bytes | str | int],
            _decode_state(acct_state.get("app-local-state", {}).get("key-value", {}), raw=raw),
        )

    def resolve(self, to_resolve: au_spec.DefaultArgumentDict) -> int | str | bytes:
        """Resolves the default value for an ABI method, based on app_spec"""

        def _data_check(value: object) -> int | str | bytes:
            if isinstance(value, int | str | bytes):
                return value
            raise ValueError(f"Unexpected type for constant data: {value}")

        match to_resolve:
            case {"source": "constant", "data": data}:
                return _data_check(data)
            case {"source": "global-state", "data": str() as key}:
                global_state = self.get_global_state(raw=True)
                return global_state[key.encode()]
            case {"source": "local-state", "data": str() as key}:
                _, sender = self.resolve_signer_sender(self.signer, self.sender)
                acct_state = self.get_local_state(sender, raw=True)
                return acct_state[key.encode()]
            case {"source": "abi-method", "data": dict() as method_dict}:
                method = Method.undictify(method_dict)
                response = self.call(method)
                assert isinstance(response, ABITransactionResponse)
                return _data_check(response.return_value)

            case {"source": source}:
                raise ValueError(f"Unrecognized default argument source: {source}")
            case _:
                raise TypeError("Unable to interpret default argument specification")

    def _get_app_deploy_metadata(
        self, version: str | None, allow_update: bool | None, allow_delete: bool | None
    ) -> au_deploy.AppDeployMetaData:
        updatable = (
            allow_update
            if allow_update is not None
            else au_deploy.get_deploy_control(
                self.app_spec, au_deploy.UPDATABLE_TEMPLATE_NAME, transaction.OnComplete.UpdateApplicationOC
            )
        )
        deletable = (
            allow_delete
            if allow_delete is not None
            else au_deploy.get_deploy_control(
                self.app_spec, au_deploy.DELETABLE_TEMPLATE_NAME, transaction.OnComplete.DeleteApplicationOC
            )
        )

        app = self._load_app_reference()

        if version is None:
            if app.app_id == 0:
                version = "v1.0"
            else:
                assert isinstance(app, au_deploy.AppDeployMetaData)
                version = get_next_version(app.version)
        return au_deploy.AppDeployMetaData(self.app_name, version, updatable=updatable, deletable=deletable)

    def _check_is_compiled(self) -> tuple[Program, Program]:
        if self._approval_program is None or self._clear_program is None:
            self._approval_program, self._clear_program = substitute_template_and_compile(
                self.algod_client, self.app_spec, self.template_values
            )

        if config.debug and config.project_root:
            persist_sourcemaps(
                sources=[
                    PersistSourceMapInput(
                        compiled_teal=self._approval_program, app_name=self.app_name, file_name="approval.teal"
                    ),
                    PersistSourceMapInput(
                        compiled_teal=self._clear_program, app_name=self.app_name, file_name="clear.teal"
                    ),
                ],
                project_root=config.project_root,
                client=self.algod_client,
                with_sources=True,
            )

        return self._approval_program, self._clear_program

    def _simulate_readonly_call(
        self, method: Method, atc: AtomicTransactionComposer
    ) -> ABITransactionResponse | TransactionResponse:
        response = simulate_response(atc, self.algod_client)
        traces = None
        if config.debug:
            traces = _create_simulate_traces(response)
        if response.failure_message:
            raise _try_convert_to_logic_error(
                response.failure_message,
                self.app_spec.approval_program,
                self._get_approval_source_map,
                traces,
            ) or Exception(f"Simulate failed for readonly method {method.get_signature()}: {response.failure_message}")

        return TransactionResponse.from_atr(response)

    def _load_reference_and_check_app_id(self) -> None:
        self._load_app_reference()
        self._check_app_id()

    def _load_app_reference(self) -> au_deploy.AppReference | au_deploy.AppMetaData:
        if not self.existing_deployments and self._creator:
            assert self._indexer_client
            self.existing_deployments = au_deploy.get_creator_apps(self._indexer_client, self._creator)

        if self.existing_deployments:
            app = self.existing_deployments.apps.get(self.app_name)
            if app:
                if self.app_id == 0:
                    self.app_id = app.app_id
                return app

        return au_deploy.AppReference(self.app_id, self.app_address)

    def _check_app_id(self) -> None:
        if self.app_id == 0:
            raise Exception(
                "ApplicationClient is not associated with an app instance, to resolve either:\n"
                "1.) provide an app_id on construction OR\n"
                "2.) provide a creator address so an app can be searched for OR\n"
                "3.) create an app first using create or deploy methods"
            )

    def _resolve_method(
        self,
        abi_method: ABIMethod | bool | None,
        args: ABIArgsDict | None,
        on_complete: transaction.OnComplete,
        call_config: au_spec.CallConfig = au_spec.CallConfig.CALL,
    ) -> Method | None:
        matches: list[Method | None] = []
        match abi_method:
            case str() | Method():  # abi method specified
                return self._resolve_abi_method(abi_method)
            case bool() | None:  # find abi method
                has_bare_config = (
                    call_config in au_deploy.get_call_config(self.app_spec.bare_call_config, on_complete)
                    or on_complete == transaction.OnComplete.ClearStateOC
                )
                abi_methods = self._find_abi_methods(args, on_complete, call_config)
                if abi_method is not False:
                    matches += abi_methods
                if has_bare_config and abi_method is not True:
                    matches += [None]
            case _:
                return abi_method.method_spec()

        if len(matches) == 1:  # exact match
            return matches[0]
        elif len(matches) > 1:  # ambiguous match
            signatures = ", ".join((m.get_signature() if isinstance(m, Method) else "bare") for m in matches)
            raise Exception(
                f"Could not find an exact method to use for {on_complete.name} with call_config of {call_config.name}, "
                f"specify the exact method using abi_method and args parameters, considered: {signatures}"
            )
        else:  # no match
            raise Exception(
                f"Could not find any methods to use for {on_complete.name} with call_config of {call_config.name}"
            )

    def _get_approval_source_map(self) -> SourceMap | None:
        if self.approval_source_map:
            return self.approval_source_map

        try:
            approval, _ = self._check_is_compiled()
        except au_deploy.DeploymentFailedError:
            return None
        return approval.source_map

    def export_source_map(self) -> str | None:
        """Export approval source map to JSON, can be later re-imported with `import_source_map`"""
        source_map = self._get_approval_source_map()
        if source_map:
            return json.dumps(
                {
                    "version": source_map.version,
                    "sources": source_map.sources,
                    "mappings": source_map.mappings,
                }
            )
        return None

    def import_source_map(self, source_map_json: str) -> None:
        """Import approval source from JSON exported by `export_source_map`"""
        source_map = json.loads(source_map_json)
        self._approval_source_map = SourceMap(source_map)

    def add_method_call(  # noqa: PLR0913
        self,
        atc: AtomicTransactionComposer,
        abi_method: ABIMethod | bool | None = None,
        *,
        abi_args: ABIArgsDict | None = None,
        app_id: int | None = None,
        parameters: TransactionParameters | TransactionParametersDict | None = None,
        on_complete: transaction.OnComplete = transaction.OnComplete.NoOpOC,
        local_schema: transaction.StateSchema | None = None,
        global_schema: transaction.StateSchema | None = None,
        approval_program: bytes | None = None,
        clear_program: bytes | None = None,
        extra_pages: int | None = None,
        app_args: list[bytes] | None = None,
        call_config: au_spec.CallConfig = au_spec.CallConfig.CALL,
    ) -> None:
        """Adds a transaction to the AtomicTransactionComposer passed"""
        if app_id is None:
            self._load_reference_and_check_app_id()
            app_id = self.app_id
        parameters = _convert_transaction_parameters(parameters)
        method = self._resolve_method(abi_method, abi_args, on_complete, call_config)
        sp = parameters.suggested_params or self.suggested_params or self.algod_client.suggested_params()
        signer, sender = self.resolve_signer_sender(parameters.signer, parameters.sender)
        if parameters.boxes is not None:
            # TODO: algosdk actually does this, but it's type hints say otherwise...
            encoded_boxes = [(id_, algosdk.encoding.encode_as_bytes(name)) for id_, name in parameters.boxes]
        else:
            encoded_boxes = None

        encoded_lease = parameters.lease.encode("utf-8") if isinstance(parameters.lease, str) else parameters.lease

        if not method:  # not an abi method, treat as a regular call
            if abi_args:
                raise Exception(f"ABI arguments specified on a bare call: {', '.join(abi_args)}")
            atc.add_transaction(
                TransactionWithSigner(
                    txn=transaction.ApplicationCallTxn(  # type: ignore[no-untyped-call]
                        sender=sender,
                        sp=sp,
                        index=app_id,
                        on_complete=on_complete,
                        approval_program=approval_program,
                        clear_program=clear_program,
                        global_schema=global_schema,
                        local_schema=local_schema,
                        extra_pages=extra_pages,
                        accounts=parameters.accounts,
                        foreign_apps=parameters.foreign_apps,
                        foreign_assets=parameters.foreign_assets,
                        boxes=encoded_boxes,
                        note=parameters.note,
                        lease=encoded_lease,
                        rekey_to=parameters.rekey_to,
                        app_args=app_args,
                    ),
                    signer=signer,
                )
            )
            return
        # resolve ABI method args
        args = self._get_abi_method_args(abi_args, method)
        atc.add_method_call(
            app_id,
            method,
            sender,
            sp,
            signer,
            method_args=args,
            on_complete=on_complete,
            local_schema=local_schema,
            global_schema=global_schema,
            approval_program=approval_program,
            clear_program=clear_program,
            extra_pages=extra_pages or 0,
            accounts=parameters.accounts,
            foreign_apps=parameters.foreign_apps,
            foreign_assets=parameters.foreign_assets,
            boxes=encoded_boxes,
            note=parameters.note.encode("utf-8") if isinstance(parameters.note, str) else parameters.note,
            lease=encoded_lease,
            rekey_to=parameters.rekey_to,
        )

    def _get_abi_method_args(self, abi_args: ABIArgsDict | None, method: Method) -> list:
        args: list = []
        hints = self._method_hints(method)
        # copy args so we don't mutate original
        abi_args = dict(abi_args or {})
        for method_arg in method.args:
            name = method_arg.name
            if name in abi_args:
                argument = abi_args.pop(name)
                if isinstance(argument, dict):
                    if hints.structs is None or name not in hints.structs:
                        raise Exception(f"Argument missing struct hint: {name}. Check argument name and type")

                    elements = hints.structs[name]["elements"]

                    argument_tuple = tuple(argument[field_name] for field_name, field_type in elements)
                    args.append(argument_tuple)
                else:
                    args.append(argument)

            elif hints.default_arguments is not None and name in hints.default_arguments:
                default_arg = hints.default_arguments[name]
                if default_arg is not None:
                    args.append(self.resolve(default_arg))
            else:
                raise Exception(f"Unspecified argument: {name}")
        if abi_args:
            raise Exception(f"Unused arguments specified: {', '.join(abi_args)}")
        return args

    def _method_matches(
        self,
        method: Method,
        args: ABIArgsDict | None,
        on_complete: transaction.OnComplete,
        call_config: au_spec.CallConfig,
    ) -> bool:
        hints = self._method_hints(method)
        if call_config not in au_deploy.get_call_config(hints.call_config, on_complete):
            return False
        method_args = {m.name for m in method.args}
        provided_args = set(args or {}) | set(hints.default_arguments)

        # TODO: also match on types?
        return method_args == provided_args

    def _find_abi_methods(
        self, args: ABIArgsDict | None, on_complete: transaction.OnComplete, call_config: au_spec.CallConfig
    ) -> list[Method]:
        return [
            method
            for method in self.app_spec.contract.methods
            if self._method_matches(method, args, on_complete, call_config)
        ]

    def _resolve_abi_method(self, method: ABIMethod) -> Method:
        if isinstance(method, str):
            try:
                return next(iter(m for m in self.app_spec.contract.methods if m.get_signature() == method))
            except StopIteration:
                pass
            return self.app_spec.contract.get_method_by_name(method)
        elif hasattr(method, "method_spec"):
            return method.method_spec()
        else:
            return method

    def _method_hints(self, method: Method) -> au_spec.MethodHints:
        sig = method.get_signature()
        if sig not in self.app_spec.hints:
            return au_spec.MethodHints()
        return self.app_spec.hints[sig]

    def _execute_atc_tr(self, atc: AtomicTransactionComposer) -> TransactionResponse:
        result = self.execute_atc(atc)
        return TransactionResponse.from_atr(result)

    def execute_atc(self, atc: AtomicTransactionComposer) -> AtomicTransactionResponse:
        return execute_atc_with_logic_error(
            atc,
            self.algod_client,
            approval_program=self.app_spec.approval_program,
            approval_source_map=self._get_approval_source_map,
        )

    def get_signer_sender(
        self, signer: TransactionSigner | None = None, sender: str | None = None
    ) -> tuple[TransactionSigner | None, str | None]:
        """Return signer and sender, using default values on client if not specified

        Will use provided values if given, otherwise will fall back to values defined on client.
        If no sender is specified then will attempt to obtain sender from signer"""
        resolved_signer = signer or self.signer
        resolved_sender = sender or get_sender_from_signer(signer) or self.sender or get_sender_from_signer(self.signer)
        return resolved_signer, resolved_sender

    def resolve_signer_sender(
        self, signer: TransactionSigner | None = None, sender: str | None = None
    ) -> tuple[TransactionSigner, str]:
        """Return signer and sender, using default values on client if not specified

        Will use provided values if given, otherwise will fall back to values defined on client.
        If no sender is specified then will attempt to obtain sender from signer

        :raises ValueError: Raised if a signer or sender is not provided. See `get_signer_sender`
        for variant with no exception"""
        resolved_signer, resolved_sender = self.get_signer_sender(signer, sender)
        if not resolved_signer:
            raise ValueError("No signer provided")
        if not resolved_sender:
            raise ValueError("No sender provided")
        return resolved_signer, resolved_sender

    # TODO: remove private implementation, kept in the 1.0.2 release to not impact existing beaker 1.0 installs
    _resolve_signer_sender = resolve_signer_sender


def substitute_template_and_compile(
    algod_client: "AlgodClient",
    app_spec: au_spec.ApplicationSpecification,
    template_values: au_deploy.TemplateValueMapping,
) -> tuple[Program, Program]:
    """Substitutes the provided template_values into app_spec and compiles"""
    template_values = dict(template_values or {})
    clear = au_deploy.replace_template_variables(app_spec.clear_program, template_values)

    au_deploy.check_template_variables(app_spec.approval_program, template_values)
    approval = au_deploy.replace_template_variables(app_spec.approval_program, template_values)

    approval_app, clear_app = Program(approval, algod_client), Program(clear, algod_client)

    return approval_app, clear_app


def get_next_version(current_version: str) -> str:
    """Calculates the next version from `current_version`

    Next version is calculated by finding a semver like
    version string and incrementing the lower. This function is used by {py:meth}`ApplicationClient.deploy` when
    a version is not specified, and is intended mostly for convenience during local development.

    :params str current_version: An existing version string with a semver like version contained within it,
    some valid inputs and incremented outputs:
    `1` -> `2`
    `1.0` -> `1.1`
    `v1.1` -> `v1.2`
    `v1.1-beta1` -> `v1.2-beta1`
    `v1.2.3.4567` -> `v1.2.3.4568`
    `v1.2.3.4567-alpha` -> `v1.2.3.4568-alpha`
    :raises DeploymentFailedError: If `current_version` cannot be parsed"""
    pattern = re.compile(r"(?P<prefix>\w*)(?P<version>(?:\d+\.)*\d+)(?P<suffix>\w*)")
    match = pattern.match(current_version)
    if match:
        version = match.group("version")
        new_version = _increment_version(version)

        def replacement(m: re.Match) -> str:
            return f"{m.group('prefix')}{new_version}{m.group('suffix')}"

        return re.sub(pattern, replacement, current_version)
    raise au_deploy.DeploymentFailedError(
        f"Could not auto increment {current_version}, please specify the next version using the version parameter"
    )


def _try_convert_to_logic_error(
    source_ex: Exception | str,
    approval_program: str,
    approval_source_map: SourceMap | typing.Callable[[], SourceMap | None] | None = None,
    simulate_traces: list[SimulationTrace] | None = None,
) -> Exception | None:
    source_ex_str = str(source_ex)
    logic_error_data = parse_logic_error(source_ex_str)
    if logic_error_data:
        return LogicError(
            logic_error_str=source_ex_str,
            logic_error=source_ex if isinstance(source_ex, Exception) else None,
            program=approval_program,
            source_map=approval_source_map() if callable(approval_source_map) else approval_source_map,
            **logic_error_data,
            traces=simulate_traces,
        )

    return None


def execute_atc_with_logic_error(
    atc: AtomicTransactionComposer,
    algod_client: "AlgodClient",
    approval_program: str,
    wait_rounds: int = 4,
    approval_source_map: SourceMap | typing.Callable[[], SourceMap | None] | None = None,
) -> AtomicTransactionResponse:
    """Calls {py:meth}`AtomicTransactionComposer.execute` on provided `atc`, but will parse any errors
    and raise a {py:class}`LogicError` if possible

    ```{note}
    `approval_program` and `approval_source_map` are required to be able to parse any errors into a
    {py:class}`LogicError`
    ```
    """
    try:
        if config.debug and config.project_root and config.trace_all:
            simulate_and_persist_response(atc, config.project_root, algod_client, config.trace_buffer_size_mb)

        return atc.execute(algod_client, wait_rounds=wait_rounds)
    except Exception as ex:
        if config.debug:
            simulate = None
            if config.project_root and not config.trace_all:
                # if trace_all is enabled, we already have the traces executed above
                # hence we only need to simulate if trace_all is disabled and
                # project_root is set
                simulate = simulate_and_persist_response(
                    atc, config.project_root, algod_client, config.trace_buffer_size_mb
                )
            else:
                simulate = simulate_response(atc, algod_client)
            traces = _create_simulate_traces(simulate)
        else:
            traces = None
            logger.info("An error occurred while executing the transaction.")
            logger.info("To see more details, enable debug mode by setting config.debug = True ")

        logic_error = _try_convert_to_logic_error(ex, approval_program, approval_source_map, traces)
        if logic_error:
            raise logic_error from ex
        raise ex


def _create_simulate_traces(simulate: SimulateAtomicTransactionResponse) -> list[SimulationTrace]:
    traces = []
    if hasattr(simulate, "simulate_response") and hasattr(simulate, "failed_at") and simulate.failed_at:
        for txn_group in simulate.simulate_response["txn-groups"]:
            app_budget_added = txn_group.get("app-budget-added", None)
            app_budget_consumed = txn_group.get("app-budget-consumed", None)
            failure_message = txn_group.get("failure-message", None)
            txn_result = txn_group.get("txn-results", [{}])[0]
            exec_trace = txn_result.get("exec-trace", {})
            traces.append(
                SimulationTrace(
                    app_budget_added=app_budget_added,
                    app_budget_consumed=app_budget_consumed,
                    failure_message=failure_message,
                    exec_trace=exec_trace,
                )
            )
    return traces


def _convert_transaction_parameters(
    args: TransactionParameters | TransactionParametersDict | None,
) -> CreateCallParameters:
    _args = args.__dict__ if isinstance(args, TransactionParameters) else (args or {})
    return CreateCallParameters(**_args)


def get_sender_from_signer(signer: TransactionSigner | None) -> str | None:
    """Returns the associated address of a signer, return None if no address found"""

    if isinstance(signer, AccountTransactionSigner):
        sender = address_from_private_key(signer.private_key)  # type: ignore[no-untyped-call]
        assert isinstance(sender, str)
        return sender
    elif isinstance(signer, MultisigTransactionSigner):
        sender = signer.msig.address()  # type: ignore[no-untyped-call]
        assert isinstance(sender, str)
        return sender
    elif isinstance(signer, LogicSigTransactionSigner):
        return signer.lsig.address()
    return None


# TEMPORARY, use SDK one when available
def _parse_result(
    methods: dict[int, Method],
    txns: list[dict[str, Any]],
    txids: list[str],
) -> list[ABIResult]:
    method_results = []
    for i, tx_info in enumerate(txns):
        raw_value = b""
        return_value = None
        decode_error = None

        if i not in methods:
            continue

        # Parse log for ABI method return value
        try:
            if methods[i].returns.type == Returns.VOID:
                method_results.append(
                    ABIResult(
                        tx_id=txids[i],
                        raw_value=raw_value,
                        return_value=return_value,
                        decode_error=decode_error,
                        tx_info=tx_info,
                        method=methods[i],
                    )
                )
                continue

            logs = tx_info.get("logs", [])

            # Look for the last returned value in the log
            if not logs:
                raise Exception("No logs")

            result = logs[-1]
            # Check that the first four bytes is the hash of "return"
            result_bytes = base64.b64decode(result)
            if len(result_bytes) < len(ABI_RETURN_HASH) or result_bytes[: len(ABI_RETURN_HASH)] != ABI_RETURN_HASH:
                raise Exception("no logs")

            raw_value = result_bytes[4:]
            abi_return_type = methods[i].returns.type
            if isinstance(abi_return_type, ABIType):
                return_value = abi_return_type.decode(raw_value)
            else:
                return_value = raw_value

        except Exception as e:
            decode_error = e

        method_results.append(
            ABIResult(
                tx_id=txids[i],
                raw_value=raw_value,
                return_value=return_value,
                decode_error=decode_error,
                tx_info=tx_info,
                method=methods[i],
            )
        )

    return method_results


def _increment_version(version: str) -> str:
    split = list(map(int, version.split(".")))
    split[-1] = split[-1] + 1
    return ".".join(str(x) for x in split)


def _str_or_hex(v: bytes) -> str:
    decoded: str
    try:
        decoded = v.decode("utf-8")
    except UnicodeDecodeError:
        decoded = v.hex()

    return decoded


def _decode_state(state: list[dict[str, Any]], *, raw: bool = False) -> dict[str | bytes, bytes | str | int | None]:
    decoded_state: dict[str | bytes, bytes | str | int | None] = {}

    for state_value in state:
        raw_key = base64.b64decode(state_value["key"])

        key: str | bytes = raw_key if raw else _str_or_hex(raw_key)
        val: str | bytes | int | None

        action = state_value["value"]["action"] if "action" in state_value["value"] else state_value["value"]["type"]

        match action:
            case 1:
                raw_val = base64.b64decode(state_value["value"]["bytes"])
                val = raw_val if raw else _str_or_hex(raw_val)
            case 2:
                val = state_value["value"]["uint"]
            case 3:
                val = None
            case _:
                raise NotImplementedError

        decoded_state[key] = val
    return decoded_state

# === File: algokit_utils/_ensure_funded.py ===
from dataclasses import dataclass

from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.transaction import SuggestedParams
from algosdk.v2client.algod import AlgodClient

from algokit_utils._transfer import TransferParameters, transfer
from algokit_utils.account import get_dispenser_account
from algokit_utils.dispenser_api import (
    DispenserAssetName,
    TestNetDispenserApiClient,
)
from algokit_utils.models import Account
from algokit_utils.network_clients import is_testnet


@dataclass(kw_only=True)
class EnsureBalanceParameters:
    """Parameters for ensuring an account has a minimum number of µALGOs"""

    account_to_fund: Account | AccountTransactionSigner | str
    """The account address that will receive the µALGOs"""

    min_spending_balance_micro_algos: int
    """The minimum balance of ALGOs that the account should have available to spend (i.e. on top of
    minimum balance requirement)"""

    min_funding_increment_micro_algos: int = 0
    """When issuing a funding amount, the minimum amount to transfer (avoids many small transfers if this gets
    called often on an active account)"""

    funding_source: Account | AccountTransactionSigner | TestNetDispenserApiClient | None = None
    """The account (with private key) or signer that will send the µALGOs,
    will use `get_dispenser_account` by default. Alternatively you can pass an instance of [`TestNetDispenserApiClient`](https://github.com/algorandfoundation/algokit-utils-py/blob/main/docs/source/capabilities/dispenser-client.md)
    which will allow you to interact with [AlgoKit TestNet Dispenser API](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/features/dispenser.md)."""

    suggested_params: SuggestedParams | None = None
    """(optional) transaction parameters"""

    note: str | bytes | None = None
    """The (optional) transaction note, default: "Funding account to meet minimum requirement"""

    fee_micro_algos: int | None = None
    """(optional) The flat fee you want to pay, useful for covering extra fees in a transaction group or app call"""

    max_fee_micro_algos: int | None = None
    """(optional)The maximum fee that you are happy to pay (default: unbounded) -
    if this is set it's possible the transaction could get rejected during network congestion"""


@dataclass(kw_only=True)
class EnsureFundedResponse:
    """Response for ensuring an account has a minimum number of µALGOs"""

    """The transaction ID of the funding transaction"""
    transaction_id: str
    """The amount of µALGOs that were funded"""
    amount: int


def _get_address_to_fund(parameters: EnsureBalanceParameters) -> str:
    if isinstance(parameters.account_to_fund, str):
        return parameters.account_to_fund
    else:
        return str(address_from_private_key(parameters.account_to_fund.private_key))  # type: ignore[no-untyped-call]


def _get_account_info(client: AlgodClient, address_to_fund: str) -> dict:
    account_info = client.account_info(address_to_fund)
    assert isinstance(account_info, dict)
    return account_info


def _calculate_fund_amount(
    parameters: EnsureBalanceParameters, current_spending_balance_micro_algos: int
) -> int | None:
    if parameters.min_spending_balance_micro_algos > current_spending_balance_micro_algos:
        min_fund_amount_micro_algos = parameters.min_spending_balance_micro_algos - current_spending_balance_micro_algos
        return max(min_fund_amount_micro_algos, parameters.min_funding_increment_micro_algos)
    else:
        return None


def _fund_using_dispenser_api(
    dispenser_client: TestNetDispenserApiClient, address_to_fund: str, fund_amount_micro_algos: int
) -> EnsureFundedResponse | None:
    response = dispenser_client.fund(
        address=address_to_fund, amount=fund_amount_micro_algos, asset_id=DispenserAssetName.ALGO
    )

    return EnsureFundedResponse(transaction_id=response.tx_id, amount=response.amount)


def _fund_using_transfer(
    client: AlgodClient, parameters: EnsureBalanceParameters, address_to_fund: str, fund_amount_micro_algos: int
) -> EnsureFundedResponse:
    if isinstance(parameters.funding_source, TestNetDispenserApiClient):
        raise Exception(f"Invalid funding source: {parameters.funding_source}")

    funding_source = parameters.funding_source or get_dispenser_account(client)
    response = transfer(
        client,
        TransferParameters(
            from_account=funding_source,
            to_address=address_to_fund,
            micro_algos=fund_amount_micro_algos,
            note=parameters.note or "Funding account to meet minimum requirement",
            suggested_params=parameters.suggested_params,
            max_fee_micro_algos=parameters.max_fee_micro_algos,
            fee_micro_algos=parameters.fee_micro_algos,
        ),
    )
    transaction_id = response.get_txid()  # type: ignore[no-untyped-call]
    return EnsureFundedResponse(transaction_id=transaction_id, amount=response.amt)


def ensure_funded(
    client: AlgodClient,
    parameters: EnsureBalanceParameters,
) -> EnsureFundedResponse | None:
    """
    Funds a given account using a funding source such that it has a certain amount of algos free to spend
    (accounting for ALGOs locked in minimum balance requirement)
    see <https://developer.algorand.org/docs/get-details/accounts/#minimum-balance>


    Args:
        client (AlgodClient): An instance of the AlgodClient class from the AlgoSDK library.
        parameters (EnsureBalanceParameters): An instance of the EnsureBalanceParameters class that
        specifies the account to fund and the minimum spending balance.

    Returns:
        PaymentTxn | str | None: If funds are needed, the function returns a payment transaction or a
        string indicating that the dispenser API was used. If no funds are needed, the function returns None.
    """

    address_to_fund = _get_address_to_fund(parameters)
    account_info = _get_account_info(client, address_to_fund)
    balance_micro_algos = account_info.get("amount", 0)
    minimum_balance_micro_algos = account_info.get("min-balance", 0)
    current_spending_balance_micro_algos = balance_micro_algos - minimum_balance_micro_algos
    fund_amount_micro_algos = _calculate_fund_amount(parameters, current_spending_balance_micro_algos)

    if fund_amount_micro_algos is not None:
        if is_testnet(client) and isinstance(parameters.funding_source, TestNetDispenserApiClient):
            return _fund_using_dispenser_api(parameters.funding_source, address_to_fund, fund_amount_micro_algos)
        else:
            return _fund_using_transfer(client, parameters, address_to_fund, fund_amount_micro_algos)

    return None

# === File: algokit_utils/account.py ===
import logging
import os
from typing import TYPE_CHECKING, Any

from algosdk.account import address_from_private_key
from algosdk.mnemonic import from_private_key, to_private_key
from algosdk.util import algos_to_microalgos

from algokit_utils._transfer import TransferParameters, transfer
from algokit_utils.models import Account
from algokit_utils.network_clients import get_kmd_client_from_algod_client, is_localnet

if TYPE_CHECKING:
    from collections.abc import Callable

    from algosdk.kmd import KMDClient
    from algosdk.v2client.algod import AlgodClient

__all__ = [
    "create_kmd_wallet_account",
    "get_account",
    "get_account_from_mnemonic",
    "get_dispenser_account",
    "get_kmd_wallet_account",
    "get_localnet_default_account",
    "get_or_create_kmd_wallet_account",
]

logger = logging.getLogger(__name__)
_DEFAULT_ACCOUNT_MINIMUM_BALANCE = 1_000_000_000


def get_account_from_mnemonic(mnemonic: str) -> Account:
    """Convert a mnemonic (25 word passphrase) into an Account"""
    private_key = to_private_key(mnemonic)  # type: ignore[no-untyped-call]
    address = address_from_private_key(private_key)  # type: ignore[no-untyped-call]
    return Account(private_key=private_key, address=address)


def create_kmd_wallet_account(kmd_client: "KMDClient", name: str) -> Account:
    """Creates a wallet with specified name"""
    wallet_id = kmd_client.create_wallet(name, "")["id"]
    wallet_handle = kmd_client.init_wallet_handle(wallet_id, "")
    kmd_client.generate_key(wallet_handle)

    key_ids: list[str] = kmd_client.list_keys(wallet_handle)
    account_key = key_ids[0]

    private_account_key = kmd_client.export_key(wallet_handle, "", account_key)
    return get_account_from_mnemonic(from_private_key(private_account_key))  # type: ignore[no-untyped-call]


def get_or_create_kmd_wallet_account(
    client: "AlgodClient", name: str, fund_with_algos: float = 1000, kmd_client: "KMDClient | None" = None
) -> Account:
    """Returns a wallet with specified name, or creates one if not found"""
    kmd_client = kmd_client or get_kmd_client_from_algod_client(client)
    account = get_kmd_wallet_account(client, kmd_client, name)

    if account:
        account_info = client.account_info(account.address)
        assert isinstance(account_info, dict)
        if account_info["amount"] > 0:
            return account
        logger.debug(f"Found existing account in LocalNet with name '{name}', but no funds in the account.")
    else:
        account = create_kmd_wallet_account(kmd_client, name)

        logger.debug(
            f"Couldn't find existing account in LocalNet with name '{name}'. "
            f"So created account {account.address} with keys stored in KMD."
        )

    logger.debug(f"Funding account {account.address} with {fund_with_algos} ALGOs")

    if fund_with_algos:
        transfer(
            client,
            TransferParameters(
                from_account=get_dispenser_account(client),
                to_address=account.address,
                micro_algos=algos_to_microalgos(fund_with_algos),  # type: ignore[no-untyped-call]
            ),
        )

    return account


def _is_default_account(account: dict[str, Any]) -> bool:
    return bool(account["status"] != "Offline" and account["amount"] > _DEFAULT_ACCOUNT_MINIMUM_BALANCE)


def get_localnet_default_account(client: "AlgodClient") -> Account:
    """Returns the default Account in a LocalNet instance"""
    if not is_localnet(client):
        raise Exception("Can't get a default account from non LocalNet network")

    account = get_kmd_wallet_account(
        client, get_kmd_client_from_algod_client(client), "unencrypted-default-wallet", _is_default_account
    )
    assert account
    return account


def get_dispenser_account(client: "AlgodClient") -> Account:
    """Returns an Account based on DISPENSER_MNENOMIC environment variable or the default account on LocalNet"""
    if is_localnet(client):
        return get_localnet_default_account(client)
    return get_account(client, "DISPENSER")


def get_kmd_wallet_account(
    client: "AlgodClient",
    kmd_client: "KMDClient",
    name: str,
    predicate: "Callable[[dict[str, Any]], bool] | None" = None,
) -> Account | None:
    """Returns wallet matching specified name and predicate or None if not found"""
    wallets: list[dict] = kmd_client.list_wallets()

    wallet = next((w for w in wallets if w["name"] == name), None)
    if wallet is None:
        return None

    wallet_id = wallet["id"]
    wallet_handle = kmd_client.init_wallet_handle(wallet_id, "")
    key_ids: list[str] = kmd_client.list_keys(wallet_handle)
    matched_account_key = None
    if predicate:
        for key in key_ids:
            account = client.account_info(key)
            assert isinstance(account, dict)
            if predicate(account):
                matched_account_key = key
    else:
        matched_account_key = next(key_ids.__iter__(), None)

    if not matched_account_key:
        return None

    private_account_key = kmd_client.export_key(wallet_handle, "", matched_account_key)
    return get_account_from_mnemonic(from_private_key(private_account_key))  # type: ignore[no-untyped-call]


def get_account(
    client: "AlgodClient", name: str, fund_with_algos: float = 1000, kmd_client: "KMDClient | None" = None
) -> Account:
    """Returns an Algorand account with private key loaded by convention based on the given name identifier.

    # Convention

    **Non-LocalNet:** will load `os.environ[f"{name}_MNEMONIC"]` as a mnemonic secret
    Be careful how the mnemonic is handled, never commit it into source control and ideally load it via a
    secret storage service rather than the file system.

    **LocalNet:** will load the account from a KMD wallet called {name} and if that wallet doesn't exist it will
    create it and fund the account for you

    This allows you to write code that will work seamlessly in production and local development (LocalNet) without
    manual config locally (including when you reset the LocalNet).

    # Example
    If you have a mnemonic secret loaded into `os.environ["ACCOUNT_MNEMONIC"]` then you can call the following to get
    that private key loaded into an account object:
    ```python
    account = get_account('ACCOUNT', algod)
    ```

    If that code runs against LocalNet then a wallet called 'ACCOUNT' will automatically be created with an account
    that is automatically funded with 1000 (default) ALGOs from the default LocalNet dispenser.
    """

    mnemonic_key = f"{name.upper()}_MNEMONIC"
    mnemonic = os.getenv(mnemonic_key)
    if mnemonic:
        return get_account_from_mnemonic(mnemonic)

    if is_localnet(client):
        account = get_or_create_kmd_wallet_account(client, name, fund_with_algos, kmd_client)
        os.environ[mnemonic_key] = from_private_key(account.private_key)  # type: ignore[no-untyped-call]
        return account

    raise Exception(f"Missing environment variable '{mnemonic_key}' when looking for account '{name}'")

# === File: algokit_utils/beta/composer.py ===
import base64
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import algosdk
from algokit_utils import (
    AppManager,
    Config,
    EventType,
    encode_lease,
    get_abi_return_value,
    send_atomic_transaction_composer,
)
from algokit_utils.client_manager import ClientManager
from algosdk.abi import Method
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.transaction import (
    ApplicationCallTxn,
    ApplicationCreateTxn,
    AssetConfigTxn,
    AssetFreezeTxn,
    AssetTransferTxn,
    OnComplete,
    PaymentTxn,
    StateSchema,
    SuggestedParams,
    Transaction,
)
from algosdk.v2client.algod import AlgodClient


@dataclass
class CommonTransactionParams:
    sender: str
    signer: algosdk.transaction.TransactionSigner | None = None
    rekey_to: str | None = None
    note: bytes | str | None = None
    lease: bytes | str | None = None
    static_fee: int | None = None
    extra_fee: int | None = None
    max_fee: int | None = None
    validity_window: int | None = None
    first_valid_round: int | None = None
    last_valid_round: int | None = None


@dataclass
class PaymentParams(CommonTransactionParams):
    receiver: str
    amount: int
    close_remainder_to: str | None = None


@dataclass
class AssetCreateParams(CommonTransactionParams):
    total: int
    decimals: int = 0
    asset_name: str | None = None
    unit_name: str | None = None
    url: str | None = None
    metadata_hash: str | bytes | None = None
    default_frozen: bool = False
    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None


@dataclass
class AssetConfigParams(CommonTransactionParams):
    asset_id: int
    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None


@dataclass
class AssetFreezeParams(CommonTransactionParams):
    asset_id: int
    account: str
    frozen: bool


@dataclass
class AssetDestroyParams(CommonTransactionParams):
    asset_id: int


@dataclass
class AssetTransferParams(CommonTransactionParams):
    asset_id: int
    amount: int
    receiver: str
    clawback_target: str | None = None
    close_asset_to: str | None = None


@dataclass
class AppCallParams(CommonTransactionParams):
    app_id: int
    on_complete: OnComplete | None = None
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[str | dict[str, int | bytes]] | None = None


@dataclass
class AppCreateParams(AppCallParams):
    approval_program: str | bytes
    clear_state_program: str | bytes
    schema: dict[str, int] | None = None
    extra_program_pages: int | None = None


@dataclass
class AppMethodCallParams(AppCallParams):
    method: Method
    method_args: list[Any]


class BuiltTransactions:
    def __init__(
        self,
        transactions: list[Transaction],
        method_calls: dict[int, Method],
        signers: dict[int, algosdk.transaction.TransactionSigner],
    ):
        self.transactions = transactions
        self.method_calls = method_calls
        self.signers = signers


class AlgoKitComposer:
    NULL_SIGNER = AccountTransactionSigner(algosdk.account.generate_account()[0])

    def __init__(  # noqa: PLR0913
        self,
        algod: AlgodClient,
        get_signer: Callable[[str], algosdk.transaction.TransactionSigner],
        get_suggested_params: Callable[[], SuggestedParams] | None = None,
        default_validity_window: int | None = None,
        app_manager: AppManager | None = None,
    ) -> None:
        self.txn_method_map: dict[str, Method] = {}
        self.txns: list[dict[str, Any]] = []
        self.atc = AtomicTransactionComposer()
        self.algod = algod
        self.get_suggested_params = get_suggested_params or self.algod.suggested_params
        self.get_signer = get_signer
        self.default_validity_window = default_validity_window or 10
        self.default_validity_window_is_explicit = default_validity_window is not None
        self.app_manager = app_manager or AppManager(algod)

    def add_transaction(
        self, transaction: Transaction, signer: algosdk.transaction.TransactionSigner | None = None
    ) -> "AlgoKitComposer":
        self.txns.append(
            {
                "txn": transaction,
                "signer": signer or self.get_signer(algosdk.encoding.encode_address(transaction.sender)),
                "type": "txn_with_signer",
            }
        )
        return self

    def add_payment(self, params: PaymentParams) -> "AlgoKitComposer":
        self.txns.append({**params.__dict__, "type": "pay"})
        return self

    def add_asset_create(self, params: AssetCreateParams) -> "AlgoKitComposer":
        self.txns.append({**params.__dict__, "type": "asset_create"})
        return self

    def add_asset_config(self, params: AssetConfigParams) -> "AlgoKitComposer":
        self.txns.append({**params.__dict__, "type": "asset_config"})
        return self

    def add_asset_freeze(self, params: AssetFreezeParams) -> "AlgoKitComposer":
        self.txns.append({**params.__dict__, "type": "asset_freeze"})
        return self

    def add_asset_destroy(self, params: AssetDestroyParams) -> "AlgoKitComposer":
        self.txns.append({**params.__dict__, "type": "asset_destroy"})
        return self

    def add_asset_transfer(self, params: AssetTransferParams) -> "AlgoKitComposer":
        self.txns.append({**params.__dict__, "type": "asset_transfer"})
        return self

    def add_app_call(self, params: AppCallParams) -> "AlgoKitComposer":
        self.txns.append({**params.__dict__, "type": "app_call"})
        return self

    def add_app_create(self, params: AppCreateParams) -> "AlgoKitComposer":
        self.txns.append({**params.__dict__, "type": "app_create"})
        return self

    def add_method_call(self, params: AppMethodCallParams) -> "AlgoKitComposer":
        self.txns.append({**params.__dict__, "type": "method_call"})
        return self

    def _build_atc(self, atc: AtomicTransactionComposer) -> list[TransactionWithSigner]:
        group = atc.build_group()
        for tws in group:
            tws.txn.group = None
        method = atc._method_dict.get(len(group) - 1)
        if method:
            self.txn_method_map[group[-1].txn.get_txid()] = method
        return group

    def _common_txn_build_step(
        self, params: CommonTransactionParams, txn: Transaction, suggested_params: SuggestedParams
    ) -> Transaction:
        if params.lease:
            txn.lease = encode_lease(params.lease)
        if params.rekey_to:
            txn.rekey_to = algosdk.encoding.decode_address(params.rekey_to)
        if params.note:
            txn.note = params.note.encode() if isinstance(params.note, str) else params.note

        if params.first_valid_round:
            txn.first_valid_round = params.first_valid_round

        if params.last_valid_round:
            txn.last_valid_round = params.last_valid_round
        else:
            window = params.validity_window
            if window is None:
                if not self.default_validity_window_is_explicit and ClientManager.genesis_id_is_localnet(
                    str(suggested_params.gen)
                ):
                    window = 1000
                else:
                    window = self.default_validity_window
            txn.last_valid_round = txn.first_valid_round + window

        if params.static_fee is not None and params.extra_fee is not None:
            raise ValueError("Cannot set both static_fee and extra_fee")

        if params.static_fee is not None:
            txn.fee = params.static_fee
        else:
            txn.fee = txn.estimate_size() * suggested_params.min_fee or algosdk.constants.MIN_TXN_FEE  # type: ignore[no-untyped-call]
            if params.extra_fee:
                txn.fee += params.extra_fee

        if params.max_fee is not None and txn.fee > params.max_fee:
            raise ValueError(f"Transaction fee {txn.fee} µALGO is greater than max_fee {params.max_fee}")

        return txn

    def _build_payment(self, params: PaymentParams, suggested_params: SuggestedParams) -> Transaction:
        txn = PaymentTxn(
            sender=params.sender,
            sp=suggested_params,
            receiver=params.receiver,
            amt=params.amount,
            close_remainder_to=params.close_remainder_to,
        )
        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_create(self, params: AssetCreateParams, suggested_params: SuggestedParams) -> Transaction:
        txn = AssetConfigTxn(
            sender=params.sender,
            sp=suggested_params,
            total=params.total,
            default_frozen=params.default_frozen,
            unit_name=params.unit_name,
            asset_name=params.asset_name,
            manager=params.manager,
            reserve=params.reserve,
            freeze=params.freeze,
            clawback=params.clawback,
            url=params.url,
            metadata_hash=params.metadata_hash,
            decimals=params.decimals,
        )
        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_config(self, params: AssetConfigParams, suggested_params: SuggestedParams) -> Transaction:
        txn = AssetConfigTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
            manager=params.manager,
            reserve=params.reserve,
            freeze=params.freeze,
            clawback=params.clawback,
            strict_empty_address_check=False,
        )
        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_freeze(self, params: AssetFreezeParams, suggested_params: SuggestedParams) -> Transaction:
        txn = AssetFreezeTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
            target=params.account,
            new_freeze_state=params.frozen,
        )
        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_destroy(self, params: AssetDestroyParams, suggested_params: SuggestedParams) -> Transaction:
        txn = AssetConfigTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
            strict_empty_address_check=False,
        )
        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_transfer(self, params: AssetTransferParams, suggested_params: SuggestedParams) -> Transaction:
        txn = AssetTransferTxn(
            sender=params.sender,
            sp=suggested_params,
            receiver=params.receiver,
            amt=params.amount,
            index=params.asset_id,
            revocation_target=params.clawback_target,
            close_assets_to=params.close_asset_to,
        )
        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_app_call(self, params: AppCallParams, suggested_params: SuggestedParams) -> Transaction:
        txn = ApplicationCallTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.app_id,
            on_complete=params.on_complete or OnComplete.NoOpOC,
            app_args=params.args,
            accounts=params.account_references,
            foreign_apps=params.app_references,
            foreign_assets=params.asset_references,
            boxes=[(b["app_id"], b["name"]) if isinstance(b, dict) else (0, b) for b in (params.box_references or [])],
        )
        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_app_create(self, params: AppCreateParams, suggested_params: SuggestedParams) -> Transaction:
        approval_program = (
            self.app_manager.compile_program(params.approval_program)
            if isinstance(params.approval_program, str)
            else params.approval_program
        )
        clear_program = (
            self.app_manager.compile_program(params.clear_state_program)
            if isinstance(params.clear_state_program, str)
            else params.clear_state_program
        )

        schema = params.schema or {}
        global_schema = StateSchema(schema.get("global_ints", 0), schema.get("global_bytes", 0))
        local_schema = StateSchema(schema.get("local_ints", 0), schema.get("local_bytes", 0))

        txn = ApplicationCreateTxn(
            sender=params.sender,
            sp=suggested_params,
            on_complete=params.on_complete or OnComplete.NoOpOC,
            approval_program=approval_program,
            clear_program=clear_program,
            global_schema=global_schema,
            local_schema=local_schema,
            app_args=params.args,
            accounts=params.account_references,
            foreign_apps=params.app_references,
            foreign_assets=params.asset_references,
            boxes=[(b["app_id"], b["name"]) if isinstance(b, dict) else (0, b) for b in (params.box_references or [])],
            extra_pages=params.extra_program_pages,
        )
        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_method_call(
        self, params: AppMethodCallParams, suggested_params: SuggestedParams, include_signer: bool
    ) -> list[TransactionWithSigner]:
        atc = AtomicTransactionComposer()

        signer = params.signer if include_signer else self.NULL_SIGNER
        if not signer:
            signer = self.get_signer(params.sender)

        atc.add_method_call(
            app_id=params.app_id,
            method=params.method,
            sender=params.sender,
            sp=suggested_params,
            signer=signer,
            method_args=params.method_args,
            on_complete=params.on_complete,
            accounts=params.account_references,
            foreign_apps=params.app_references,
            foreign_assets=params.asset_references,
            boxes=[(b["app_id"], b["name"]) if isinstance(b, dict) else (0, b) for b in (params.box_references or [])],
        )

        return self._build_atc(atc)

    def _build_txn(self, txn: dict[str, Any], suggested_params: SuggestedParams) -> list[Transaction]:
        txn_type = txn["type"]
        if txn_type == "pay":
            return [self._build_payment(PaymentParams(**txn), suggested_params)]
        elif txn_type == "asset_create":
            return [self._build_asset_create(AssetCreateParams(**txn), suggested_params)]
        elif txn_type == "asset_config":
            return [self._build_asset_config(AssetConfigParams(**txn), suggested_params)]
        elif txn_type == "asset_freeze":
            return [self._build_asset_freeze(AssetFreezeParams(**txn), suggested_params)]
        elif txn_type == "asset_destroy":
            return [self._build_asset_destroy(AssetDestroyParams(**txn), suggested_params)]
        elif txn_type == "asset_transfer":
            return [self._build_asset_transfer(AssetTransferParams(**txn), suggested_params)]
        elif txn_type == "app_call":
            return [self._build_app_call(AppCallParams(**txn), suggested_params)]
        elif txn_type == "app_create":
            return [self._build_app_create(AppCreateParams(**txn), suggested_params)]
        else:
            raise ValueError(f"Unsupported transaction type: {txn_type}")

    def _build_txn_with_signer(
        self, txn: dict[str, Any], suggested_params: SuggestedParams
    ) -> list[TransactionWithSigner]:
        txn_type = txn["type"]
        if txn_type == "txn_with_signer":
            return [txn]
        elif txn_type == "atc":
            return self._build_atc(txn["atc"])
        elif txn_type == "method_call":
            return self._build_method_call(AppMethodCallParams(**txn), suggested_params, True)
        else:
            signer = txn.get("signer") or self.get_signer(txn["sender"])
            transactions = self._build_txn(txn, suggested_params)
            return [TransactionWithSigner(txn=t, signer=signer) for t in transactions]

    def build_transactions(self) -> BuiltTransactions:
        suggested_params = self.get_suggested_params()

        transactions: list[Transaction] = []
        method_calls: dict[int, Method] = {}
        signers: dict[int, algosdk.transaction.TransactionSigner] = {}

        index = 0
        for txn in self.txns:
            if txn["type"] not in ["txn_with_signer", "atc", "method_call"]:
                built_txns = self._build_txn(txn, suggested_params)
                transactions.extend(built_txns)
                index += len(built_txns)
            else:
                transactions_with_signer = (
                    [txn]
                    if txn["type"] == "txn_with_signer"
                    else self._build_atc(txn["atc"])
                    if txn["type"] == "atc"
                    else self._build_method_call(AppMethodCallParams(**txn), suggested_params, False)
                )
                for tws in transactions_with_signer:
                    transactions.append(tws.txn)
                    if tws.signer and tws.signer != self.NULL_SIGNER:
                        signers[index] = tws.signer
                    index += 1

        for idx, txn in enumerate(transactions):
            method = self.txn_method_map.get(txn.get_txid())
            if method:
                method_calls[idx] = method

        return BuiltTransactions(transactions, method_calls, signers)

    def count(self) -> int:
        return len(self.build_transactions().transactions)

    def build(self) -> dict[str, Any]:
        if self.atc.get_status() == AtomicTransactionComposer.Status.BUILDING:
            suggested_params = self.get_suggested_params()
            txn_with_signers = []
            for txn in self.txns:
                txn_with_signers.extend(self._build_txn_with_signer(txn, suggested_params))

            method_calls: dict[int, Method] = {}
            for idx, tws in enumerate(txn_with_signers):
                self.atc.add_transaction(tws)
                method = self.txn_method_map.get(tws.txn.get_txid())
                if method:
                    method_calls[idx] = method
            self.atc._method_dict = method_calls

        return {"atc": self.atc, "transactions": self.atc.build_group(), "method_calls": self.atc._method_dict}

    def rebuild(self) -> dict[str, Any]:
        self.atc = AtomicTransactionComposer()
        return self.build()

    def send(self, params: SendParams | None = None) -> dict[str, Any]:
        group = self.build()["transactions"]

        if params and params.max_rounds_to_wait_for_confirmation is not None:
            wait_rounds = params.max_rounds_to_wait_for_confirmation
        else:
            last_round = max(txn.last_valid_round for txn in group)
            first_round = self.get_suggested_params().first
            wait_rounds = last_round - first_round + 1

        return send_atomic_transaction_composer(
            atc=self.atc,
            algod_client=self.algod,
            max_rounds_to_wait_for_confirmation=wait_rounds,
            suppress_logging=params.suppress_log if params else False,
            populate_app_call_resources=params.populate_app_call_resources if params else False,
        )

    def execute(self, params: SendParams | None = None) -> dict[str, Any]:
        return self.send(params)

    def simulate(self, options: dict[str, Any] | None = None) -> dict[str, Any]:
        if options and options.get("skip_signatures"):
            atc = AtomicTransactionComposer()
            options["allow_empty_signatures"] = True
            transactions = self.build_transactions()
            for txn in transactions.transactions:
                atc.add_transaction(TransactionWithSigner(txn=txn, signer=self.NULL_SIGNER))
            atc._method_dict = transactions.method_calls
        else:
            self.build()
            atc = self.atc

        simulate_request = algosdk.v2client.models.SimulateRequest(
            txn_groups=[],
            **(options or {}),
        )

        method_results, simulate_response = atc.simulate(self.algod, simulate_request)

        failed_group = simulate_response.txn_groups[0] if simulate_response.txn_groups else None
        if failed_group and failed_group.failure_message:
            error_message = (
                f"Transaction failed at transaction(s) "
                f"{', '.join(map(str, failed_group.failed_at or ['unknown']))} in the group. "
                f"{failed_group.failure_message}"
            )
            error = ValueError(error_message)
            if Config.debug:
                Config.events.emit(EventType.TXN_GROUP_SIMULATED, {"simulate_response": simulate_response})
            error.simulate_response = simulate_response
            raise error

        if Config.debug and Config.trace_all:
            Config.events.emit(EventType.TXN_GROUP_SIMULATED, {"simulate_response": simulate_response})

        transactions = atc.build_group()
        return {
            "confirmations": [t.txn_result for t in simulate_response.txn_groups[0].txn_results],
            "transactions": [t.txn for t in transactions],
            "tx_ids": [t.txn.get_txid() for t in transactions],
            "group_id": base64.b64encode(transactions[0].txn.group or b"").decode(),
            "simulate_response": simulate_response,
            "returns": [get_abi_return_value(result) for result in method_results],
        }

    @staticmethod
    def arc2_note(note: Arc2TransactionNote) -> bytes:
        data = note.data if isinstance(note.data, str) else json.dumps(note.data)
        arc2_payload = f"{note.dAppName}:{note.format}{data}"
        return arc2_payload.encode()

# === File: algokit_utils/beta/algorand_client.py ===
import copy
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from algokit_utils.beta.account_manager import AccountManager
from algokit_utils.beta.composer import (
    AlgokitComposer,
    AppCallParams,
    AssetConfigParams,
    AssetCreateParams,
    AssetDestroyParams,
    AssetFreezeParams,
    AssetOptInParams,
    AssetTransferParams,
    MethodCallParams,
    OnlineKeyRegParams,
    PaymentParams,
)
from algokit_utils.client_manager import AlgoSdkClients, ClientManager
from algokit_utils.network_clients import (
    AlgoConfig,
    get_algod_client,
    get_algonode_config,
    get_default_localnet_config,
    get_indexer_client,
    get_kmd_client,
)
from algosdk.atomic_transaction_composer import AtomicTransactionResponse, TransactionSigner
from algosdk.transaction import SuggestedParams, Transaction, wait_for_confirmation
from typing_extensions import Self

__all__ = [
    "AlgorandClient",
    "AssetCreateParams",
    "AssetOptInParams",
    "MethodCallParams",
    "PaymentParams",
    "AssetFreezeParams",
    "AssetConfigParams",
    "AssetDestroyParams",
    "AppCallParams",
    "OnlineKeyRegParams",
    "AssetTransferParams",
]


@dataclass
class AlgorandClientSendMethods:
    """
    Methods used to send a transaction to the network and wait for confirmation
    """

    payment: Callable[[PaymentParams], dict[str, Any]]
    asset_create: Callable[[AssetCreateParams], dict[str, Any]]
    asset_config: Callable[[AssetConfigParams], dict[str, Any]]
    asset_freeze: Callable[[AssetFreezeParams], dict[str, Any]]
    asset_destroy: Callable[[AssetDestroyParams], dict[str, Any]]
    asset_transfer: Callable[[AssetTransferParams], dict[str, Any]]
    app_call: Callable[[AppCallParams], dict[str, Any]]
    online_key_reg: Callable[[OnlineKeyRegParams], dict[str, Any]]
    method_call: Callable[[MethodCallParams], dict[str, Any]]
    asset_opt_in: Callable[[AssetOptInParams], dict[str, Any]]


@dataclass
class AlgorandClientTransactionMethods:
    """
    Methods used to form a transaction without signing or sending to the network
    """

    payment: Callable[[PaymentParams], Transaction]
    asset_create: Callable[[AssetCreateParams], Transaction]
    asset_config: Callable[[AssetConfigParams], Transaction]
    asset_freeze: Callable[[AssetFreezeParams], Transaction]
    asset_destroy: Callable[[AssetDestroyParams], Transaction]
    asset_transfer: Callable[[AssetTransferParams], Transaction]
    app_call: Callable[[AppCallParams], Transaction]
    online_key_reg: Callable[[OnlineKeyRegParams], Transaction]
    method_call: Callable[[MethodCallParams], list[Transaction]]
    asset_opt_in: Callable[[AssetOptInParams], Transaction]


class AlgorandClient:
    """A client that brokers easy access to Algorand functionality."""

    def __init__(self, config: AlgoConfig | AlgoSdkClients):
        self._client_manager: ClientManager = ClientManager(config)
        self._account_manager: AccountManager = AccountManager(self._client_manager)

        self._cached_suggested_params: SuggestedParams | None = None
        self._cached_suggested_params_expiry: float | None = None
        self._cached_suggested_params_timeout: int = 3_000  # three seconds

        self._default_validity_window: int = 10

    def _unwrap_single_send_result(self, results: AtomicTransactionResponse) -> dict[str, Any]:
        return {
            "confirmation": wait_for_confirmation(self._client_manager.algod, results.tx_ids[0]),
            "tx_id": results.tx_ids[0],
        }

    def set_default_validity_window(self, validity_window: int) -> Self:
        """
        Sets the default validity window for transactions.

        :param validity_window: The number of rounds between the first and last valid rounds
        :return: The `AlgorandClient` so method calls can be chained
        """
        self._default_validity_window = validity_window
        return self

    def set_default_signer(self, signer: TransactionSigner) -> Self:
        """
        Sets the default signer to use if no other signer is specified.

        :param signer: The signer to use, either a `TransactionSigner` or a `TransactionSignerAccount`
        :return: The `AlgorandClient` so method calls can be chained
        """
        self._account_manager.set_default_signer(signer)
        return self

    def set_signer(self, sender: str, signer: TransactionSigner) -> Self:
        """
        Tracks the given account for later signing.

        :param sender: The sender address to use this signer for
        :param signer: The signer to sign transactions with for the given sender
        :return: The `AlgorandClient` so method calls can be chained
        """
        self._account_manager.set_signer(sender, signer)
        return self

    def set_suggested_params(self, suggested_params: SuggestedParams, until: float | None = None) -> Self:
        """
        Sets a cache value to use for suggested params.

        :param suggested_params: The suggested params to use
        :param until: A timestamp until which to cache, or if not specified then the timeout is used
        :return: The `AlgorandClient` so method calls can be chained
        """
        self._cached_suggested_params = suggested_params
        self._cached_suggested_params_expiry = until or time.time() + self._cached_suggested_params_timeout
        return self

    def set_suggested_params_timeout(self, timeout: int) -> Self:
        """
        Sets the timeout for caching suggested params.

        :param timeout: The timeout in milliseconds
        :return: The `AlgorandClient` so method calls can be chained
        """
        self._cached_suggested_params_timeout = timeout
        return self

    def get_suggested_params(self) -> SuggestedParams:
        """Get suggested params for a transaction (either cached or from algod if the cache is stale or empty)"""
        if self._cached_suggested_params and (
            self._cached_suggested_params_expiry is None or self._cached_suggested_params_expiry > time.time()
        ):
            return copy.deepcopy(self._cached_suggested_params)

        self._cached_suggested_params = self._client_manager.algod.suggested_params()
        self._cached_suggested_params_expiry = time.time() + self._cached_suggested_params_timeout

        return copy.deepcopy(self._cached_suggested_params)

    @property
    def client(self) -> ClientManager:
        """Get clients, including algosdk clients and app clients."""
        return self._client_manager

    @property
    def account(self) -> AccountManager:
        """Get or create accounts that can sign transactions."""
        return self._account_manager

    def new_group(self) -> AlgokitComposer:
        """Start a new `AlgokitComposer` transaction group"""
        return AlgokitComposer(
            algod=self.client.algod,
            get_signer=lambda addr: self.account.get_signer(addr),
            get_suggested_params=self.get_suggested_params,
            default_validity_window=self._default_validity_window,
        )

    @property
    def send(self) -> AlgorandClientSendMethods:
        """Methods for sending a transaction and waiting for confirmation"""
        return AlgorandClientSendMethods(
            payment=lambda params: self._unwrap_single_send_result(self.new_group().add_payment(params).execute()),
            asset_create=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_create(params).execute()
            ),
            asset_config=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_config(params).execute()
            ),
            asset_freeze=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_freeze(params).execute()
            ),
            asset_destroy=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_destroy(params).execute()
            ),
            asset_transfer=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_transfer(params).execute()
            ),
            app_call=lambda params: self._unwrap_single_send_result(self.new_group().add_app_call(params).execute()),
            online_key_reg=lambda params: self._unwrap_single_send_result(
                self.new_group().add_online_key_reg(params).execute()
            ),
            method_call=lambda params: self._unwrap_single_send_result(
                self.new_group().add_method_call(params).execute()
            ),
            asset_opt_in=lambda params: self._unwrap_single_send_result(
                self.new_group().add_asset_opt_in(params).execute()
            ),
        )

    @property
    def transactions(self) -> AlgorandClientTransactionMethods:
        """Methods for building transactions"""

        return AlgorandClientTransactionMethods(
            payment=lambda params: self.new_group().add_payment(params).build_group()[0].txn,
            asset_create=lambda params: self.new_group().add_asset_create(params).build_group()[0].txn,
            asset_config=lambda params: self.new_group().add_asset_config(params).build_group()[0].txn,
            asset_freeze=lambda params: self.new_group().add_asset_freeze(params).build_group()[0].txn,
            asset_destroy=lambda params: self.new_group().add_asset_destroy(params).build_group()[0].txn,
            asset_transfer=lambda params: self.new_group().add_asset_transfer(params).build_group()[0].txn,
            app_call=lambda params: self.new_group().add_app_call(params).build_group()[0].txn,
            online_key_reg=lambda params: self.new_group().add_online_key_reg(params).build_group()[0].txn,
            method_call=lambda params: [txn.txn for txn in self.new_group().add_method_call(params).build_group()],
            asset_opt_in=lambda params: self.new_group().add_asset_opt_in(params).build_group()[0].txn,
        )

    @staticmethod
    def default_local_net() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing at default LocalNet ports and API token.

        :return: The `AlgorandClient`
        """
        return AlgorandClient(
            AlgoConfig(
                algod_config=get_default_localnet_config("algod"),
                indexer_config=get_default_localnet_config("indexer"),
                kmd_config=get_default_localnet_config("kmd"),
            )
        )

    @staticmethod
    def test_net() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing at TestNet using AlgoNode.

        :return: The `AlgorandClient`
        """
        return AlgorandClient(
            AlgoConfig(
                algod_config=get_algonode_config("testnet", "algod", ""),
                indexer_config=get_algonode_config("testnet", "indexer", ""),
                kmd_config=None,
            )
        )

    @staticmethod
    def main_net() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing at MainNet using AlgoNode.

        :return: The `AlgorandClient`
        """
        return AlgorandClient(
            AlgoConfig(
                algod_config=get_algonode_config("mainnet", "algod", ""),
                indexer_config=get_algonode_config("mainnet", "indexer", ""),
                kmd_config=None,
            )
        )

    @staticmethod
    def from_clients(clients: AlgoSdkClients) -> "AlgorandClient":
        """
        Returns an `AlgorandClient` pointing to the given client(s).

        :param clients: The clients to use
        :return: The `AlgorandClient`
        """
        return AlgorandClient(clients)

    @staticmethod
    def from_environment() -> "AlgorandClient":
        """
        Returns an `AlgorandClient` loading the configuration from environment variables.

        Retrieve configurations from environment variables when defined or get defaults.

        Expects to be called from a Python environment.

        :return: The `AlgorandClient`
        """
        return AlgorandClient(
            AlgoSdkClients(
                algod=get_algod_client(),
                kmd=get_kmd_client(),
                indexer=get_indexer_client(),
            )
        )

    @staticmethod
    def from_config(config: AlgoConfig) -> "AlgorandClient":
        """
        Returns an `AlgorandClient` from the given config.

        :param config: The config to use
        :return: The `AlgorandClient`
        """
        return AlgorandClient(config)

# === File: algokit_utils/beta/client_manager.py ===
# import algosdk
# from algokit_utils.dispenser_api import TestNetDispenserApiClient
# from algokit_utils.network_clients import AlgoClientConfigs, get_algod_client, get_indexer_client, get_kmd_client
# from algosdk.kmd import KMDClient
# from algosdk.v2client.algod import AlgodClient
# from algosdk.v2client.indexer import IndexerClient


# class AlgoSdkClients:
#     """
#     Clients from algosdk that interact with the official Algorand APIs.

#     Attributes:
#         algod (AlgodClient): Algod client, see https://developer.algorand.org/docs/rest-apis/algod/
#         indexer (Optional[IndexerClient]): Optional indexer client, see https://developer.algorand.org/docs/rest-apis/indexer/
#         kmd (Optional[KMDClient]): Optional KMD client, see https://developer.algorand.org/docs/rest-apis/kmd/
#     """

#     def __init__(
#         self,
#         algod: algosdk.v2client.algod.AlgodClient,
#         indexer: IndexerClient | None = None,
#         kmd: KMDClient | None = None,
#     ):
#         self.algod = algod
#         self.indexer = indexer
#         self.kmd = kmd


# class ClientManager:
#     """
#     Exposes access to various API clients.

#     Args:
#         clients_or_config (Union[AlgoConfig, AlgoSdkClients]): algosdk clients or config for interacting with the official Algorand APIs.
#     """

#     def __init__(self, clients_or_configs: AlgoClientConfigs | AlgoSdkClients):
#         if isinstance(clients_or_configs, AlgoSdkClients):
#             _clients = clients_or_configs
#         elif isinstance(clients_or_configs, AlgoClientConfigs):
#             _clients = AlgoSdkClients(
#                 algod=get_algod_client(clients_or_configs.algod_config),
#                 indexer=get_indexer_client(clients_or_configs.indexer_config)
#                 if clients_or_configs.indexer_config
#                 else None,
#                 kmd=get_kmd_client(clients_or_configs.kmd_config) if clients_or_configs.kmd_config else None,
#             )
#         self._algod = _clients.algod
#         self._indexer = _clients.indexer
#         self._kmd = _clients.kmd

#     @property
#     def algod(self) -> AlgodClient:
#         """Returns an algosdk Algod API client."""
#         return self._algod

#     @property
#     def indexer(self) -> IndexerClient:
#         """Returns an algosdk Indexer API client or raises an error if it's not been provided."""
#         if not self._indexer:
#             raise ValueError("Attempt to use Indexer client in AlgoKit instance with no Indexer configured")
#         return self._indexer

#     @property
#     def kmd(self) -> KMDClient:
#         """Returns an algosdk KMD API client or raises an error if it's not been provided."""
#         if not self._kmd:
#             raise ValueError("Attempt to use Kmd client in AlgoKit instance with no Kmd configured")
#         return self._kmd

#     def get_testnet_dispenser(
#         self, auth_token: str | None = None, request_timeout: int | None = None
#     ) -> TestNetDispenserApiClient:
#         if request_timeout:
#             return TestNetDispenserApiClient(auth_token=auth_token, request_timeout=request_timeout)

#         return TestNetDispenserApiClient(auth_token=auth_token)

# === File: algokit_utils/beta/account_manager.py ===
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from algokit_utils.account import get_dispenser_account, get_kmd_wallet_account, get_localnet_default_account
from algokit_utils.client_manager import ClientManager
from algosdk.account import generate_account
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner
from typing_extensions import Self


@dataclass
class AddressAndSigner:
    address: str
    signer: TransactionSigner


class AccountManager:
    """Creates and keeps track of addresses and signers"""

    def __init__(self, client_manager: ClientManager):
        """
        Create a new account manager.

        :param client_manager: The ClientManager client to use for algod and kmd clients
        """
        self._client_manager = client_manager
        self._accounts = dict[str, TransactionSigner]()
        self._default_signer: TransactionSigner | None = None

    def set_default_signer(self, signer: TransactionSigner) -> Self:
        """
        Sets the default signer to use if no other signer is specified.

        :param signer: The signer to use, either a `TransactionSigner` or a `TransactionSignerAccount`
        :return: The `AccountManager` so method calls can be chained
        """
        self._default_signer = signer
        return self

    def set_signer(self, sender: str, signer: TransactionSigner) -> Self:
        """
        Tracks the given account for later signing.

        :param sender: The sender address to use this signer for
        :param signer: The signer to sign transactions with for the given sender
        :return: The AccountCreator instance for method chaining
        """
        self._accounts[sender] = signer
        return self

    def get_signer(self, sender: str) -> TransactionSigner:
        """
        Returns the `TransactionSigner` for the given sender address.

        If no signer has been registered for that address then the default signer is used if registered.

        :param sender: The sender address
        :return: The `TransactionSigner` or throws an error if not found
        """
        signer = self._accounts.get(sender, None) or self._default_signer
        if not signer:
            raise ValueError(f"No signer found for address {sender}")
        return signer

    def get_information(self, sender: str) -> dict[str, Any]:
        """
        Returns the given sender account's current status, balance and spendable amounts.

        Example:
            address = "XBYLS2E6YI6XXL5BWCAMOA4GTWHXWENZMX5UHXMRNWWUQ7BXCY5WC5TEPA"
            account_info = account.get_information(address)

        `Response data schema details <https://developer.algorand.org/docs/rest-apis/algod/#get-v2accountsaddress>`_

        :param sender: The address of the sender/account to look up
        :return: The account information
        """
        info = self._client_manager.algod.account_info(sender)
        assert isinstance(info, dict)
        return info

    def get_asset_information(self, sender: str, asset_id: int) -> dict[str, Any]:
        info = self._client_manager.algod.account_asset_info(sender, asset_id)
        assert isinstance(info, dict)
        return info

    # TODO
    # def from_mnemonic(self, mnemonic_secret: str, sender: Optional[str] = None) -> AddrAndSigner:
    #     """
    #     Tracks and returns an Algorand account with secret key loaded (i.e. that can sign transactions) by taking the mnemonic secret.

    #     Example:
    #         account = account.from_mnemonic("mnemonic secret ...")
    #         rekeyed_account = account.from_mnemonic("mnemonic secret ...", "SENDERADDRESS...")

    #     :param mnemonic_secret: The mnemonic secret representing the private key of an account; **Note: Be careful how the mnemonic is handled**,
    #         never commit it into source control and ideally load it from the environment (ideally via a secret storage service) rather than the file system.
    #     :param sender: The optional sender address to use this signer for (aka a rekeyed account)
    #     :return: The account
    #     """
    #     account = mnemonic_account(mnemonic_secret)
    #     return self.signer_account(rekeyed_account(account, sender) if sender else account)

    def from_kmd(
        self,
        name: str,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
    ) -> AddressAndSigner:
        """
        Tracks and returns an Algorand account with private key loaded from the given KMD wallet (identified by name).

        Example (Get default funded account in a LocalNet):
            default_dispenser_account = account.from_kmd('unencrypted-default-wallet',
                lambda a: a['status'] != 'Offline' and a['amount'] > 1_000_000_000
            )

        :param name: The name of the wallet to retrieve an account from
        :param predicate: An optional filter to use to find the account (otherwise it will return a random account from the wallet)
        :return: The account
        """
        account = get_kmd_wallet_account(
            name=name, predicate=predicate, client=self._client_manager.algod, kmd_client=self._client_manager.kmd
        )
        if not account:
            raise ValueError(f"Unable to find KMD account {name}{' with predicate' if predicate else ''}")

        self.set_signer(account.address, account.signer)
        return AddressAndSigner(address=account.address, signer=account.signer)

    # TODO
    # def multisig(
    #     self, multisig_params: algosdk.MultisigMetadata, signing_accounts: Union[algosdk.Account, SigningAccount]
    # ) -> TransactionSignerAccount:
    #     """
    #     Tracks and returns an account that supports partial or full multisig signing.

    #     Example:
    #         account = account.multisig(
    #             {
    #                 "version": 1,
    #                 "threshold": 1,
    #                 "addrs": ["ADDRESS1...", "ADDRESS2..."]
    #             },
    #             account.from_environment('ACCOUNT1')
    #         )

    #     :param multisig_params: The parameters that define the multisig account
    #     :param signing_accounts: The signers that are currently present
    #     :return: A multisig account wrapper
    #     """
    #     return self.signer_account(multisig_account(multisig_params, signing_accounts))

    def random(self) -> AddressAndSigner:
        """
        Tracks and returns a new, random Algorand account with secret key loaded.

        Example:
            account = account.random()

        :return: The account
        """
        (sk, addr) = generate_account()  # type: ignore[no-untyped-call]
        signer = AccountTransactionSigner(sk)

        self.set_signer(addr, signer)

        return AddressAndSigner(address=addr, signer=signer)

    def dispenser(self) -> AddressAndSigner:
        """
        Returns an account (with private key loaded) that can act as a dispenser.

        Example:
            account = account.dispenser()

        If running on LocalNet then it will return the default dispenser account automatically,
        otherwise it will load the account mnemonic stored in os.environ['DISPENSER_MNEMONIC'].

        :return: The account
        """
        acct = get_dispenser_account(self._client_manager.algod)

        self.set_signer(acct.address, acct.signer)

        return AddressAndSigner(address=acct.address, signer=acct.signer)

    def localnet_dispenser(self) -> AddressAndSigner:
        """
        Returns an Algorand account with private key loaded for the default LocalNet dispenser account (that can be used to fund other accounts).

        Example:
            account = account.localnet_dispenser()

        :return: The account
        """
        acct = get_localnet_default_account(self._client_manager.algod)
        self.set_signer(acct.address, acct.signer)
        return AddressAndSigner(address=acct.address, signer=acct.signer)
