import json
from typing import TYPE_CHECKING

import pytest
from algokit_utils._debug_utils import AVMDebuggerSourceMap, PersistSourceMapInput, persist_sourcemaps

from tests.conftest import check_output_stability

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient


def test_build_teal_sourcemaps(algod_client: "AlgodClient", tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    approval = """
#pragma version 6
int 1
"""

    clear = """
#pragma version 6
int 1
"""
    sources = [
        PersistSourceMapInput(teal=approval, app_name="cool_app", file_name="approval.teal"),
        PersistSourceMapInput(teal=clear, app_name="cool_app", file_name="clear"),
    ]

    persist_sourcemaps(sources=sources, project_root=cwd, client=algod_client)

    root_path = cwd / ".algokit" / "sourcemaps"
    sourcemap_file_path = root_path / "avm.sources"
    app_output_path = root_path / "cool_app"

    assert (sourcemap_file_path).exists()
    assert (app_output_path / "approval.teal").exists()
    assert (app_output_path / "approval.tok.map").exists()
    assert (app_output_path / "clear.teal").exists()
    assert (app_output_path / "clear.tok.map").exists()

    result = AVMDebuggerSourceMap.from_dict(json.loads(sourcemap_file_path.read_text()))
    for item in result.txn_group_sources:
        item.location = "dummy"

    check_output_stability(json.dumps(result.to_dict()))
