import logging
import re
from enum import Enum
from pathlib import Path
from uuid import uuid4

import pytest
from algokit_utils.account import get_account, get_sandbox_default_account
from algokit_utils.app import (
    DELETABLE_TEMPLATE_NAME,
    UPDATABLE_TEMPLATE_NAME,
    App,
    DeploymentFailedError,
    OnSchemaBreak,
    OnUpdate,
    deploy_app,
    replace_template_variables,
)
from algokit_utils.application_specification import ApplicationSpecification
from algokit_utils.logic_error import LogicException
from algokit_utils.network_clients import get_algod_client, get_indexer_client

from tests.conftest import check_output_stability

logger = logging.getLogger(__name__)


class DeployFixture:
    def __init__(self, caplog: pytest.LogCaptureFixture, request: pytest.FixtureRequest):
        self.app_ids = []
        self.caplog = caplog
        self.request = request
        self.algod_client = get_algod_client()
        self.indexer = get_indexer_client()
        self.creator_name = _get_unique_name()
        self.creator = get_account(self.algod_client, self.creator_name)

    def deploy(
        self,
        app_spec: ApplicationSpecification,
        version: str,
        *,
        on_update: OnUpdate = OnUpdate.UpdateApp,
        on_schema_break: OnSchemaBreak = OnSchemaBreak.Fail,
        allow_delete: bool | None = None,
        allow_update: bool | None = None,
    ) -> App:
        app = deploy_app(
            self.algod_client,
            self.indexer,
            app_spec,
            self.creator,
            version=version,
            on_update=on_update,
            on_schema_break=on_schema_break,
            allow_update=allow_update,
            allow_delete=allow_delete,
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
        logs = re.sub(r"app id \d+", r"{appN_failed}", logs)
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


def _read_spec(path: str, *, updatable: bool | None = None, deletable: bool | None = None) -> ApplicationSpecification:
    spec = ApplicationSpecification.from_json(Path(path).read_text(encoding="utf-8"))

    template_variables = {}
    if updatable is not None:
        template_variables[UPDATABLE_TEMPLATE_NAME] = int(updatable)

    if deletable is not None:
        template_variables[DELETABLE_TEMPLATE_NAME] = int(deletable)

    spec.approval_program = (
        replace_template_variables(spec.approval_program, template_variables)
        .replace(f"// {UPDATABLE_TEMPLATE_NAME}", "// updatable")
        .replace(f"// {DELETABLE_TEMPLATE_NAME}", "// deletable")
    )
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


def _get_unique_name() -> str:
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

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.id

    app_v2 = deploy_fixture.deploy(v2, version="2.0")

    assert app_v1.id == app_v2.id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_immutable_app_fails(deploy_fixture: DeployFixture):
    v1, v2, _ = get_specs(updatable=False)

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.id

    with pytest.raises(LogicException) as error:
        deploy_fixture.deploy(v2, version="2.0")
    logger.error(f"LogicException: {error.value.message}")

    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_immutable_app_and_on_update_equals_delete_app_succeeds(
    deploy_fixture: DeployFixture,
):
    v1, v2, _ = get_specs(updatable=False, deletable=True)

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.id

    app_v2 = deploy_fixture.deploy(v2, version="2.0", on_update=OnUpdate.DeleteApp)

    assert app_v1.id != app_v2.id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_deletable_app_succeeds(deploy_fixture: DeployFixture):
    v1, v2, _ = get_specs(deletable=True)

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.id

    app_v2 = deploy_fixture.deploy(v2, version="2.0", on_update=OnUpdate.DeleteApp)
    assert app_v1.id != app_v2.id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_permanent_app_fails(deploy_fixture: DeployFixture):
    v1, _, v3 = get_specs(deletable=False)

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.id

    with pytest.raises(DeploymentFailedError) as error:
        deploy_fixture.deploy(v3, version="3.0")
    logger.error(f"DeploymentFailedError: {error.value}")
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_permanent_app_and_on_schema_break_equals_delete_app_fails(
    deploy_fixture: DeployFixture,
):
    v1, _, v3 = get_specs(deletable=False)

    app_v1 = deploy_fixture.deploy(v1, "1.0")
    assert app_v1.id

    with pytest.raises(LogicException) as exc_info:
        deploy_fixture.deploy(v3, "3.0", on_schema_break=OnSchemaBreak.DeleteApp)

    logger.error(f"Deployment failed: {exc_info.value.message}")

    deploy_fixture.check_log_stability()


def test_deploy_templated_app_with_changing_parameters_succeeds(deploy_fixture: DeployFixture):
    app_spec = _read_spec("app_v1.json")

    logger.info("Deploy V1 as updatable, deletable")
    deploy_fixture.deploy(
        app_spec,
        version="1",
        allow_delete=True,
        allow_update=True,
    )

    logger.info("Deploy V2 as immutable, deletable")
    deploy_fixture.deploy(
        app_spec,
        version="2",
        allow_delete=True,
        allow_update=False,
    )

    logger.info("Attempt to deploy V3 as updatable, deletable, it will fail because V2 was immutable")
    with pytest.raises(LogicException) as exc_info:
        # try to make it updatable again
        deploy_fixture.deploy(
            app_spec,
            version="3",
            allow_delete=True,
            allow_update=True,
        )

    logger.error(f"LogicException: {exc_info.value.message}")

    logger.info("2nd Attempt to deploy V3 as updatable, deletable, it will succeed as on_update=OnUpdate.DeleteApp")
    # deploy with delete_app_on_update=True so we can replace it
    deploy_fixture.deploy(
        app_spec,
        version="4",
        on_update=OnUpdate.DeleteApp,
        allow_delete=True,
        allow_update=True,
    )

    deploy_fixture.check_log_stability()


class Deletable(Enum):
    No = 0
    Yes = 1


class Updatable(Enum):
    No = 0
    Yes = 1


@pytest.mark.parametrize("deletable", [Deletable.No, Deletable.Yes])
@pytest.mark.parametrize("updatable", [Updatable.No, Updatable.Yes])
@pytest.mark.parametrize("on_schema_break", [OnSchemaBreak.Fail, OnSchemaBreak.DeleteApp])
def test_deploy_with_schema_breaking_change(
    deploy_fixture: DeployFixture,
    *,
    deletable: Deletable,
    updatable: Updatable,
    on_schema_break: OnSchemaBreak,
):
    v1 = _read_spec("app_v1.json")
    v3 = _read_spec("app_v3.json")

    app_v1 = deploy_fixture.deploy(
        v1, "1.0", allow_delete=deletable == deletable.Yes, allow_update=updatable == updatable.Yes
    )
    assert app_v1.id

    try:
        deploy_fixture.deploy(
            v3,
            "3.0",
            allow_delete=deletable == deletable.Yes,
            allow_update=updatable == updatable.Yes,
            on_schema_break=on_schema_break,
        )
    except DeploymentFailedError as error:
        logger.error(f"DeploymentFailedError: {error}")
    except LogicException as error:
        logger.error(f"LogicException: {error.message}")

    deploy_fixture.check_log_stability()


@pytest.mark.parametrize("deletable", [Deletable.No, Deletable.Yes])
@pytest.mark.parametrize("updatable", [Updatable.No, Updatable.Yes])
@pytest.mark.parametrize("on_update", [OnUpdate.Fail, OnUpdate.UpdateApp, OnUpdate.DeleteApp])
def test_deploy_with_update(
    deploy_fixture: DeployFixture,
    *,
    deletable: Deletable,
    updatable: Updatable,
    on_update: OnUpdate,
):
    v1 = _read_spec("app_v1.json")
    v2 = _read_spec("app_v2.json")

    app_v1 = deploy_fixture.deploy(
        v1, "1.0", allow_delete=deletable == deletable.Yes, allow_update=updatable == updatable.Yes
    )
    assert app_v1.id

    try:
        deploy_fixture.deploy(
            v2,
            "2.0",
            allow_delete=deletable == deletable.Yes,
            allow_update=updatable == updatable.Yes,
            on_update=on_update,
        )
    except DeploymentFailedError as error:
        logger.error(f"DeploymentFailedError: {error}")
    except LogicException as error:
        logger.error(f"LogicException: {error.message}")

    deploy_fixture.check_log_stability()


def test_template_substitution():
    program = """
test TMPL_INT // TMPL_INT
test TMPL_INT
no change
test TMPL_STR // TMPL_STR
TMPL_STR
TMPL_STR // TMPL_INT
TMPL_STR // foo //
TMPL_STR // bar
"""
    result = replace_template_variables(program, {"TMPL_INT": 123, "TMPL_STR": "ABC"})
    check_output_stability(result)
