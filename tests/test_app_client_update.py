import pytest
from algokit_utils import (
    Account,
    ApplicationClient,
    ApplicationSpecification,
    LogicError,
)
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from tests.conftest import check_output_stability


@pytest.fixture(scope="module")
def client_fixture(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: ApplicationSpecification,
    funded_account: Account,
) -> ApplicationClient:
    client = ApplicationClient(algod_client, app_spec, creator=funded_account, indexer_client=indexer_client)
    client.create("create")
    return client


def test_abi_update(client_fixture: ApplicationClient) -> None:
    update_response = client_fixture.update("update")

    assert update_response.tx_id
    assert client_fixture.call("hello", name="test").return_value == "Updated ABI, test"


def test_bare_update(client_fixture: ApplicationClient) -> None:
    update_response = client_fixture.update(call_abi_method=False)

    assert update_response.tx_id
    assert client_fixture.call("hello", name="test").return_value == "Updated Bare, test"


def test_abi_update_args(client_fixture: ApplicationClient) -> None:
    update_response = client_fixture.update("update_args", check="Yes")

    assert update_response.tx_id
    assert client_fixture.call("hello", name="test").return_value == "Updated Args, test"


def test_abi_update_args_fails(client_fixture: ApplicationClient) -> None:
    with pytest.raises(LogicError) as ex:
        client_fixture.update("update_args", check="No")

    check_output_stability(str(ex.value).replace(ex.value.transaction_id, "{txn}"))
