from pathlib import Path

import pytest
from algosdk.logic import get_application_address
from algosdk.transaction import ApplicationCreateTxn, OnComplete

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
        account_fo_fund=random_account.address,
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
