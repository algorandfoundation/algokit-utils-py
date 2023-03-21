import pytest
from algokit_utils.account import get_account
from algokit_utils.application_client import ABICallArgs, ApplicationClient, get_app_id_from_tx_id
from algokit_utils.application_specification import ApplicationSpecification
from algokit_utils.network_clients import get_algod_client, get_indexer_client
from algosdk.atomic_transaction_composer import AtomicTransactionComposer
from algosdk.transaction import OnComplete

from tests.conftest import get_unique_name, read_spec


@pytest.fixture
def app_spec() -> ApplicationSpecification:
    app_spec = read_spec("app_client_test.json", deletable=True, updatable=True)
    return app_spec


@pytest.fixture
def client_fixture(app_spec: ApplicationSpecification) -> ApplicationClient:
    algod_client = get_algod_client()
    indexer_client = get_indexer_client()
    creator_name = get_unique_name()
    creator = get_account(algod_client, creator_name)

    client = ApplicationClient(algod_client, indexer_client, app_spec, creator=creator)
    return client


def test_bare_create(client_fixture: ApplicationClient) -> None:
    client_fixture.create(abi_method=False)

    assert client_fixture.call("hello", args={"name": "test"}).abi_result.return_value == "Hello Bare, test"


def test_abi_create(client_fixture: ApplicationClient) -> None:
    client_fixture.create("create")

    assert client_fixture.call("hello", args={"name": "test"}).abi_result.return_value == "Hello ABI, test"


def test_abi_create_args(client_fixture: ApplicationClient, app_spec: ApplicationSpecification) -> None:
    create = next(m for m in app_spec.contract.methods if m.name == "create_args")
    client_fixture.create(create, args={"greeting": "ahoy"})

    assert client_fixture.call("hello", args={"name": "test"}).abi_result.return_value == "ahoy, test"


def test_create_auto_find(client_fixture: ApplicationClient) -> None:
    client_fixture.create(on_complete=OnComplete.OptInOC)

    assert client_fixture.call("hello", args={"name": "test"}).abi_result.return_value == "Opt In, test"


def test_abi_create_with_atc(client_fixture: ApplicationClient) -> None:
    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create")

    create_result = atc.execute(client_fixture.algod_client, 4)
    client_fixture.app_id = get_app_id_from_tx_id(client_fixture.algod_client, create_result.tx_ids[0])

    assert client_fixture.call("hello", args={"name": "test"}).abi_result.return_value == "Hello ABI, test"


def test_bare_create_with_atc(client_fixture: ApplicationClient) -> None:
    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, abi_method=False)

    create_result = atc.execute(client_fixture.algod_client, 4)
    client_fixture.app_id = get_app_id_from_tx_id(client_fixture.algod_client, create_result.tx_ids[0])

    assert client_fixture.call("hello", args={"name": "test"}).abi_result.return_value == "Hello Bare, test"


def test_abi_call_with_atc(client_fixture: ApplicationClient) -> None:
    client_fixture.create("create")
    atc = AtomicTransactionComposer()
    client_fixture.compose_call(atc, "hello", args={"name": "test"})
    result = atc.execute(client_fixture.algod_client, 4)

    assert result.abi_results[0].return_value == "Hello ABI, test"


def test_abi_call_multiple_times_with_atc(client_fixture: ApplicationClient) -> None:
    client_fixture.create("create")
    atc = AtomicTransactionComposer()
    client_fixture.compose_call(atc, "hello", args={"name": "test"})
    client_fixture.compose_call(atc, "hello", args={"name": "test2"})
    client_fixture.compose_call(atc, "hello", args={"name": "test3"})
    result = atc.execute(client_fixture.algod_client, 4)

    assert result.abi_results[0].return_value == "Hello ABI, test"
    assert result.abi_results[1].return_value == "Hello ABI, test2"
    assert result.abi_results[2].return_value == "Hello ABI, test3"


def test_deploy_with_create(client_fixture: ApplicationClient) -> None:
    client_fixture.deploy(
        "v1",
        create_args=ABICallArgs(
            method="create",
        ),
    )

    assert client_fixture.call("hello", args={"name": "test"}).abi_result.return_value == "Hello ABI, test"


def test_deploy_with_create_args(client_fixture: ApplicationClient, app_spec: ApplicationSpecification) -> None:
    create_args = next(m for m in app_spec.contract.methods if m.name == "create_args")
    client_fixture.deploy("v1", create_args=ABICallArgs(method=create_args, args={"greeting": "deployed"}))

    assert client_fixture.call("hello", args={"name": "test"}).abi_result.return_value == "deployed, test"


def test_deploy_with_bare_create(client_fixture: ApplicationClient) -> None:
    client_fixture.deploy(
        "v1",
        create_args=ABICallArgs(
            method=False,
        ),
    )

    assert client_fixture.call("hello", args={"name": "test"}).abi_result.return_value == "Hello Bare, test"
