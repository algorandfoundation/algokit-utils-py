from typing import TYPE_CHECKING

import pytest

from algokit_utils import (
    ABICreateCallArgs,
    Account,
    ApplicationClient,
    ApplicationSpecification,
    TransferParameters,
    transfer,
)
from legacy_v2_tests.conftest import get_unique_name, read_spec

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient
    from algosdk.v2client.indexer import IndexerClient


@pytest.fixture
def client_fixture(
    algod_client: "AlgodClient",
    indexer_client: "IndexerClient",
    funded_account: Account,
) -> ApplicationClient:
    app_spec = read_spec("app_client_test.json", deletable=True, updatable=True, template_values={"VERSION": 1})
    return ApplicationClient(
        algod_client, app_spec, creator=funded_account, indexer_client=indexer_client, app_name=get_unique_name()
    )


def test_deploy_with_create(client_fixture: ApplicationClient, creator: Account) -> None:
    client_fixture.deploy(
        "v1",
        create_args=ABICreateCallArgs(
            method="create",
        ),
    )

    transfer(
        client_fixture.algod_client,
        TransferParameters(from_account=creator, to_address=client_fixture.app_address, micro_algos=100_000),
    )

    assert client_fixture.call("hello", name="test").return_value == "Hello ABI, test"


def test_deploy_with_create_args(client_fixture: ApplicationClient, app_spec: ApplicationSpecification) -> None:
    create_args = next(m for m in app_spec.contract.methods if m.name == "create_args")
    client_fixture.deploy("v1", create_args=ABICreateCallArgs(method=create_args, args={"greeting": "deployed"}))

    assert client_fixture.call("hello", name="test").return_value == "deployed, test"


def test_deploy_with_bare_create(client_fixture: ApplicationClient) -> None:
    client_fixture.deploy(
        "v1",
        create_args=ABICreateCallArgs(
            method=False,
        ),
    )

    assert client_fixture.call("hello", name="test").return_value == "Hello Bare, test"
