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


@pytest.fixture()
def client_fixture(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    funded_account: Account,
    app_spec: ApplicationSpecification,
) -> ApplicationClient:
    client = ApplicationClient(algod_client, app_spec, creator=funded_account, indexer_client=indexer_client)
    client.create("create")
    return client


def test_abi_delete(client_fixture: ApplicationClient) -> None:
    delete_response = client_fixture.delete("delete")

    assert delete_response.tx_id


def test_bare_delete(client_fixture: ApplicationClient) -> None:
    delete_response = client_fixture.delete(call_abi_method=False)

    assert delete_response.tx_id


def test_abi_delete_args(client_fixture: ApplicationClient) -> None:
    delete_response = client_fixture.delete("delete_args", check="Yes")

    assert delete_response.tx_id


def test_abi_delete_args_fails(client_fixture: ApplicationClient) -> None:
    with pytest.raises(LogicError) as ex:
        client_fixture.delete("delete_args", check="No")

    check_output_stability(str(ex.value).replace(ex.value.transaction_id, "{txn}"))
