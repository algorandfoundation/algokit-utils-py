import logging
import re
from enum import Enum

import pytest
from algokit_utils.account import get_account, get_sandbox_default_account
from algokit_utils.app import (
    DeploymentFailedError,
    replace_template_variables,
)
from algokit_utils.application_client import ApplicationClient, OnSchemaBreak, OnUpdate, get_next_version
from algokit_utils.application_specification import ApplicationSpecification
from algokit_utils.logic_error import LogicError
from algokit_utils.network_clients import get_algod_client, get_indexer_client
from conftest import check_output_stability, get_specs, get_unique_name, read_spec

logger = logging.getLogger(__name__)


class DeployFixture:
    def __init__(self, caplog: pytest.LogCaptureFixture, request: pytest.FixtureRequest):
        self.app_ids = []
        self.caplog = caplog
        self.request = request
        self.algod_client = get_algod_client()
        self.indexer_client = get_indexer_client()
        self.creator_name = get_unique_name()
        self.creator = get_account(self.algod_client, self.creator_name)

    def deploy(
        self,
        app_spec: ApplicationSpecification,
        *,
        version: str | None = None,
        on_update: OnUpdate = OnUpdate.UpdateApp,
        on_schema_break: OnSchemaBreak = OnSchemaBreak.Fail,
        allow_delete: bool | None = None,
        allow_update: bool | None = None,
    ) -> ApplicationClient:
        app_client = ApplicationClient(self.algod_client, self.indexer_client, app_spec, creator=self.creator)
        response = app_client.deploy(
            version=version,
            on_update=on_update,
            on_schema_break=on_schema_break,
            allow_update=allow_update,
            allow_delete=allow_delete,
        )
        self._wait_for_indexer_round(response.app.updated_round)
        self.app_ids.append(app_client.app_id)
        return app_client

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

    def _wait_for_indexer_round(self, round_target: int, max_attempts: int = 100) -> None:
        for _attempts in range(max_attempts):
            health = self.indexer_client.health()  # type: ignore[no-untyped-call]
            if health["round"] >= round_target:
                break


@pytest.fixture
def deploy_fixture(caplog: pytest.LogCaptureFixture, request: pytest.FixtureRequest) -> DeployFixture:
    caplog.set_level(logging.DEBUG)
    return DeployFixture(caplog, request)


def test_deploy_app_with_no_existing_app_succeeds(deploy_fixture: DeployFixture):
    v1, _, _ = get_specs()

    app = deploy_fixture.deploy(v1, version="1.0")

    assert app.app_id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_updatable_app_succeeds(deploy_fixture: DeployFixture):
    v1, v2, _ = get_specs(updatable=True)

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.app_id

    app_v2 = deploy_fixture.deploy(v2, version="2.0")

    assert app_v1.app_id == app_v2.app_id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_immutable_app_fails(deploy_fixture: DeployFixture):
    v1, v2, _ = get_specs(updatable=False)

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.app_id

    with pytest.raises(LogicError) as error:
        deploy_fixture.deploy(v2, version="2.0")
    logger.error(f"LogicException: {error.value.message}")

    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_immutable_app_and_on_update_equals_replace_app_succeeds(
    deploy_fixture: DeployFixture,
):
    v1, v2, _ = get_specs(updatable=False, deletable=True)

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.app_id

    app_v2 = deploy_fixture.deploy(v2, version="2.0", on_update=OnUpdate.ReplaceApp)

    assert app_v1.app_id != app_v2.app_id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_deletable_app_succeeds(deploy_fixture: DeployFixture):
    v1, v2, _ = get_specs(deletable=True)

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.app_id

    app_v2 = deploy_fixture.deploy(v2, version="2.0", on_update=OnUpdate.ReplaceApp)
    assert app_v1.app_id != app_v2.app_id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_permanent_app_fails(deploy_fixture: DeployFixture):
    v1, _, v3 = get_specs(deletable=False)

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.app_id

    with pytest.raises(DeploymentFailedError) as error:
        deploy_fixture.deploy(v3, version="3.0")
    logger.error(f"DeploymentFailedError: {error.value}")
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_permanent_app_on_update_equals_replace_app_fails_and_doesnt_create_2nd_app(
    deploy_fixture: DeployFixture,
):
    v1, v2, _ = get_specs(deletable=False)

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.app_id

    with pytest.raises(LogicError) as error:
        deploy_fixture.deploy(v2, version="3.0", on_update=OnUpdate.ReplaceApp)
    all_apps = deploy_fixture.indexer_client.lookup_account_application_by_creator(deploy_fixture.creator.address)[
        "applications"
    ]  # type: ignore[no-untyped-call]

    # ensure no other apps were created
    assert len(all_apps) == 1

    logger.error(f"DeploymentFailedError: {error.value.message}")
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_permanent_app_and_on_schema_break_equals_replace_app_fails(
    deploy_fixture: DeployFixture,
):
    v1, _, v3 = get_specs(deletable=False)

    app_v1 = deploy_fixture.deploy(v1, version="1.0")
    assert app_v1.app_id

    with pytest.raises(LogicError) as exc_info:
        deploy_fixture.deploy(v3, version="3.0", on_schema_break=OnSchemaBreak.ReplaceApp)

    logger.error(f"Deployment failed: {exc_info.value.message}")

    deploy_fixture.check_log_stability()


def test_deploy_templated_app_with_changing_parameters_succeeds(deploy_fixture: DeployFixture):
    app_spec = read_spec("app_v1.json")

    logger.info("Deploy V1 as updatable, deletable")
    app_client = deploy_fixture.deploy(
        app_spec,
        version="1",
        allow_delete=True,
        allow_update=True,
    )

    response = app_client.call("hello", args={"name": "call_1"})
    logger.info(f"Called hello: {response.abi_result.return_value}")

    logger.info("Deploy V2 as immutable, deletable")
    app_client = deploy_fixture.deploy(
        app_spec,
        allow_delete=True,
        allow_update=False,
    )

    response = app_client.call("hello", args={"name": "call_2"})
    logger.info(f"Called hello: {response.abi_result.return_value}")

    logger.info("Attempt to deploy V3 as updatable, deletable, it will fail because V2 was immutable")
    with pytest.raises(LogicError) as exc_info:
        # try to make it updatable again
        deploy_fixture.deploy(
            app_spec,
            allow_delete=True,
            allow_update=True,
        )

    logger.error(f"LogicException: {exc_info.value.message}")
    response = app_client.call("hello", args={"name": "call_3"})
    logger.info(f"Called hello: {response.abi_result.return_value}")

    logger.info("2nd Attempt to deploy V3 as updatable, deletable, it will succeed as on_update=OnUpdate.DeleteApp")
    # deploy with allow_delete=True, so we can replace it
    app_client = deploy_fixture.deploy(
        app_spec,
        version="4",
        on_update=OnUpdate.ReplaceApp,
        allow_delete=True,
        allow_update=True,
    )
    response = app_client.call("hello", args={"name": "call_4"})
    logger.info(f"Called hello: {response.abi_result.return_value}")
    app_id = app_client.app_id

    app_client = ApplicationClient(
        deploy_fixture.algod_client,
        deploy_fixture.indexer_client,
        app_spec,
        app_id=app_id,
        signer=deploy_fixture.creator,
    )
    response = app_client.call("hello", args={"name": "call_5"})
    logger.info(f"Called hello: {response.abi_result.return_value}")

    deploy_fixture.check_log_stability()


class Deletable(Enum):
    No = 0
    Yes = 1


class Updatable(Enum):
    No = 0
    Yes = 1


@pytest.mark.parametrize("deletable", [Deletable.No, Deletable.Yes])
@pytest.mark.parametrize("updatable", [Updatable.No, Updatable.Yes])
@pytest.mark.parametrize("on_schema_break", [OnSchemaBreak.Fail, OnSchemaBreak.ReplaceApp])
def test_deploy_with_schema_breaking_change(
    deploy_fixture: DeployFixture,
    *,
    deletable: Deletable,
    updatable: Updatable,
    on_schema_break: OnSchemaBreak,
):
    v1 = read_spec("app_v1.json")
    v3 = read_spec("app_v3.json")

    app_v1 = deploy_fixture.deploy(
        v1, version="1.0", allow_delete=deletable == deletable.Yes, allow_update=updatable == updatable.Yes
    )
    assert app_v1.app_id

    try:
        deploy_fixture.deploy(
            v3,
            version="3.0",
            allow_delete=deletable == deletable.Yes,
            allow_update=updatable == updatable.Yes,
            on_schema_break=on_schema_break,
        )
    except DeploymentFailedError as error:
        logger.error(f"DeploymentFailedError: {error}")
    except LogicError as error:
        logger.error(f"LogicException: {error.message}")

    deploy_fixture.check_log_stability()


@pytest.mark.parametrize("deletable", [Deletable.No, Deletable.Yes])
@pytest.mark.parametrize("updatable", [Updatable.No, Updatable.Yes])
@pytest.mark.parametrize("on_update", [OnUpdate.Fail, OnUpdate.UpdateApp, OnUpdate.ReplaceApp])
def test_deploy_with_update(
    deploy_fixture: DeployFixture,
    *,
    deletable: Deletable,
    updatable: Updatable,
    on_update: OnUpdate,
):
    v1 = read_spec("app_v1.json")
    v2 = read_spec("app_v2.json")

    app_v1 = deploy_fixture.deploy(
        v1, version="1.0", allow_delete=deletable == deletable.Yes, allow_update=updatable == updatable.Yes
    )
    assert app_v1.app_id

    try:
        deploy_fixture.deploy(
            v2,
            version="2.0",
            allow_delete=deletable == deletable.Yes,
            allow_update=updatable == updatable.Yes,
            on_update=on_update,
        )
    except DeploymentFailedError as error:
        logger.error(f"DeploymentFailedError: {error}")
    except LogicError as error:
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
    result = replace_template_variables(program, {"INT": 123, "STR": "ABC"})
    check_output_stability(result)


@pytest.mark.parametrize(
    "current,expected_next",
    [
        ("1", "2"),
        ("v1", "v2"),
        ("v1-alpha", "v2-alpha"),
        ("1.0", "1.1"),
        ("v1.0", "v1.1"),
        ("v1.0-alpha", "v1.1-alpha"),
        ("1.0.0", "1.0.1"),
        ("v1.0.0", "v1.0.1"),
        ("v1.0.0-alpha", "v1.0.1-alpha"),
    ],
)
def test_auto_version_increment(current: str | None, expected_next: str | None) -> None:
    try:
        value = get_next_version(current)
    except DeploymentFailedError:
        if expected_next is not None:
            raise AssertionError(f"failed to auto increment {current}") from None
        else:
            return
    assert value == expected_next


def test_auto_version_increment_failure():
    with pytest.raises(DeploymentFailedError):
        get_next_version("teapot")
