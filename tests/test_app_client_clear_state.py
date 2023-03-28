import base64

import pytest
from algokit_utils import (
    Account,
    ApplicationClient,
    ApplicationSpecification,
)
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from tests.conftest import is_opted_in


@pytest.fixture
def client_fixture(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: ApplicationSpecification,
    funded_account: Account,
) -> ApplicationClient:
    client = ApplicationClient(algod_client, app_spec, creator=funded_account, indexer_client=indexer_client)
    create_response = client.create("create")
    assert create_response.tx_id
    opt_in_response = client.opt_in("opt_in")
    assert opt_in_response.tx_id
    return client


def test_clear_state(client_fixture: ApplicationClient) -> None:
    assert is_opted_in(client_fixture)

    close_out_response = client_fixture.clear_state()
    assert close_out_response.tx_id

    assert not is_opted_in(client_fixture)


def test_clear_state_app_already_deleted(client_fixture: ApplicationClient) -> None:
    assert is_opted_in(client_fixture)

    client_fixture.delete("delete")
    assert is_opted_in(client_fixture)

    close_out_response = client_fixture.clear_state()
    assert close_out_response.tx_id

    assert not is_opted_in(client_fixture)


def test_clear_state_app_args(client_fixture: ApplicationClient) -> None:
    assert is_opted_in(client_fixture)
    app_args = [b"test", b"data"]

    close_out_response = client_fixture.clear_state(app_args=app_args)
    assert close_out_response.tx_id

    tx_info = client_fixture.algod_client.pending_transaction_info(close_out_response.tx_id)
    assert isinstance(tx_info, dict)
    assert [base64.b64decode(x) for x in tx_info["txn"]["txn"]["apaa"]] == app_args
