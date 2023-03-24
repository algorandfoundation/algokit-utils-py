from algokit_utils import (
    ABICallArgs,
    Account,
    ApplicationClient,
    ApplicationSpecification,
    DefaultArgumentDict,
    TransferParameters,
    get_app_id_from_tx_id,
    transfer,
)
from algosdk.atomic_transaction_composer import AtomicTransactionComposer
from algosdk.transaction import OnComplete
from algosdk.v2client.algod import AlgodClient
from conftest import read_spec


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


def test_abi_call_with_atc(client_fixture: ApplicationClient) -> None:
    client_fixture.create("create")
    atc = AtomicTransactionComposer()
    client_fixture.compose_call(atc, "hello", name="test")
    result = atc.execute(client_fixture.algod_client, 4)

    assert result.abi_results[0].return_value == "Hello ABI, test"


def test_abi_call_multiple_times_with_atc(client_fixture: ApplicationClient) -> None:
    client_fixture.create("create")
    atc = AtomicTransactionComposer()
    client_fixture.compose_call(atc, "hello", name="test")
    client_fixture.compose_call(atc, "hello", name="test2")
    client_fixture.compose_call(atc, "hello", name="test3")
    result = atc.execute(client_fixture.algod_client, 4)

    assert result.abi_results[0].return_value == "Hello ABI, test"
    assert result.abi_results[1].return_value == "Hello ABI, test2"
    assert result.abi_results[2].return_value == "Hello ABI, test3"


def test_deploy_with_create(client_fixture: ApplicationClient, creator: Account) -> None:
    client_fixture.deploy(
        "v1",
        create_args=ABICallArgs(
            method="create",
        ),
    )

    transfer(
        TransferParameters(from_account=creator, to_address=client_fixture.app_address, amount=100_000),
        client_fixture.algod_client,
    )

    assert client_fixture.call("hello", name="test").return_value == "Hello ABI, test"


def test_deploy_with_create_args(client_fixture: ApplicationClient, app_spec: ApplicationSpecification) -> None:
    create_args = next(m for m in app_spec.contract.methods if m.name == "create_args")
    client_fixture.deploy("v1", create_args=ABICallArgs(method=create_args, args={"greeting": "deployed"}))

    assert client_fixture.call("hello", name="test").return_value == "deployed, test"


def test_deploy_with_bare_create(client_fixture: ApplicationClient) -> None:
    client_fixture.deploy(
        "v1",
        create_args=ABICallArgs(
            method=False,
        ),
    )

    assert client_fixture.call("hello", name="test").return_value == "Hello Bare, test"


def test_resolve(algod_client: AlgodClient, creator: Account) -> None:
    app_spec = read_spec("app_resolve.json")
    client_fixture = ApplicationClient(algod_client, app_spec, signer=creator)
    client_fixture.create()
    client_fixture.opt_in()

    int_default_argument: DefaultArgumentDict = {"source": "constant", "data": 1}
    assert client_fixture.resolve(int_default_argument) == 1

    string_default_argument: DefaultArgumentDict = {"source": "constant", "data": "stringy"}
    assert client_fixture.resolve(string_default_argument) == "stringy"

    global_state_int_default_argument: DefaultArgumentDict = {
        "source": "global-state",
        "data": "global_state_val_int",
    }
    assert client_fixture.resolve(global_state_int_default_argument) == 1

    global_state_byte_default_argument: DefaultArgumentDict = {
        "source": "global-state",
        "data": "global_state_val_byte",
    }
    assert client_fixture.resolve(global_state_byte_default_argument) == b"test"

    local_state_int_default_argument: DefaultArgumentDict = {
        "source": "local-state",
        "data": "acct_state_val_int",
    }
    assert client_fixture.resolve(local_state_int_default_argument) == 2

    local_state_byte_default_argument: DefaultArgumentDict = {
        "source": "local-state",
        "data": "acct_state_val_byte",
    }
    assert client_fixture.resolve(local_state_byte_default_argument) == b"local-test"

    method_default_argument: DefaultArgumentDict = {
        "source": "abi-method",
        "data": {"name": "dummy", "args": [], "returns": {"type": "string"}},
    }
    assert client_fixture.resolve(method_default_argument) == "deadbeef"
