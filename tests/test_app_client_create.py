from algokit_utils import (
    ApplicationClient,
    ApplicationSpecification,
    get_app_id_from_tx_id,
)
from algosdk.atomic_transaction_composer import AtomicTransactionComposer
from algosdk.transaction import OnComplete


def test_bare_create(client_fixture: ApplicationClient) -> None:
    client_fixture.create(abi_method=False)

    assert client_fixture.call("hello", name="test").return_value == "Hello Bare, test"


def test_abi_create(client_fixture: ApplicationClient) -> None:
    client_fixture.create("create")

    assert client_fixture.call("hello", name="test").return_value == "Hello ABI, test"


def test_abi_create_args(client_fixture: ApplicationClient, app_spec: ApplicationSpecification) -> None:
    create = next(m for m in app_spec.contract.methods if m.name == "create_args")
    client_fixture.create(create, greeting="ahoy")

    assert client_fixture.call("hello", name="test").return_value == "ahoy, test"


def test_create_auto_find(client_fixture: ApplicationClient) -> None:
    client_fixture.create(parameters={"on_complete": OnComplete.OptInOC})

    assert client_fixture.call("hello", name="test").return_value == "Opt In, test"


def test_abi_create_with_atc(client_fixture: ApplicationClient) -> None:
    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create")

    create_result = atc.execute(client_fixture.algod_client, 4)
    client_fixture.app_id = get_app_id_from_tx_id(client_fixture.algod_client, create_result.tx_ids[0])

    assert client_fixture.call("hello", name="test").return_value == "Hello ABI, test"


def test_bare_create_with_atc(client_fixture: ApplicationClient) -> None:
    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, abi_method=False)

    create_result = atc.execute(client_fixture.algod_client, 4)
    client_fixture.app_id = get_app_id_from_tx_id(client_fixture.algod_client, create_result.tx_ids[0])

    assert client_fixture.call("hello", name="test").return_value == "Hello Bare, test"
