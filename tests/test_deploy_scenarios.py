import logging
import re
from enum import Enum

import pytest
from algokit_utils import (
    Account,
    ApplicationClient,
    ApplicationSpecification,
    DeploymentFailedError,
    LogicError,
    OnSchemaBreak,
    OnUpdate,
    get_account,
    get_algod_client,
    get_indexer_client,
    get_localnet_default_account,
)

from tests.conftest import check_output_stability, get_specs, get_unique_name, read_spec

logger = logging.getLogger(__name__)


class DeployFixture:
    def __init__(
        self,
        caplog: pytest.LogCaptureFixture,
        request: pytest.FixtureRequest,
        creator_name: str,
        creator: Account,
        app_name: str,
    ):
        self.app_ids: list[int] = []
        self.caplog = caplog
        self.request = request
        self.algod_client = get_algod_client()
        self.indexer_client = get_indexer_client()
        self.creator_name = creator_name
        self.creator = creator
        self.app_name = app_name

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
        app_client = ApplicationClient(
            self.algod_client, app_spec, indexer_client=self.indexer_client, creator=self.creator
        )
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

    def check_log_stability(self, replacements: dict[str, str] | None = None, suffix: str = "") -> None:
        if replacements is None:
            replacements = {}
        replacements[self.app_name] = "SampleApp"
        records = self.caplog.get_records("call")
        logs = "\n".join(f"{r.levelname}: {r.message}" for r in records)
        logs = self._normalize_logs(logs)
        for find, replace in (replacements or {}).items():
            logs = logs.replace(find, replace)
        check_output_stability(logs, test_name=self.request.node.name + suffix)

    def _normalize_logs(self, logs: str) -> str:
        dispenser = get_localnet_default_account(self.algod_client)
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


@pytest.fixture(scope="module")
def creator_name() -> str:
    return get_unique_name()


@pytest.fixture(scope="module")
def creator(creator_name: str) -> Account:
    return get_account(get_algod_client(), creator_name)


@pytest.fixture()
def app_name() -> str:
    return get_unique_name()


@pytest.fixture()
def deploy_fixture(
    caplog: pytest.LogCaptureFixture, request: pytest.FixtureRequest, creator_name: str, creator: Account, app_name: str
) -> DeployFixture:
    caplog.set_level(logging.DEBUG)
    return DeployFixture(caplog, request, creator_name=creator_name, creator=creator, app_name=app_name)


def test_deploy_app_with_no_existing_app_succeeds(deploy_fixture: DeployFixture, app_name: str) -> None:
    v1, _, _ = get_specs(name=app_name)

    app = deploy_fixture.deploy(v1, version="1.0", allow_update=False, allow_delete=False)

    assert app.app_id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_updatable_app_succeeds(deploy_fixture: DeployFixture, app_name: str) -> None:
    v1, v2, _ = get_specs(name=app_name)

    app_v1 = deploy_fixture.deploy(v1, version="1.0", allow_update=True, allow_delete=False)
    assert app_v1.app_id

    app_v2 = deploy_fixture.deploy(v2, version="2.0", allow_update=True, allow_delete=False)

    assert app_v1.app_id == app_v2.app_id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_immutable_app_fails(deploy_fixture: DeployFixture, app_name: str) -> None:
    v1, v2, _ = get_specs(name=app_name)

    app_v1 = deploy_fixture.deploy(v1, version="1.0", allow_update=False, allow_delete=False)
    assert app_v1.app_id

    with pytest.raises(LogicError) as error:
        deploy_fixture.deploy(v2, version="2.0", allow_update=False, allow_delete=False)
    logger.error(f"LogicException: {error.value.message}")

    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_immutable_app_and_on_update_equals_replace_app_succeeds(
    deploy_fixture: DeployFixture,
    app_name: str,
) -> None:
    v1, v2, _ = get_specs(name=app_name)

    app_v1 = deploy_fixture.deploy(v1, version="1.0", allow_update=False, allow_delete=True)
    assert app_v1.app_id

    app_v2 = deploy_fixture.deploy(
        v2, version="2.0", allow_update=False, allow_delete=True, on_update=OnUpdate.ReplaceApp
    )

    assert app_v1.app_id != app_v2.app_id
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_permanent_app_fails(deploy_fixture: DeployFixture, app_name: str) -> None:
    v1, _, v3 = get_specs(name=app_name)

    app_v1 = deploy_fixture.deploy(v1, version="1.0", allow_update=False, allow_delete=False)
    assert app_v1.app_id

    with pytest.raises(DeploymentFailedError) as error:
        deploy_fixture.deploy(v3, version="3.0", allow_update=False, allow_delete=False)
    logger.error(f"DeploymentFailedError: {error.value}")
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_immutable_app_cannot_determine_if_updatable(
    deploy_fixture: DeployFixture, app_name: str
) -> None:
    v1, v2, _ = get_specs(updatable=False, deletable=False, name=app_name)

    app_v1 = deploy_fixture.deploy(v1)
    assert app_v1.app_id

    with pytest.raises(LogicError) as error:
        deploy_fixture.deploy(v2, on_update=OnUpdate.UpdateApp)
    logger.error(f"LogicError: {error.value.message}")
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_permanent_app_cannot_determine_if_deletable(
    deploy_fixture: DeployFixture, app_name: str
) -> None:
    v1, v2, _ = get_specs(updatable=False, deletable=False, name=app_name)

    app_v1 = deploy_fixture.deploy(v1)
    assert app_v1.app_id

    with pytest.raises(LogicError) as error:
        deploy_fixture.deploy(v2, on_update=OnUpdate.ReplaceApp)
    logger.error(f"LogicError: {error.value.message}")
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_permanent_app_on_update_equals_replace_app_fails_and_doesnt_create_2nd_app(
    deploy_fixture: DeployFixture,
    app_name: str,
) -> None:
    v1, v2, _ = get_specs(name=app_name)

    app_v1 = deploy_fixture.deploy(v1, version="1.0", allow_update=False, allow_delete=False)
    assert app_v1.app_id

    apps_before = deploy_fixture.indexer_client.lookup_account_application_by_creator(
        deploy_fixture.creator.address
    )  # type: ignore[no-untyped-call]

    with pytest.raises(LogicError) as error:
        deploy_fixture.deploy(v2, version="3.0", allow_update=False, allow_delete=False, on_update=OnUpdate.ReplaceApp)
    apps_after = deploy_fixture.indexer_client.lookup_account_application_by_creator(
        deploy_fixture.creator.address
    )  # type: ignore[no-untyped-call]

    # ensure no other apps were created
    assert len(apps_before["applications"]) == len(apps_after["applications"])

    logger.error(f"DeploymentFailedError: {error.value.message}")
    deploy_fixture.check_log_stability()


def test_deploy_app_with_existing_permanent_app_and_on_schema_break_equals_replace_app_fails(
    deploy_fixture: DeployFixture,
    app_name: str,
) -> None:
    v1, _, v3 = get_specs(name=app_name)

    app_v1 = deploy_fixture.deploy(v1, allow_update=False, allow_delete=False, version="1.0")
    assert app_v1.app_id

    with pytest.raises(LogicError) as exc_info:
        deploy_fixture.deploy(
            v3, allow_update=False, allow_delete=False, version="3.0", on_schema_break=OnSchemaBreak.ReplaceApp
        )

    logger.error(f"Deployment failed: {exc_info.value.message}")

    deploy_fixture.check_log_stability()


def test_deploy_templated_app_with_changing_parameters_succeeds(deploy_fixture: DeployFixture, app_name: str) -> None:
    app_spec = read_spec("app_v1.json", name=app_name)

    logger.info("Deploy V1 as updatable, deletable")
    app_client = deploy_fixture.deploy(
        app_spec,
        version="1",
        allow_delete=True,
        allow_update=True,
    )

    response = app_client.call("hello", name="call_1")
    logger.info(f"Called hello: {response.return_value}")

    logger.info("Deploy V2 as immutable, deletable")
    app_client = deploy_fixture.deploy(
        app_spec,
        allow_delete=True,
        allow_update=False,
    )

    response = app_client.call("hello", name="call_2")
    logger.info(f"Called hello: {response.return_value}")

    logger.info("Attempt to deploy V3 as updatable, deletable, it will fail because V2 was immutable")
    with pytest.raises(LogicError) as exc_info:
        # try to make it updatable again
        deploy_fixture.deploy(
            app_spec,
            allow_delete=True,
            allow_update=True,
        )

    logger.error(f"LogicException: {exc_info.value.message}")
    response = app_client.call("hello", name="call_3")
    logger.info(f"Called hello: {response.return_value}")

    logger.info("2nd Attempt to deploy V3 as updatable, deletable, it will succeed as on_update=OnUpdate.DeleteApp")
    # deploy with allow_delete=True, so we can replace it
    app_client = deploy_fixture.deploy(
        app_spec,
        version="4",
        on_update=OnUpdate.ReplaceApp,
        allow_delete=True,
        allow_update=True,
    )
    response = app_client.call("hello", name="call_4")
    logger.info(f"Called hello: {response.return_value}")
    app_id = app_client.app_id

    app_client = ApplicationClient(
        deploy_fixture.algod_client,
        app_spec,
        app_id=app_id,
        signer=deploy_fixture.creator,
    )
    response = app_client.call("hello", name="call_5")
    logger.info(f"Called hello: {response.return_value}")

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
    app_name: str,
) -> None:
    v1, _, v3 = get_specs(name=app_name)

    app_v1 = deploy_fixture.deploy(
        v1, version="1.0", allow_delete=deletable == Deletable.Yes, allow_update=updatable == Updatable.Yes
    )
    assert app_v1.app_id

    try:
        deploy_fixture.deploy(
            v3,
            version="3.0",
            allow_delete=deletable == Deletable.Yes,
            allow_update=updatable == Updatable.Yes,
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
    app_name: str,
) -> None:
    v1, v2, _ = get_specs(name=app_name)

    app_v1 = deploy_fixture.deploy(
        v1, version="1.0", allow_delete=deletable == Deletable.Yes, allow_update=updatable == Updatable.Yes
    )
    assert app_v1.app_id

    try:
        deploy_fixture.deploy(
            v2,
            version="2.0",
            allow_delete=deletable == Deletable.Yes,
            allow_update=updatable == Updatable.Yes,
            on_update=on_update,
        )
    except DeploymentFailedError as error:
        logger.error(f"DeploymentFailedError: {error}")
    except LogicError as error:
        logger.error(f"LogicException: {error.message}")

    deploy_fixture.check_log_stability()
