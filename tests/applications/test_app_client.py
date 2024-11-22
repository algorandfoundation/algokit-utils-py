from pathlib import Path

import pytest

from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.applications.app_client import (
    AppClient,
    AppClientMethodCallParams,
    AppClientParams,
    CloneAppClientParams,
    ResolveAppClientByNetwork,
)
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.applications.utils import arc32_to_arc56
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.models.account import Account
from algokit_utils.models.application import Arc56Contract
from algokit_utils.transactions.transaction_composer import AppCreateParams


@pytest.fixture
def algorand(funded_account: Account) -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_signer(sender=funded_account.address, signer=funded_account.signer)
    return client


@pytest.fixture
def raw_hello_world_arc32_app_spec() -> str:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "hello_world" / "arc32_app_spec.json"
    return raw_json_spec.read_text()


@pytest.fixture
def hello_world_arc32_app_spec() -> ApplicationSpecification:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "hello_world" / "arc32_app_spec.json"
    return ApplicationSpecification.from_json(raw_json_spec.read_text())


@pytest.fixture
def hello_world_arc32_app_id(
    algorand: AlgorandClient, funded_account: Account, hello_world_arc32_app_spec: ApplicationSpecification
) -> int:
    global_schema = hello_world_arc32_app_spec.global_state_schema
    local_schema = hello_world_arc32_app_spec.local_state_schema
    response = algorand.send.app_create(
        AppCreateParams(
            sender=funded_account.address,
            approval_program=hello_world_arc32_app_spec.approval_program,
            clear_state_program=hello_world_arc32_app_spec.clear_program,
            schema={
                "global_ints": global_schema.num_uints,
                "global_bytes": global_schema.num_byte_slices,
                "local_ints": local_schema.num_uints,
                "local_bytes": local_schema.num_byte_slices,
            },  # type: ignore[arg-type]
        )
    )
    return response.app_id


@pytest.fixture
def raw_testing_app_arc32_app_spec() -> str:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "testing_app" / "arc32_app_spec.json"
    return raw_json_spec.read_text()


@pytest.fixture
def testing_app_arc32_app_spec() -> ApplicationSpecification:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "testing_app" / "arc32_app_spec.json"
    return ApplicationSpecification.from_json(raw_json_spec.read_text())


@pytest.fixture
def testing_app_arc32_app_id(
    algorand: AlgorandClient, funded_account: Account, testing_app_arc32_app_spec: ApplicationSpecification
) -> int:
    global_schema = testing_app_arc32_app_spec.global_state_schema
    local_schema = testing_app_arc32_app_spec.local_state_schema
    approval = AppManager.replace_template_variables(
        testing_app_arc32_app_spec.approval_program,
        {
            "VALUE": 1,
            "UPDATABLE": 0,
            "DELETABLE": 0,
        },
    )
    response = algorand.send.app_create(
        AppCreateParams(
            sender=funded_account.address,
            approval_program=approval,
            clear_state_program=testing_app_arc32_app_spec.clear_program,
            schema={
                "global_bytes": global_schema.num_byte_slices,
                "global_ints": global_schema.num_uints,
                "local_bytes": local_schema.num_byte_slices,
                "local_ints": local_schema.num_uints,
            },  # type: ignore[arg-type]
        )
    )
    return response.app_id


# TODO: add variations around arc 56 contracts too


def test_clone_overriding_default_sender_and_inheriting_app_name(
    algorand: AlgorandClient,
    funded_account: Account,
    hello_world_arc32_app_spec: ApplicationSpecification,
    hello_world_arc32_app_id: int,
) -> None:
    app_client = AppClient(
        AppClientParams(
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            app_id=hello_world_arc32_app_id,
            algorand=algorand,
            app_spec=hello_world_arc32_app_spec,
        )
    )

    cloned_default_sender = "ABC" * 55
    cloned_app_client = app_client.clone(CloneAppClientParams(default_sender=cloned_default_sender))

    assert app_client.app_name == "HelloWorld"
    assert cloned_app_client.app_id == app_client.app_id
    assert cloned_app_client.app_name == app_client.app_name
    assert cloned_app_client._default_sender == cloned_default_sender  # noqa: SLF001
    assert app_client._default_sender == funded_account.address  # noqa: SLF001


def test_clone_overriding_app_name(
    algorand: AlgorandClient,
    funded_account: Account,
    hello_world_arc32_app_spec: ApplicationSpecification,
    hello_world_arc32_app_id: int,
) -> None:
    app_client = AppClient(
        AppClientParams(
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            app_id=hello_world_arc32_app_id,
            algorand=algorand,
            app_spec=hello_world_arc32_app_spec,
        )
    )

    cloned_app_name = "George CLONEy"
    cloned_app_client = app_client.clone(CloneAppClientParams(app_name=cloned_app_name))
    assert app_client.app_name == hello_world_arc32_app_spec.contract.name == "HelloWorld"
    assert cloned_app_client.app_name == cloned_app_name


def test_clone_inheriting_app_name_based_on_default_handling(
    algorand: AlgorandClient,
    funded_account: Account,
    hello_world_arc32_app_spec: ApplicationSpecification,
    hello_world_arc32_app_id: int,
) -> None:
    app_client = AppClient(
        AppClientParams(
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            app_id=hello_world_arc32_app_id,
            algorand=algorand,
            app_spec=hello_world_arc32_app_spec,
        )
    )

    cloned_app_name = None
    cloned_app_client = app_client.clone(CloneAppClientParams(app_name=cloned_app_name))
    assert cloned_app_client.app_name == hello_world_arc32_app_spec.contract.name == app_client.app_name


def test_normalise_app_spec(
    raw_hello_world_arc32_app_spec: str,
    hello_world_arc32_app_spec: ApplicationSpecification,
) -> None:
    normalized_app_spec_from_arc32 = AppClient.normalise_app_spec(hello_world_arc32_app_spec)
    assert isinstance(normalized_app_spec_from_arc32, Arc56Contract)

    normalize_app_spec_from_raw_arc32 = AppClient.normalise_app_spec(raw_hello_world_arc32_app_spec)
    assert isinstance(normalize_app_spec_from_raw_arc32, Arc56Contract)


def test_resolve_from_network(
    algorand: AlgorandClient,
    hello_world_arc32_app_id: int,
    hello_world_arc32_app_spec: ApplicationSpecification,
) -> None:
    arc56_app_spec = arc32_to_arc56(hello_world_arc32_app_spec)
    arc56_app_spec.networks = {"localnet": {"app_id": hello_world_arc32_app_id}}
    app_client = AppClient.from_network(
        ResolveAppClientByNetwork(
            algorand=algorand,
            app_spec=arc56_app_spec,
        )
    )

    assert app_client


# TODO: see if needs moving into app factory tests file
def test_abi_with_default_arg_method(
    algorand: AlgorandClient,
    funded_account: Account,
    testing_app_arc32_app_id: int,
    testing_app_arc32_app_spec: ApplicationSpecification,
) -> None:
    arc56_app_spec = arc32_to_arc56(testing_app_arc32_app_spec)
    arc56_app_spec.networks = {"localnet": {"app_id": testing_app_arc32_app_id}}
    app_client = AppClient.from_network(
        ResolveAppClientByNetwork(
            algorand=algorand,
            app_spec=arc56_app_spec,
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
        )
    )

    # Test with defined value
    defined_value_result = app_client.send.call(
        AppClientMethodCallParams(method="default_value_from_local_state(string)string", args=["defined value"])
    )
    assert defined_value_result.return_value == "Local state, defined value"

    # Test with default value
    default_value_result = app_client.send.call(AppClientMethodCallParams(method="hello(string)string", args=[None]))
    assert default_value_result.return_value == "Hello, default"
