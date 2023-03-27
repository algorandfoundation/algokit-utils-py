from algokit_utils import (
    ABICreateCallArgs,
    Account,
    ApplicationClient,
    ApplicationSpecification,
    TransferParameters,
    transfer,
)


def test_deploy_with_create(client_fixture: ApplicationClient, creator: Account) -> None:
    client_fixture.deploy(
        "v1",
        create_args=ABICreateCallArgs(
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
