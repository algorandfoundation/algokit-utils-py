import pytest
from algokit_utils import (
    ApplicationClient,
    ApplicationSpecification,
    get_app_id_from_tx_id,
)
from algosdk.atomic_transaction_composer import AtomicTransactionComposer
from algosdk.transaction import OnComplete


def test_bare_create(client_fixture: ApplicationClient) -> None:
    client_fixture.create(call_abi_method=False)

    assert client_fixture.call("hello", name="test").return_value == "Hello Bare, test"


def test_abi_create(client_fixture: ApplicationClient) -> None:
    client_fixture.create("create")

    assert client_fixture.call("hello", name="test").return_value == "Hello ABI, test"


@pytest.mark.parametrize("method", ["create_args", "create_args(string)void", True])
def test_abi_create_args(
    method: str | bool, client_fixture: ApplicationClient, app_spec: ApplicationSpecification
) -> None:
    client_fixture.create(method, greeting="ahoy")

    assert client_fixture.call("hello", name="test").return_value == "ahoy, test"


def test_create_auto_find(client_fixture: ApplicationClient) -> None:
    client_fixture.create(transaction_parameters={"on_complete": OnComplete.OptInOC})

    assert client_fixture.call("hello", name="test").return_value == "Opt In, test"


def test_abi_create_with_atc(client_fixture: ApplicationClient) -> None:
    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create")

    create_result = atc.execute(client_fixture.algod_client, 4)
    client_fixture.app_id = get_app_id_from_tx_id(client_fixture.algod_client, create_result.tx_ids[0])

    assert client_fixture.call("hello", name="test").return_value == "Hello ABI, test"


def test_bare_create_with_atc(client_fixture: ApplicationClient) -> None:
    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, call_abi_method=False)

    create_result = atc.execute(client_fixture.algod_client, 4)
    client_fixture.app_id = get_app_id_from_tx_id(client_fixture.algod_client, create_result.tx_ids[0])

    assert client_fixture.call("hello", name="test").return_value == "Hello Bare, test"