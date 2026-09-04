"""Demonstrates the application layer — app factories, app clients, idempotent
deployment, state access, and logic-error handling.

This maps to the Concepts -> Applications docs page. Two app specs
are used here: `examples/artifacts/HelloWorld.arc56.json` (the algokit template's
hello-world contract, used for factory creation and deployment) and
`examples/artifacts/State.arc56.json` (a test contract with ABI methods,
global/local/box state, and deploy-time template variables).

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.applications``.
"""

from pathlib import Path

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AppClient,
    AppClientMethodCallParams,
    AppCreateParams,
    FundAppAccountParams,
    LogicError,
    OnSchemaBreak,
    OnUpdate,
    OperationPerformed,
    PaymentParams,
    SigningAccount,
)
from examples._helpers import setup_localnet_environment

# Minimal approve-everything TEAL pair for the raw-layer create call.
APPROVAL_TEAL = "#pragma version 12\nint 1"
CLEAR_STATE_TEAL = "#pragma version 12\nint 1"


def deploy_hello_world(algorand: AlgorandClient, deployer: SigningAccount) -> None:
    # example: GET_APP_FACTORY
    app_spec = Path("examples/artifacts/HelloWorld.arc56.json").read_text()
    factory = algorand.client.get_app_factory(
        app_spec=app_spec,
        default_sender=deployer.address,
    )
    # example: GET_APP_FACTORY

    # example: DEPLOY_APP
    app_client, deploy_result = factory.deploy()
    print(f"{deploy_result.operation_performed}: app {app_client.app_id} at {app_client.app_address}")
    # example: DEPLOY_APP
    assert deploy_result.operation_performed == OperationPerformed.Create

    # example: FUND_APP_ACCOUNT
    app_client.send.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=1)))
    # example: FUND_APP_ACCOUNT

    # example: FUND_APP_ACCOUNT_ON_CREATE
    # Fund the app account only when the deployment created a fresh app instance
    if deploy_result.operation_performed in (OperationPerformed.Create, OperationPerformed.Replace):
        app_client.send.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=1)))
    # example: FUND_APP_ACCOUNT_ON_CREATE


def template_variables_and_redeploy(algorand: AlgorandClient, deployer: SigningAccount) -> AppClient:
    # example: TEMPLATE_VARIABLES
    app_spec = Path("examples/artifacts/State.arc56.json").read_text()
    factory = algorand.client.get_app_factory(
        app_spec=app_spec,
        default_sender=deployer.address,
    )
    app_client, deploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {"VALUE": 1},
            "updatable": True,
            "deletable": True,
        },
    )
    # example: TEMPLATE_VARIABLES
    assert deploy_result.operation_performed == OperationPerformed.Create

    # example: REDEPLOY_APP
    # Deploying unchanged code performs no transactions
    _, redeploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {"VALUE": 1},
            "updatable": True,
            "deletable": True,
        },
    )
    print(redeploy_result.operation_performed)  # OperationPerformed.Nothing

    # A change in the compiled program becomes an in-place update;
    # a schema break would deploy a fresh app rather than fail
    _, update_result = factory.deploy(
        on_update=OnUpdate.UpdateApp,
        on_schema_break=OnSchemaBreak.AppendApp,
        compilation_params={
            "deploy_time_params": {"VALUE": 2},
            "updatable": True,
            "deletable": True,
        },
    )
    print(update_result.operation_performed)  # OperationPerformed.Update
    # example: REDEPLOY_APP
    assert redeploy_result.operation_performed == OperationPerformed.Nothing
    assert update_result.operation_performed == OperationPerformed.Update

    # example: GET_APP_CLIENT
    same_app_client = algorand.client.get_app_client_by_id(
        app_spec=app_spec,
        app_id=app_client.app_id,
        default_sender=deployer.address,
    )
    # example: GET_APP_CLIENT
    assert same_app_client.app_id == app_client.app_id

    return app_client


def method_calls(algorand: AlgorandClient, app_client: AppClient, deployer: SigningAccount) -> None:
    # example: CALL_APP_METHOD
    call_result = app_client.send.call(AppClientMethodCallParams(method="call_abi", args=["from the docs"]))
    print(call_result.abi_return)  # Hello, from the docs
    # example: CALL_APP_METHOD
    assert call_result.abi_return == "Hello, from the docs"

    # example: DEFAULT_ARGUMENTS
    default_result = app_client.send.call(AppClientMethodCallParams(method="default_value", args=[None]))
    # example: DEFAULT_ARGUMENTS
    assert default_result.abi_return == "default value"

    # example: CALL_APP_METHOD_WITH_TXN_ARG
    payment = algorand.create_transaction.payment(
        PaymentParams(
            sender=deployer.address,
            receiver=app_client.app_address,
            amount=AlgoAmount(algo=1),
        )
    )
    txn_arg_result = app_client.send.call(
        AppClientMethodCallParams(method="call_abi_txn", args=[payment, "with payment"])
    )
    print(txn_arg_result.abi_return)  # Sent 1000000. with payment
    # example: CALL_APP_METHOD_WITH_TXN_ARG
    assert txn_arg_result.abi_return == "Sent 1000000. with payment"


def state_and_errors(app_client: AppClient, deployer: SigningAccount) -> None:
    # example: READ_GLOBAL_STATE
    # The contract's set_global method stores its arguments in the global state keys int1, int2, bytes1, bytes2
    app_client.send.call(AppClientMethodCallParams(method="set_global", args=[10, 20, "text", b"1234"]))
    int1 = app_client.state.global_state.get_value("int1")  # 10
    all_global_state = app_client.state.global_state.get_all()
    # example: READ_GLOBAL_STATE
    assert int1 == 10
    assert all_global_state["int2"] == 20

    # example: READ_LOCAL_STATE
    # set_local stores its arguments in the caller's local state keys local_int1, local_int2, local_bytes1, local_bytes2
    app_client.send.opt_in(AppClientMethodCallParams(method="opt_in"))
    app_client.send.call(AppClientMethodCallParams(method="set_local", args=[1, 2, "text", b"1234"]))
    local_int1 = app_client.state.local_state(deployer.address).get_value("local_int1")  # 1
    # example: READ_LOCAL_STATE
    assert local_int1 == 1

    # Box storage requires the app account to cover the box minimum balance requirement
    app_client.send.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=1)))

    # example: READ_BOX_STATE
    # This contract's "box" map is keyed by byte[4] values; boxes with string names take plain strings
    box_key = b"\x00\x00\x00\x01"
    app_client.send.call(
        AppClientMethodCallParams(method="set_box", args=[box_key, "box content"], box_references=[box_key])
    )

    box_value = app_client.state.box.get_map_value("box", box_key)
    box_map = app_client.state.box.get_map("box")  # {'[0, 0, 0, 1]': 'box content'}
    # example: READ_BOX_STATE
    assert box_value == "box content"
    assert box_map == {"[0, 0, 0, 1]": "box content"}

    # example: HANDLE_LOGIC_ERROR
    try:
        app_client.send.call(AppClientMethodCallParams(method="error"))
    except LogicError as e:
        print(f"Call failed at TEAL line {e.line_no}: {e.message}")
    # example: HANDLE_LOGIC_ERROR


def raw_layer(algorand: AlgorandClient, deployer: SigningAccount) -> None:
    # example: CREATE_AND_READ_APP
    # Send a bare creation transaction through the transaction layer
    create_result = algorand.send.app_create(
        AppCreateParams(
            sender=deployer.address,
            approval_program=APPROVAL_TEAL,
            clear_state_program=CLEAR_STATE_TEAL,
        )
    )

    # Read the app back through the AppManager
    app_info = algorand.app.get_by_id(create_result.app_id)
    print(f"App {app_info.app_id} created at address {app_info.app_address}")
    # example: CREATE_AND_READ_APP
    assert app_info.app_id == create_result.app_id
    assert app_info.creator == deployer.address


def main() -> None:
    env = setup_localnet_environment()
    algorand = env.algorand
    deployer = env.account_a

    deploy_hello_world(algorand, deployer)
    app_client = template_variables_and_redeploy(algorand, deployer)
    method_calls(algorand, app_client, deployer)
    state_and_errors(app_client, deployer)
    raw_layer(algorand, deployer)


if __name__ == "__main__":
    main()
