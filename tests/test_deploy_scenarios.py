import logging
from enum import Enum
from pathlib import Path
from uuid import uuid4

import pytest
from algokit_utils.account import get_account, get_sandbox_default_account
from algokit_utils.app import App, DeploymentFailedError, deploy_app
from algokit_utils.application_specification import ApplicationSpecification
from algokit_utils.network_clients import get_algod_client, get_indexer_client
from pyteal import CallConfig, MethodConfig

from tests.conftest import check_output_stability

logger = logging.getLogger(__name__)


class DeployFixture:
    def __init__(self, caplog: pytest.LogCaptureFixture, request: pytest.FixtureRequest):
        self.app_ids = []
        self.caplog = caplog
        self.request = request
        self.algod_client = get_algod_client()
        self.indexer = get_indexer_client()
        self.creator_name = get_unique_name()
        self.creator = get_account(self.algod_client, self.creator_name)

    def deploy(
        self,
        app_spec: ApplicationSpecification,
        version: str,
        *,
        delete_app_on_update_if_exists: bool = False,
        delete_app_on_schema_break: bool = False,
    ) -> App:
        app = deploy_app(
            self.algod_client,
            self.indexer,
            app_spec,
            self.creator,
            version=version,
            delete_app_on_update_if_exists=delete_app_on_update_if_exists,
            delete_app_on_schema_break=delete_app_on_schema_break,
        )
        self._wait_for_round(app.created_at_round)
        self.app_ids.append(app.id)
        return app

    def check_log_stability(self, suffix: str = ""):
        records = self.caplog.get_records("call")
        logs = "\n".join(f"{r.levelname}: {r.message}" for r in records)
        logs = self._normalize_logs(logs)
        check_output_stability(logs, test_name=self.request.node.name + suffix)

    def _normalize_logs(self, logs: str) -> str:
        dispenser = get_sandbox_default_account(self.algod_client)
        logs = logs.replace(self.creator_name, "{creator}")
        logs = logs.replace(self.creator.address, "{creator_account}")
        logs = logs.replace(dispenser.address, "{dispenser_account}")
        for index, app_id in enumerate(self.app_ids):
            logs = logs.replace(f"app id {app_id}", f"app id {{app{index}}}")
        return logs

    def _wait_for_round(self, round_target: int, max_attempts: int = 100) -> None:
        for _attempts in range(max_attempts):
            health = self.indexer.health()
            if health["round"] >= round_target:
                break


@pytest.fixture
def deploy_fixture(caplog: pytest.LogCaptureFixture, request: pytest.FixtureRequest) -> DeployFixture:
    caplog.set_level(logging.DEBUG)
    return DeployFixture(caplog, request)


def _read_spec(path: str, *, updatable: bool = False, deletable: bool = False) -> ApplicationSpecification:
    spec = ApplicationSpecification.from_json(Path(path).read_text(encoding="utf-8"))
    # patch spec to simulate updatable, deletable
    if not updatable:
        kwargs = dict(spec.bare_call_config.__dict__)
        kwargs["update_application"] = CallConfig.NEVER
        spec.bare_call_config = MethodConfig(**kwargs)
    if not deletable:
        kwargs = dict(spec.bare_call_config.__dict__)
        kwargs["delete_application"] = CallConfig.NEVER
        spec.bare_call_config = MethodConfig(**kwargs)
    return spec


def get_specs(
    *, updatable: bool = False, deletable: bool = False
) -> tuple[ApplicationSpecification, ApplicationSpecification, ApplicationSpecification]:
    specs = (
        _read_spec("app_v1.json", updatable=updatable, deletable=deletable),
        _read_spec("app_v2.json", updatable=updatable, deletable=deletable),
        _read_spec("app_v3.json", updatable=updatable, deletable=deletable),
    )
    return specs


def get_unique_name() -> str:
    name = str(uuid4()).replace("-", "")
    assert name.isalnum()
    return name


def test_deploy_app_with_no_existing_app_succeeds(deploy_fixture: DeployFixture):
    v1, _, _ = get_specs()

    app = deploy_fixture.deploy(v1, version="1.0")

    assert app.id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_updatable_app_succeeds(deploy_fixture: DeployFixture):
    v1, v2, _ = get_specs(updatable=True)
    assert v1.updatable

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.id

    app_v2 = deploy_fixture.deploy(v2, version="2.0")

    assert app_v1.id == app_v2.id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_immutable_app_fails(deploy_fixture: DeployFixture):
    v1, v2, _ = get_specs(updatable=False)
    assert not v1.updatable

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.id

    with pytest.raises(DeploymentFailedError):
        deploy_fixture.deploy(v2, version="2.0")
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_immutable_app_and_delete_app_on_update_equals_true_succeeds(
    deploy_fixture: DeployFixture,
):
    v1, v2, _ = get_specs(updatable=False)
    assert not v1.updatable

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.id

    app_v2 = deploy_fixture.deploy(v2, version="2.0", delete_app_on_update_if_exists=True)

    assert app_v1.id != app_v2.id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_deletable_app_succeeds(deploy_fixture: DeployFixture):
    v1, _, v3 = get_specs(deletable=True)
    assert v1.deletable

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.id

    app_v3 = deploy_fixture.deploy(v3, version="3.0")
    assert app_v1.id != app_v3.id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_permanent_app_fails(deploy_fixture: DeployFixture):
    v1, _, v3 = get_specs(deletable=False)
    assert not v1.deletable

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.id

    with pytest.raises(DeploymentFailedError):
        deploy_fixture.deploy(v3, version="3.0")
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_permanent_app_and_delete_app_on_schema_break_equal_true_succeeds(
    deploy_fixture: DeployFixture,
):
    v1, _, v3 = get_specs(deletable=False)
    assert not v1.deletable

    app_v1 = deploy_fixture.deploy(v1, "1.0")
    assert app_v1.id

    app_v3 = deploy_fixture.deploy(v3, "3.0", delete_app_on_schema_break=True)
    assert app_v1.id != app_v3.id
    deploy_fixture.check_log_stability()


class Deletable(Enum):
    No = 0
    Yes = 1


class Updatable(Enum):
    No = 0
    Yes = 1


class DeleteSchemaBreak(Enum):
    Disabled = 0
    Enabled = 1


@pytest.mark.parametrize("deletable", [Deletable.No, Deletable.Yes])
@pytest.mark.parametrize("updatable", [Updatable.No, Updatable.Yes])
@pytest.mark.parametrize("delete_on_schema_break", [DeleteSchemaBreak.Disabled, DeleteSchemaBreak.Enabled])
def test_deploy_with_schema_breaking_change(
    deploy_fixture: DeployFixture,
    *,
    deletable: Deletable,
    updatable: Updatable,
    delete_on_schema_break: DeleteSchemaBreak,
):
    v1, _, v3 = get_specs(deletable=deletable == Deletable.Yes, updatable=updatable == Updatable.Yes)

    app_v1 = deploy_fixture.deploy(v1, "1.0")
    assert app_v1.id

    try:
        deploy_fixture.deploy(
            v3,
            "3.0",
            delete_app_on_schema_break=delete_on_schema_break == DeleteSchemaBreak.Enabled,
        )
    except DeploymentFailedError as error:
        logger.info(f"DeploymentFailedError: {error}")
    deploy_fixture.check_log_stability()


class DeleteAppUpdate(Enum):
    Disabled = 0
    Enabled = 1


@pytest.mark.parametrize("deletable", [Deletable.No, Deletable.Yes])
@pytest.mark.parametrize("updatable", [Updatable.No, Updatable.Yes])
@pytest.mark.parametrize("delete_on_app_update", [DeleteAppUpdate.Disabled, DeleteAppUpdate.Enabled])
def test_deploy_with_update(
    deploy_fixture: DeployFixture,
    *,
    deletable: Deletable,
    updatable: Updatable,
    delete_on_app_update: DeleteAppUpdate,
):
    v1, v2, _ = get_specs(deletable=deletable == Deletable.Yes, updatable=updatable == Updatable.Yes)

    app_v1 = deploy_fixture.deploy(v1, "1.0")
    assert app_v1.id

    try:
        deploy_fixture.deploy(
            v2,
            "2.0",
            delete_app_on_update_if_exists=delete_on_app_update == DeleteAppUpdate.Enabled,
        )
    except DeploymentFailedError as error:
        logger.info(f"DeploymentFailedError: {error}")
    deploy_fixture.check_log_stability()
