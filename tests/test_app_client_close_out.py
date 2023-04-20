from typing import TYPE_CHECKING

import pytest
from algokit_utils import (
    Account,
    ApplicationClient,
    ApplicationSpecification,
    LogicError,
)

from tests.conftest import check_output_stability, is_opted_in

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient
    from algosdk.v2client.indexer import IndexerClient


@pytest.fixture()
def client_fixture(
    algod_client: "AlgodClient",
    indexer_client: "IndexerClient",
    app_spec: ApplicationSpecification,
    funded_account: Account,
) -> ApplicationClient:
    client = ApplicationClient(algod_client, app_spec, creator=funded_account, indexer_client=indexer_client)
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
