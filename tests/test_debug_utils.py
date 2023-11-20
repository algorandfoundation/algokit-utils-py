from typing import TYPE_CHECKING

import pytest
from algokit_utils._debug_utils import persist_sourcemaps
from algokit_utils.config import config

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient


def test_build_teal_sourcemap(algod_client: "AlgodClient", tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    config.configure(debug=True, project_root=str(cwd))

    approval = """
#pragma version 6
int 1
"""

    clear = """
#pragma version 6
int 1
"""

    persist_sourcemaps(approval=approval, clear=clear, app_name="cool_app", client=algod_client)
