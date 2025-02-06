from pathlib import Path

import algosdk
import pytest
from algosdk.logic import get_application_address
from algosdk.transaction import OnComplete

from algokit_utils.algorand import AlgorandClient
from algokit_utils.applications.app_client import (
    AppClient,
    AppClientMethodCallCreateParams,
    AppClientMethodCallParams,
    AppClientParams,
)
from algokit_utils.applications.app_deployer import OnSchemaBreak, OnUpdate, OperationPerformed
from algokit_utils.applications.app_factory import (
    AppFactory,
    AppFactoryCreateMethodCallParams,
    AppFactoryCreateParams,
)
from algokit_utils.applications.app_spec.arc56 import Arc56Contract
from algokit_utils.errors import LogicError
from algokit_utils.models.account import SigningAccount
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import PaymentParams


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> SigningAccount:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account, dispenser, AlgoAmount.from_algo(100), min_funding_increment=AlgoAmount.from_algo(1)
    )
    algorand.set_signer(sender=new_account.address, signer=new_account.signer)
    return new_account


@pytest.fixture
def app_spec() -> str:
    return (Path(__file__).parent.parent / "artifacts" / "testing_app" / "app_spec.arc32.json").read_text()


@pytest.fixture
def factory(algorand: AlgorandClient, funded_account: SigningAccount, app_spec: str) -> AppFactory:
    """Create AppFactory fixture"""
    return algorand.client.get_app_factory(app_spec=app_spec, default_sender=funded_account.address)


@pytest.fixture
def arc56_factory(
    algorand: AlgorandClient,
    funded_account: SigningAccount,
) -> AppFactory:
    """Create AppFactory fixture"""
    arc56_raw_spec = (
        Path(__file__).parent.parent / "artifacts" / "testing_app_arc56" / "app_spec.arc56.json"
    ).read_text()
    return algorand.client.get_app_factory(app_spec=arc56_raw_spec, default_sender=funded_account.address)


def test_create_app(factory: AppFactory) -> None:
    """Test creating an app using the factory"""
    app_client, result = factory.send.bare.create(
        params=AppFactoryCreateParams(),
        compilation_params={
            "deploy_time_params": {
                # It should strip off the TMPL_
                "TMPL_UPDATABLE": 0,
                "DELETABLE": 0,
                "VALUE": 1,
            }
        },
    )

    assert app_client.app_id > 0
    assert app_client.app_address == get_application_address(app_client.app_id)
    assert isinstance(result.confirmation, dict)
    assert result.confirmation.get("application-index", 0) == app_client.app_id
    assert result.compiled_approval is not None
    assert result.compiled_clear is not None


def test_create_app_with_constructor_deploy_time_params(algorand: AlgorandClient, app_spec: str) -> None:
    """Test creating an app using the factory with constructor deploy time params"""
    random_account = algorand.account.random()
    dispenser_account = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        account_to_fund=random_account,
        dispenser_account=dispenser_account.address,
        min_spending_balance=AlgoAmount.from_algo(10),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    factory = algorand.client.get_app_factory(
        app_spec=app_spec,
        default_sender=random_account.address,
        compilation_params={
            "deploy_time_params": {
                # It should strip off the TMPL_
                "TMPL_UPDATABLE": 0,
                "DELETABLE": 0,
                "VALUE": 1,
            }
        },
    )

    app_client, result = factory.send.bare.create()

    assert result.app_id > 0
    assert app_client.app_id == result.app_id


def test_create_app_with_oncomplete_overload(factory: AppFactory) -> None:
    app_client, result = factory.send.bare.create(
        params=AppFactoryCreateParams(
            on_complete=OnComplete.OptInOC,
        ),
        compilation_params={
            "updatable": True,
            "deletable": True,
            "deploy_time_params": {
                "VALUE": 1,
            },
        },
    )

    assert result.transaction.application_call
    assert result.transaction.application_call.on_complete == OnComplete.OptInOC
    assert app_client.app_id > 0
    assert app_client.app_address == get_application_address(app_client.app_id)
    assert isinstance(result.confirmation, dict)
    assert result.confirmation.get("application-index", 0) == app_client.app_id


def test_deploy_when_immutable_and_permanent(factory: AppFactory) -> None:
    factory.deploy(
        on_schema_break=OnSchemaBreak.Fail,
        on_update=OnUpdate.Fail,
        compilation_params={
            "deletable": False,
            "updatable": False,
            "deploy_time_params": {
                "VALUE": 1,
            },
        },
    )


def test_deploy_app_create(factory: AppFactory) -> None:
    app_client, deploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {
                "VALUE": 1,
            },
        },
    )

    assert deploy_result.operation_performed == OperationPerformed.Create
    assert deploy_result.create_result
    assert deploy_result.create_result.app_id > 0
    assert app_client.app_id == deploy_result.create_result.app_id
    assert app_client.app_address == get_application_address(app_client.app_id)


def test_deploy_app_create_abi(factory: AppFactory) -> None:
    app_client, deploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {
                "VALUE": 1,
            },
        },
        create_params=AppClientMethodCallCreateParams(method="create_abi", args=["arg_io"]),
    )

    assert deploy_result.operation_performed == OperationPerformed.Create
    create_result = deploy_result.create_result
    assert create_result is not None
    assert deploy_result.app.app_id > 0
    app_index = create_result.confirmation["application-index"]  # type: ignore[call-overload]
    assert app_client.app_id == deploy_result.app.app_id == app_index
    assert app_client.app_address == get_application_address(app_client.app_id)


def test_deploy_app_update(factory: AppFactory) -> None:
    app_client, create_deploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {
                "VALUE": 1,
            },
            "updatable": True,
        },
    )
    assert create_deploy_result.operation_performed == OperationPerformed.Create
    assert create_deploy_result.create_result

    updated_app_client, update_deploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {
                "VALUE": 2,
            },
        },
        on_update=OnUpdate.UpdateApp,
    )
    assert update_deploy_result.operation_performed == OperationPerformed.Update
    assert update_deploy_result.update_result

    assert create_deploy_result.app.app_id == update_deploy_result.app.app_id
    assert create_deploy_result.app.app_address == update_deploy_result.app.app_address
    assert create_deploy_result.create_result.confirmation
    assert create_deploy_result.app.updatable
    assert create_deploy_result.app.updatable == update_deploy_result.app.updatable
    assert create_deploy_result.app.updated_round != update_deploy_result.app.updated_round
    assert create_deploy_result.app.created_round == update_deploy_result.app.created_round
    assert update_deploy_result.update_result.confirmation
    confirmed_round = update_deploy_result.update_result.confirmation["confirmed-round"]  # type: ignore[call-overload]
    assert update_deploy_result.app.updated_round == confirmed_round


def test_deploy_app_update_detects_extra_pages_as_breaking_change(
    algorand: AlgorandClient, funded_account: SigningAccount
) -> None:
    small_app_spec = (Path(__file__).parent.parent / "artifacts" / "extra_pages_test" / "small.arc56.json").read_text()
    large_app_spec = (Path(__file__).parent.parent / "artifacts" / "extra_pages_test" / "large.arc56.json").read_text()
    factory = algorand.client.get_app_factory(
        app_spec=small_app_spec,
        default_sender=funded_account.address,
    )
    small_client, create_deploy_result = factory.deploy(
        compilation_params={
            "updatable": True,
        },
    )
    assert create_deploy_result.operation_performed == OperationPerformed.Create
    assert create_deploy_result.create_result

    factory._app_spec = Arc56Contract.from_json(large_app_spec)  # noqa: SLF001
    large_client, update_deploy_result = factory.deploy(
        compilation_params={
            "updatable": True,
        },
        on_schema_break=OnSchemaBreak.AppendApp,
        on_update=OnUpdate.UpdateApp,
    )
    assert update_deploy_result.operation_performed == OperationPerformed.Create
    assert update_deploy_result.create_result

    assert small_client.app_id != large_client.app_id


def test_deploy_app_update_abi(factory: AppFactory) -> None:
    _, create_deploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {
                "VALUE": 1,
            },
            "updatable": True,
        },
    )
    assert create_deploy_result.operation_performed == OperationPerformed.Create
    assert create_deploy_result.create_result
    created_app = create_deploy_result.create_result

    _, update_deploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {
                "VALUE": 2,
            },
        },
        on_update=OnUpdate.UpdateApp,
        update_params=AppClientMethodCallParams(method="update_abi", args=["args_io"]),
    )

    assert update_deploy_result.operation_performed == OperationPerformed.Update
    assert update_deploy_result.update_result
    assert update_deploy_result.app.app_id == created_app.app_id
    assert update_deploy_result.app.app_address == created_app.app_address
    assert update_deploy_result.update_result.confirmation is not None
    assert update_deploy_result.app.created_round == create_deploy_result.app.created_round
    assert update_deploy_result.app.updated_round != update_deploy_result.app.created_round
    assert (
        update_deploy_result.app.updated_round == update_deploy_result.update_result.confirmation["confirmed-round"]  # type: ignore[call-overload]
    )
    assert update_deploy_result.update_result.transaction.application_call
    assert update_deploy_result.update_result.transaction.application_call.on_complete == OnComplete.UpdateApplicationOC
    assert update_deploy_result.update_result.abi_return == "args_io"


def test_deploy_app_replace(factory: AppFactory) -> None:
    _, create_deploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {
                "VALUE": 1,
            },
            "deletable": True,
        },
    )
    assert create_deploy_result.operation_performed == OperationPerformed.Create
    assert create_deploy_result.create_result

    _, replace_deploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {
                "VALUE": 2,
            },
        },
        on_update=OnUpdate.ReplaceApp,
    )

    assert replace_deploy_result.operation_performed == OperationPerformed.Replace
    assert replace_deploy_result.app.app_id > create_deploy_result.app.app_id
    assert replace_deploy_result.app.app_address == algosdk.logic.get_application_address(
        replace_deploy_result.app.app_id
    )
    assert replace_deploy_result.create_result is not None
    assert replace_deploy_result.delete_result is not None
    assert replace_deploy_result.delete_result.confirmation is not None
    assert (
        len(replace_deploy_result.create_result.transactions) + len(replace_deploy_result.delete_result.transactions)
        == 2
    )
    assert replace_deploy_result.delete_result.transaction.application_call
    assert replace_deploy_result.delete_result.transaction.application_call.index == create_deploy_result.app.app_id
    assert (
        replace_deploy_result.delete_result.transaction.application_call.on_complete == OnComplete.DeleteApplicationOC
    )


def test_deploy_app_replace_abi(factory: AppFactory) -> None:
    _, create_deploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {
                "VALUE": 1,
            },
            "deletable": True,
        },
        send_params={
            "populate_app_call_resources": False,
        },
    )

    replaced_app_client, replace_deploy_result = factory.deploy(
        compilation_params={
            "deploy_time_params": {
                "VALUE": 2,
            },
            "deletable": True,
        },
        on_update=OnUpdate.ReplaceApp,
        create_params=AppClientMethodCallCreateParams(method="create_abi", args=["arg_io"]),
        delete_params=AppClientMethodCallParams(method="delete_abi", args=["arg2_io"]),
    )

    assert replace_deploy_result.operation_performed == OperationPerformed.Replace
    assert replace_deploy_result.app.app_id > create_deploy_result.app.app_id
    assert replace_deploy_result.app.app_address == algosdk.logic.get_application_address(replaced_app_client.app_id)
    assert replace_deploy_result.create_result is not None
    assert replace_deploy_result.delete_result is not None
    assert replace_deploy_result.delete_result.confirmation is not None
    assert (
        len(replace_deploy_result.create_result.transactions) + len(replace_deploy_result.delete_result.transactions)
        == 2
    )
    assert replace_deploy_result.delete_result.transaction.application_call
    assert replace_deploy_result.delete_result.transaction.application_call.index == create_deploy_result.app.app_id
    assert (
        replace_deploy_result.delete_result.transaction.application_call.on_complete == OnComplete.DeleteApplicationOC
    )
    assert replace_deploy_result.create_result.abi_return == "arg_io"
    assert replace_deploy_result.delete_result.abi_return == "arg2_io"


def test_create_then_call_app(factory: AppFactory) -> None:
    app_client, _ = factory.send.bare.create(
        compilation_params={
            "updatable": True,
            "deletable": True,
            "deploy_time_params": {
                "VALUE": 1,
            },
        },
    )

    call = app_client.send.call(AppClientMethodCallParams(method="call_abi", args=["test"]))
    assert call.abi_return == "Hello, test"


def test_call_app_with_rekey(funded_account: SigningAccount, algorand: AlgorandClient, factory: AppFactory) -> None:
    rekey_to = algorand.account.random()

    app_client, _ = factory.send.bare.create(
        compilation_params={
            "updatable": True,
            "deletable": True,
            "deploy_time_params": {
                "VALUE": 1,
            },
        },
    )

    app_client.send.opt_in(AppClientMethodCallParams(method="opt_in", rekey_to=rekey_to.address))

    # If the rekey didn't work this will throw
    rekeyed_account = algorand.account.rekeyed(sender=funded_account.address, account=rekey_to)
    algorand.send.payment(
        PaymentParams(amount=AlgoAmount.from_algo(0), sender=rekeyed_account.address, receiver=funded_account.address)
    )


def test_create_app_with_abi(factory: AppFactory) -> None:
    _, call_return = factory.send.create(
        AppFactoryCreateMethodCallParams(
            method="create_abi",
            args=["string_io"],
        ),
        compilation_params={
            "deploy_time_params": {
                "UPDATABLE": 0,
                "DELETABLE": 0,
                "VALUE": 1,
            },
        },
    )

    assert call_return.abi_return
    assert call_return.abi_return == "string_io"


def test_update_app_with_abi(factory: AppFactory) -> None:
    deploy_time_params = {
        "UPDATABLE": 1,
        "DELETABLE": 0,
        "VALUE": 1,
    }
    app_client, _ = factory.send.bare.create(
        compilation_params={
            "deploy_time_params": deploy_time_params,
        },
    )

    call_return = app_client.send.update(
        AppClientMethodCallParams(
            method="update_abi",
            args=["string_io"],
        ),
        compilation_params={
            "deploy_time_params": deploy_time_params,
        },
    )

    assert call_return.abi_return == "string_io"
    # assert call_return.compiled_approval is not None # TODO: centralize approval/clear compilation


def test_delete_app_with_abi(factory: AppFactory) -> None:
    app_client, _ = factory.send.bare.create(
        compilation_params={
            "deploy_time_params": {
                "UPDATABLE": 0,
                "DELETABLE": 1,
                "VALUE": 1,
            },
        },
    )

    call_return = app_client.send.delete(
        AppClientMethodCallParams(
            method="delete_abi",
            args=["string_io"],
        )
    )

    assert call_return.abi_return == "string_io"


def test_export_import_sourcemaps(
    factory: AppFactory,
    algorand: AlgorandClient,
    funded_account: SigningAccount,
) -> None:
    # Export source maps from original client
    app_client, _ = factory.deploy(compilation_params={"deploy_time_params": {"VALUE": 1}})
    old_sourcemaps = app_client.export_source_maps()

    # Create new client instance
    new_client = AppClient(
        AppClientParams(
            app_id=app_client.app_id,
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            algorand=algorand,
            app_spec=app_client.app_spec,
        )
    )

    # Test error handling before importing source maps
    with pytest.raises(LogicError) as exc_info:
        new_client.send.call(AppClientMethodCallParams(method="error"))

    assert "assert failed" in exc_info.value.message

    # Import source maps into new client
    new_client.import_source_maps(old_sourcemaps)

    # Test error handling after importing source maps
    with pytest.raises(LogicError) as exc_info:
        new_client.send.call(AppClientMethodCallParams(method="error"))

    error = exc_info.value
    assert (
        error.trace().strip()
        == "// error\n\terror_7:\n\tproto 0 0\n\tintc_0 // 0\n\t// Deliberate error\n\tassert\t\t<-- Error\n\tretsub\n\t\n\t// create\n\tcreate_8:"  # noqa: E501
    )
    assert error.pc == 885
    assert error.message == "assert failed pc=885"
    assert len(error.transaction_id) == 52


def test_arc56_error_messages_with_dynamic_template_vars_cblock_offset(
    arc56_factory: AppFactory,
) -> None:
    app_client, _ = arc56_factory.deploy(
        create_params=AppClientMethodCallCreateParams(method="createApplication"),
        compilation_params={
            "deploy_time_params": {
                "bytes64TmplVar": "0" * 64,
                "uint64TmplVar": 123,
                "bytes32TmplVar": "0" * 32,
                "bytesTmplVar": "foo",
            },
        },
    )

    with pytest.raises(Exception, match="this is an error"):
        app_client.send.call(AppClientMethodCallParams(method="throwError"))


def test_arc56_undefined_error_message_with_dynamic_template_vars_cblock_offset(
    arc56_factory: AppFactory,
    algorand: AlgorandClient,
    funded_account: SigningAccount,
) -> None:
    # Deploy app with template parameters
    app_client, _ = arc56_factory.deploy(
        create_params=AppClientMethodCallCreateParams(method="createApplication"),
        compilation_params={
            "deploy_time_params": {
                "bytes64TmplVar": "0" * 64,
                "uint64TmplVar": 0,
                "bytes32TmplVar": "0" * 32,
                "bytesTmplVar": "foo",
            },
        },
    )
    app_id = app_client.app_id

    # Create new client without source map from compilation
    app_client = AppClient(
        AppClientParams(
            app_id=app_id,
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            algorand=algorand,
            app_spec=app_client.app_spec,
        )
    )

    # Test error handling
    with pytest.raises(LogicError) as exc_info:
        app_client.send.call(AppClientMethodCallParams(method="tmpl"))

    assert (
        exc_info.value.trace().strip()
        == "// tests/example-contracts/arc56_templates/templates.algo.ts:14\n\t\t// assert(this.uint64TmplVar)\n\t\tintc 1 // TMPL_uint64TmplVar\n\t\tassert\n\t\tretsub\t\t<-- Error\n\t\n\t// specificLengthTemplateVar()void\n\t*abi_route_specificLengthTemplateVar:\n\t\t// execute specificLengthTemplateVar()void"  # noqa: E501
    )
