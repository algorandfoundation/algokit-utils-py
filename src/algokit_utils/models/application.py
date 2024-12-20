from dataclasses import dataclass
from typing import TYPE_CHECKING

import algosdk
from algosdk.source_map import SourceMap

if TYPE_CHECKING:
    pass

__all__ = [
    "AppCompilationResult",
    "AppInformation",
    "AppSourceMaps",
    "AppState",
    "CompiledTeal",
]


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
