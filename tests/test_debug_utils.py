from typing import TYPE_CHECKING

import pytest
from algokit_utils._debug_utils import PersistSourceMapInput, persist_sourcemaps
from algokit_utils.config import config

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient


def test_build_teal_sourcemaps(algod_client: "AlgodClient", tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    config.configure(debug=True, project_root=cwd)

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

    persist_sourcemaps(sources=sources, client=algod_client)
