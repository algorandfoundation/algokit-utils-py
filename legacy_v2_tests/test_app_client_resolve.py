from typing import TYPE_CHECKING

from algokit_utils import (
    Account,
    ApplicationClient,
    DefaultArgumentDict,
)
from legacy_v2_tests.conftest import read_spec

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient


def test_resolve(algod_client: "AlgodClient", creator: Account) -> None:
    app_spec = read_spec("app_resolve.json")
    client_fixture = ApplicationClient(algod_client, app_spec, signer=creator)
    client_fixture.create()
    client_fixture.opt_in()

    int_default_argument: DefaultArgumentDict = {"source": "constant", "data": 1}
    assert client_fixture.resolve(int_default_argument) == 1

    string_default_argument: DefaultArgumentDict = {"source": "constant", "data": "stringy"}
    assert client_fixture.resolve(string_default_argument) == "stringy"

    global_state_int_default_argument: DefaultArgumentDict = {
        "source": "global-state",
        "data": "global_state_val_int",
    }
    assert client_fixture.resolve(global_state_int_default_argument) == 1

    global_state_byte_default_argument: DefaultArgumentDict = {
        "source": "global-state",
        "data": "global_state_val_byte",
    }
    assert client_fixture.resolve(global_state_byte_default_argument) == b"test"

    local_state_int_default_argument: DefaultArgumentDict = {
        "source": "local-state",
        "data": "acct_state_val_int",
    }
    acct_state_val_int_value = 2  # defined in TEAL
    assert client_fixture.resolve(local_state_int_default_argument) == acct_state_val_int_value

    local_state_byte_default_argument: DefaultArgumentDict = {
        "source": "local-state",
        "data": "acct_state_val_byte",
    }
    assert client_fixture.resolve(local_state_byte_default_argument) == b"local-test"

    method_default_argument: DefaultArgumentDict = {
        "source": "abi-method",
        "data": {"name": "dummy", "args": [], "returns": {"type": "string"}},
    }
    assert client_fixture.resolve(method_default_argument) == "deadbeef"
