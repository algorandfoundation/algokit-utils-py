import pytest
from algokit_utils import (
    ApplicationClient,
    ApplicationSpecification,
    LogicError,
    get_account,
)
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from tests.conftest import check_output_stability, get_unique_name, is_opted_in


@pytest.fixture
def client_fixture(
    algod_client: AlgodClient, indexer_client: IndexerClient, app_spec: ApplicationSpecification
) -> ApplicationClient:
    creator_name = get_unique_name()
    creator = get_account(algod_client, creator_name)
    client = ApplicationClient(algod_client, app_spec, creator=creator, indexer_client=indexer_client)
    create_response = client.create("create")
    assert create_response.tx_id
    opt_in_response = client.opt_in("opt_in")
    assert opt_in_response.tx_id
    return client


def test_abi_close_out(client_fixture: ApplicationClient) -> None:
    assert is_opted_in(client_fixture)

    close_out_response = client_fixture.close_out("close_out")
    assert close_out_response.tx_id

    assert not is_opted_in(client_fixture)


def test_bare_close_out(client_fixture: ApplicationClient) -> None:
    assert is_opted_in(client_fixture)

    close_out_response = client_fixture.close_out(call_abi_method=False)
    assert close_out_response.tx_id

    assert not is_opted_in(client_fixture)


def test_abi_close_out_args(client_fixture: ApplicationClient) -> None:
    assert is_opted_in(client_fixture)

    close_out_response = client_fixture.close_out("close_out_args", check="Yes")
    assert close_out_response.tx_id

    assert not is_opted_in(client_fixture)


def test_abi_close_out_args_fails(client_fixture: ApplicationClient) -> None:
    assert is_opted_in(client_fixture)

    with pytest.raises(LogicError) as ex:
        client_fixture.close_out("close_out_args", check="No")

    check_output_stability(str(ex.value).replace(ex.value.transaction_id, "{txn}"))

    assert is_opted_in(client_fixture)
