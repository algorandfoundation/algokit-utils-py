from dataclasses import dataclass
from typing import Literal

import algosdk
from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.source_map import SourceMap

from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.applications.app_spec.arc56 import Arc56Contract
from algokit_utils.models.state import TealTemplateParams
from algokit_utils.protocols.client import AlgorandClientProtocol

__all__: list[str] = [
    "DELETABLE_TEMPLATE_NAME",
    "UPDATABLE_TEMPLATE_NAME",
    "BoxRecommendation",
    "CallConfig",
    "CompilerInfo",
    "CompilerVersion",
    "Recommendations",
]

UPDATABLE_TEMPLATE_NAME = "TMPL_UPDATABLE"
"""The name of the TEAL template variable for deploy-time immutability control."""

DELETABLE_TEMPLATE_NAME = "TMPL_DELETABLE"
"""The name of the TEAL template variable for deploy-time permanence control."""


@dataclass
class CallConfig:
    no_op: str | None = None
    opt_in: str | None = None
    close_out: str | None = None
    clear_state: str | None = None
    update_application: str | None = None
    delete_application: str | None = None


@dataclass(kw_only=True)
class BoxRecommendation:
    app: int | None = None
    key: str = ""
    read_bytes: int = 0
    write_bytes: int = 0


@dataclass(kw_only=True)
class Recommendations:
    inner_transaction_count: int | None = None
    boxes: list[BoxRecommendation] | None = None
    accounts: list[str] | None = None
    apps: list[int] | None = None
    assets: list[int] | None = None


@dataclass(kw_only=True)
class CompilerVersion:
    major: int
    minor: int
    patch: int
    commit_hash: str | None = None


@dataclass(kw_only=True)
class CompilerInfo:
    compiler: Literal["algod", "puya"]
    compiler_version: CompilerVersion


@dataclass(kw_only=True, frozen=True)
class AppState:
    key_raw: bytes
    key_base64: str
    value_raw: bytes | None
    value_base64: str | None
    value: str | int


@dataclass(kw_only=True, frozen=True)
class AppInformation:
    app_id: int
    app_address: str
    approval_program: bytes
    clear_state_program: bytes
    creator: str
    global_state: dict[str, AppState]
    local_ints: int
    local_byte_slices: int
    global_ints: int
    global_byte_slices: int
    extra_program_pages: int | None


@dataclass(kw_only=True, frozen=True)
class CompiledTeal:
    teal: str
    compiled: bytes
    compiled_hash: str
    compiled_base64_to_bytes: bytes
    source_map: algosdk.source_map.SourceMap | None


@dataclass(kw_only=True, frozen=True)
class AppCompilationResult:
    compiled_approval: CompiledTeal
    compiled_clear: CompiledTeal


@dataclass(kw_only=True, frozen=True)
class AppSourceMaps:
    approval_source_map: SourceMap | None = None
    clear_source_map: SourceMap | None = None


@dataclass(kw_only=True, frozen=True)
class AppClientCompilationResult:
    approval_program: bytes
    clear_state_program: bytes
    compiled_approval: CompiledTeal | None = None
    compiled_clear: CompiledTeal | None = None


@dataclass(kw_only=True, frozen=True)
class AppClientParams:
    """Full parameters for creating an app client"""

    app_spec: (
        Arc56Contract | ApplicationSpecification | str
    )  # Using string quotes since these types may be defined elsewhere
    algorand: AlgorandClientProtocol  # Using string quotes since this type may be defined elsewhere
    app_id: int
    app_name: str | None = None
    default_sender: str | bytes | None = None  # Address can be string or bytes
    default_signer: TransactionSigner | None = None
    approval_source_map: SourceMap | None = None
    clear_source_map: SourceMap | None = None


@dataclass(kw_only=True, frozen=True)
class AppClientCompilationParams:
    deploy_time_params: TealTemplateParams | None = None
    updatable: bool | None = None
    deletable: bool | None = None
