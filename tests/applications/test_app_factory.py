from pathlib import Path

import algosdk
import pytest
from algosdk.logic import get_application_address
from algosdk.transaction import ApplicationCallTxn, ApplicationCreateTxn, OnComplete

from algokit_utils import OnSchemaBreak, OnUpdate, OperationPerformed
from algokit_utils.applications.app_client import (
    AppClient,
    AppClientMethodCallParams,
    AppClientMethodCallWithCompilationAndSendParams,
    AppClientMethodCallWithSendParams,
    AppClientParams,
)
from algokit_utils.applications.app_factory import (
    AppFactory,
    AppFactoryCreateMethodCallParams,
    AppFactoryCreateWithSendParams,
)
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.errors.logic_error import LogicError
from algokit_utils.models.account import Account
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import PaymentParams


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_local_net()


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> Account:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account, dispenser, AlgoAmount.from_algos(100), min_funding_increment=AlgoAmount.from_algos(1)
    )
    algorand.set_signer(sender=new_account.address, signer=new_account.signer)
    return new_account


@pytest.fixture
def app_spec() -> str:
    return (Path(__file__).parent.parent / "artifacts" / "testing_app" / "arc32_app_spec.json").read_text()


@pytest.fixture
def factory(algorand: AlgorandClient, funded_account: Account, app_spec: str) -> AppFactory:
    """Create AppFactory fixture"""
    return algorand.client.get_app_factory(app_spec=app_spec, default_sender=funded_account.address)


@pytest.fixture
def arc56_factory(
    algorand: AlgorandClient,
    funded_account: Account,
) -> AppFactory:
    """Create AppFactory fixture"""
    arc56_raw_spec = (
        Path(__file__).parent.parent / "artifacts" / "testing_app_arc56" / "arc56_app_spec.json"
    ).read_text()
    return algorand.client.get_app_factory(app_spec=arc56_raw_spec, default_sender=funded_account.address)


def test_create_app(factory: AppFactory) -> None:
    """Test creating an app using the factory"""
    app_client, result = factory.send.bare.create(
        params=AppFactoryCreateWithSendParams(
            deploy_time_params={
                # It should strip off the TMPL_
                "TMPL_UPDATABLE": 0,
                "DELETABLE": 0,
                "VALUE": 1,
            }
        )
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
        account_fo_fund=random_account,
        dispenser_account=dispenser_account.address,
        min_spending_balance=AlgoAmount.from_algo(10),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    factory = algorand.client.get_app_factory(
        app_spec=app_spec,
        default_sender=random_account.address,
        deploy_time_params={
            # It should strip off the TMPL_
            "TMPL_UPDATABLE": 0,
            "DELETABLE": 0,
            "VALUE": 1,
        },
    )

    app_client, result = factory.send.bare.create()

    assert result.app_id > 0
    assert app_client.app_id == result.app_id


def test_create_app_with_oncomplete_overload(factory: AppFactory) -> None:
    app_client, result = factory.send.bare.create(
        params=AppFactoryCreateWithSendParams(
            on_complete=OnComplete.OptInOC,
            updatable=True,
            deletable=True,
            deploy_time_params={
                "VALUE": 1,
            },
        )
    )

    assert isinstance(result.transaction, ApplicationCreateTxn)
    assert result.transaction.on_complete == OnComplete.OptInOC
    assert app_client.app_id > 0
    assert app_client.app_address == get_application_address(app_client.app_id)
    assert isinstance(result.confirmation, dict)
    assert result.confirmation.get("application-index", 0) == app_client.app_id


def test_deploy_when_immutable_and_permanent(factory: AppFactory) -> None:
    factory.deploy(
        deletable=False,
        updatable=False,
        on_schema_break=OnSchemaBreak.Fail,
        on_update=OnUpdate.Fail,
        deploy_time_params={
            "VALUE": 1,
        },
    )


def test_deploy_app_create(factory: AppFactory) -> None:
    app_client, result = factory.deploy(
        deploy_time_params={
            "VALUE": 1,
        },
    )

    assert result.operation_performed == OperationPerformed.Create
    assert result.app_id > 0
    assert app_client.app_id == result.app_id == result.confirmation["application-index"]  # type: ignore[call-overload]
    assert app_client.app_address == get_application_address(app_client.app_id)


def test_deploy_app_create_abi(factory: AppFactory) -> None:
    app_client, result = factory.deploy(
        deploy_time_params={
            "VALUE": 1,
        },
        create_params=AppClientMethodCallParams(method="create_abi", args=["arg_io"]),
    )

    assert result.operation_performed == OperationPerformed.Create
    assert result.app_id > 0
    assert app_client.app_id == result.app_id == result.confirmation["application-index"]  # type: ignore[call-overload]
    assert app_client.app_address == get_application_address(app_client.app_id)


def test_deploy_app_update(factory: AppFactory) -> None:
    _, created_app = factory.deploy(
        deploy_time_params={
            "VALUE": 1,
        },
        updatable=True,
    )

    _, updated_app = factory.deploy(
        deploy_time_params={
            "VALUE": 2,
        },
        on_update=OnUpdate.UpdateApp,
    )

    assert updated_app.operation_performed == OperationPerformed.Update
    assert created_app.app_id == updated_app.app_id
    assert created_app.app_address == updated_app.app_address
    assert created_app.confirmation
    assert created_app.updatable
    assert created_app.updatable == updated_app.updatable
    assert created_app.updated_round != updated_app.updated_round
    assert created_app.created_round == updated_app.created_round
    assert updated_app.updated_round == updated_app.confirmation["confirmed-round"]  # type: ignore[call-overload]


def test_deploy_app_update_abi(factory: AppFactory) -> None:
    _, created_app = factory.deploy(
        deploy_time_params={
            "VALUE": 1,
        },
        updatable=True,
    )

    _, updated_app = factory.deploy(
        deploy_time_params={
            "VALUE": 2,
        },
        on_update=OnUpdate.UpdateApp,
        update_params=AppClientMethodCallParams(method="update_abi", args=["args_io"]),
    )

    assert updated_app.operation_performed == OperationPerformed.Update
    assert updated_app.app_id == created_app.app_id
    assert updated_app.app_address == created_app.app_address
    assert updated_app.confirmation is not None
    assert updated_app.created_round == created_app.created_round
    assert updated_app.updated_round != updated_app.created_round
    assert updated_app.updated_round == updated_app.confirmation["confirmed-round"]  # type: ignore[call-overload]
    assert isinstance(updated_app.transaction, ApplicationCallTxn)
    assert updated_app.transaction.on_complete == OnComplete.UpdateApplicationOC  # type: ignore[union-attr]
    assert updated_app.return_value == "args_io"


def test_deploy_app_replace(factory: AppFactory) -> None:
    _, created_app = factory.deploy(
        deploy_time_params={
            "VALUE": 1,
        },
        deletable=True,
    )

    _, replaced_app = factory.deploy(
        deploy_time_params={
            "VALUE": 2,
        },
        on_update=OnUpdate.ReplaceApp,
    )

    assert replaced_app.operation_performed == OperationPerformed.Replace
    assert replaced_app.app_id > created_app.app_id
    assert replaced_app.app_address == algosdk.logic.get_application_address(replaced_app.app_id)
    assert replaced_app.confirmation is not None
    assert replaced_app.delete_result is not None
    assert replaced_app.delete_result.confirmation is not None
    assert len(replaced_app.transactions) == 2  # noqa: PLR2004
    assert isinstance(replaced_app.delete_result.transaction, ApplicationCallTxn)
    assert replaced_app.delete_result.transaction.index == created_app.app_id  # type: ignore[union-attr]
    assert replaced_app.delete_result.transaction.on_complete == OnComplete.DeleteApplicationOC  # type: ignore[union-attr]


def test_deploy_app_replace_abi(factory: AppFactory) -> None:
    _, created_app = factory.deploy(
        deploy_time_params={
            "VALUE": 1,
        },
        deletable=True,
        populate_app_call_resources=False,
    )

    _, replaced_app = factory.deploy(
        deploy_time_params={
            "VALUE": 2,
        },
        on_update=OnUpdate.ReplaceApp,
        create_params=AppClientMethodCallParams(method="create_abi", args=["arg_io"]),
        delete_params=AppClientMethodCallParams(method="delete_abi", args=["arg2_io"]),
    )

    assert replaced_app.operation_performed == OperationPerformed.Replace
    assert replaced_app.app_id > created_app.app_id
    assert replaced_app.app_address == algosdk.logic.get_application_address(replaced_app.app_id)
    assert replaced_app.confirmation is not None
    assert replaced_app.delete_result is not None
    assert replaced_app.delete_result.confirmation is not None
    assert len(replaced_app.transactions) == 2
    assert isinstance(replaced_app.delete_result.transaction, ApplicationCallTxn)
    assert replaced_app.delete_result.transaction.index == created_app.app_id  # type: ignore[union-attr]
    assert replaced_app.delete_result.transaction.on_complete == OnComplete.DeleteApplicationOC  # type: ignore[union-attr]
    assert replaced_app.return_value == "arg_io"
    assert replaced_app.delete_return_value == "arg2_io"


def test_create_then_call_app(factory: AppFactory) -> None:
    app_client, _ = factory.send.bare.create(
        AppFactoryCreateWithSendParams(
            deploy_time_params={
                "UPDATABLE": 1,
                "DELETABLE": 1,
                "VALUE": 1,
            },
        )
    )

    call = app_client.send.call(AppClientMethodCallWithSendParams(method="call_abi", args=["test"]))

    assert call.return_value
    assert call.return_value.return_value == "Hello, test"


def test_call_app_with_rekey(funded_account: Account, algorand: AlgorandClient, factory: AppFactory) -> None:
    rekey_to = algorand.account.random()

    app_client, _ = factory.send.bare.create(
        AppFactoryCreateWithSendParams(
            deploy_time_params={
                "UPDATABLE": 1,
                "DELETABLE": 1,
                "VALUE": 1,
            },
        )
    )

    app_client.send.opt_in(AppClientMethodCallWithSendParams(method="opt_in", rekey_to=rekey_to.address))

    # If the rekey didn't work this will throw
    rekeyed_account = algorand.account.rekeyed(funded_account.address, rekey_to)
    algorand.send.payment(
        PaymentParams(amount=AlgoAmount.from_algo(0), sender=rekeyed_account.address, receiver=funded_account.address)
    )


def test_create_app_with_abi(factory: AppFactory) -> None:
    _, call_return = factory.send.create(
        AppFactoryCreateMethodCallParams(
            method="create_abi",
            args=["string_io"],
            deploy_time_params={
                "UPDATABLE": 0,
                "DELETABLE": 0,
                "VALUE": 1,
            },
        )
    )

    assert call_return.return_value
    # Fix return value issues
    assert call_return.return_value.return_value == "string_io"


def test_update_app_with_abi(factory: AppFactory) -> None:
    deploy_time_params = {
        "UPDATABLE": 1,
        "DELETABLE": 0,
        "VALUE": 1,
    }
    app_client, _ = factory.send.bare.create(
        AppFactoryCreateWithSendParams(
            deploy_time_params=deploy_time_params,
        )
    )

    call_return = app_client.send.update(
        AppClientMethodCallWithCompilationAndSendParams(
            method="update_abi",
            args=["string_io"],
            deploy_time_params=deploy_time_params,
        )
    )

    assert call_return.return_value is not None
    assert call_return.return_value.return_value == "string_io"
    # TODO: fix this
    # assert call_return.compiled_approval is not None


def test_delete_app_with_abi(factory: AppFactory) -> None:
    app_client, _ = factory.send.bare.create(
        AppFactoryCreateWithSendParams(
            deploy_time_params={
                "UPDATABLE": 0,
                "DELETABLE": 1,
                "VALUE": 1,
            },
        )
    )

    call_return = app_client.send.delete(
        AppClientMethodCallWithSendParams(
            method="delete_abi",
            args=["string_io"],
        )
    )

    assert call_return.return_value is not None
    assert call_return.return_value.return_value == "string_io"


def test_export_import_sourcemaps(
    factory: AppFactory,
    algorand: AlgorandClient,
    funded_account: Account,
) -> None:
    # Export source maps from original client
    client, app = factory.deploy(deploy_time_params={"VALUE": 1})
    old_sourcemaps = client.export_source_maps()

    # Create new client instance
    new_client = AppClient(
        AppClientParams(
            app_id=app.app_id,
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            algorand=algorand,
            app_spec=client.app_spec,
        )
    )

    # Test error handling before importing source maps
    with pytest.raises(LogicError) as exc_info:
        new_client.send.call(AppClientMethodCallWithSendParams(method="error"))

    assert "assert failed" in exc_info.value.message

    # Import source maps into new client
    new_client.import_source_maps(old_sourcemaps)

    # Test error handling after importing source maps
    with pytest.raises(LogicError) as exc_info:
        new_client.send.call(AppClientMethodCallWithSendParams(method="error"))

    error = exc_info.value
    assert error.stack == (
        "// error\n"
        "error_7:\n"
        "proto 0 0\n"
        "intc_0 // 0\n"
        "// Deliberate error\n"
        "assert <--- Error\n"
        "retsub\n\n"
        "// create\n"
        "create_8:"
    )
    assert error.pc == 885
    assert error.message == "assert failed pc=885"
    assert len(error.transaction_id) == 52


def test_arc56_error_messages_with_dynamic_template_vars_cblock_offset(
    arc56_factory: AppFactory,
) -> None:
    client, _ = arc56_factory.deploy(
        create_params=AppClientMethodCallParams(method="createApplication"),
        deploy_time_params={
            "bytes64TmplVar": "0" * 64,
            "uint64TmplVar": 123,
            "bytes32TmplVar": "0" * 32,
            "bytesTmplVar": "foo",
        },
    )

    with pytest.raises(LogicError) as exc_info:
        client.send.call(AppClientMethodCallWithSendParams(method="throwError"))

    assert "this is an error" in exc_info.value.stack


def test_arc56_undefined_error_message_with_dynamic_template_vars_cblock_offset(
    arc56_factory: AppFactory,
    algorand: AlgorandClient,
    funded_account: Account,
) -> None:
    # Deploy app with template parameters
    client, result = arc56_factory.deploy(
        create_params=AppClientMethodCallParams(method="createApplication"),
        deploy_time_params={
            "bytes64TmplVar": "0" * 64,
            "uint64TmplVar": 0,
            "bytes32TmplVar": "0" * 32,
            "bytesTmplVar": "foo",
        },
    )
    app_id = result.app_id

    # Create new client without source map from compilation
    app_client = AppClient(
        AppClientParams(
            app_id=app_id,
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            algorand=algorand,
            app_spec=client.app_spec,
        )
    )

    # Test error handling
    with pytest.raises(LogicError) as exc_info:
        app_client.send.call(AppClientMethodCallWithSendParams(method="tmpl"))

    expected_error = """log

// tests/example-contracts/arc56_templates/templates.algo.ts:14
// assert(this.uint64TmplVar)
intc 1 // TMPL_uint64TmplVar
assert <--- Error
retsub

// specificLengthTemplateVar()void
*abi_route_specificLengthTemplateVar:""".splitlines()

    assert expected_error == [t.strip() for t in exc_info.value.stack.splitlines()]
