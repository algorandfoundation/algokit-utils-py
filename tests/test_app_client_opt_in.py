import pytest
from algokit_utils import (
    Account,
    ApplicationClient,
    ApplicationSpecification,
    LogicError,
)
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from tests.conftest import check_output_stability, is_opted_in


@pytest.fixture
def client_fixture(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: ApplicationSpecification,
    funded_account: Account,
) -> ApplicationClient:
    client = ApplicationClient(algod_client, app_spec, creator=funded_account, indexer_client=indexer_client)
    client.create("create")
    return client


def test_abi_opt_in(client_fixture: ApplicationClient) -> None:
    opt_in_response = client_fixture.opt_in("opt_in")

    assert opt_in_response.tx_id
    assert client_fixture.call("get_last").return_value == "Opt In ABI"
    assert is_opted_in(client_fixture)


def test_bare_opt_in(client_fixture: ApplicationClient) -> None:
    opt_in_response = client_fixture.opt_in(call_abi_method=False)

    assert opt_in_response.tx_id
    assert client_fixture.call("get_last").return_value == "Opt In Bare"
    assert is_opted_in(client_fixture)


def test_abi_opt_in_args(client_fixture: ApplicationClient) -> None:
    update_response = client_fixture.opt_in("opt_in_args", check="Yes")

    assert update_response.tx_id
    assert client_fixture.call("get_last").return_value == "Opt In Args"
    assert is_opted_in(client_fixture)


def test_abi_update_args_fails(client_fixture: ApplicationClient) -> None:
    with pytest.raises(LogicError) as ex:
        client_fixture.opt_in("opt_in_args", check="No")

    check_output_stability(str(ex.value).replace(ex.value.transaction_id, "{txn}"))
    assert not is_opted_in(client_fixture)
