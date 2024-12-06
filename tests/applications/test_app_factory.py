from pathlib import Path

import algosdk
import pytest
from algosdk.logic import get_application_address
from algosdk.transaction import ApplicationCallTxn, ApplicationCreateTxn, OnComplete

from algokit_utils._legacy_v2.deploy import OnSchemaBreak, OnUpdate, OperationPerformed
from algokit_utils.applications.app_client import AppClientMethodCallParams
from algokit_utils.applications.app_factory import AppFactory, AppFactoryCreateWithSendParams
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.models.account import Account
from algokit_utils.models.amount import AlgoAmount


@pytest.fixture
def algorand(funded_account: Account) -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_signer(sender=funded_account.address, signer=funded_account.signer)
    return client


@pytest.fixture
def app_spec() -> str:
    return (Path(__file__).parent.parent / "artifacts" / "testing_app" / "arc32_app_spec.json").read_text()


@pytest.fixture
def factory(algorand: AlgorandClient, funded_account: Account, app_spec: str) -> AppFactory:
    """Create AppFactory fixture"""
    return algorand.client.get_app_factory(app_spec=app_spec, default_sender=funded_account.address)


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
    assert replaced_app.delete_return is not None
    assert replaced_app.delete_return.confirmation is not None
    assert replaced_app.delete_return.transaction.application_id == created_app.app_id  # type: ignore[union-attr]
    assert replaced_app.delete_return.transaction.on_complete == OnComplete.DeleteApplicationOC  # type: ignore[union-attr]
