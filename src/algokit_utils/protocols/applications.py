from typing import Any, Protocol

from algokit_utils.applications.app_client import AppClient, AppClientBareCallParams, AppClientMethodCallParams
from algokit_utils.applications.app_deployer import AppLookup, OnSchemaBreak, OnUpdate
from algokit_utils.applications.app_factory import AppFactoryDeployResponse
from algokit_utils.models.state import TealTemplateParams
from algokit_utils.protocols.client import AlgorandClientProtocol


class TypedAppFactoryProtocol(Protocol):
    def __init__(
        self,
        algorand: AlgorandClientProtocol,
        **kwargs: Any,
    ) -> None: ...

    def deploy(  # noqa: PLR0913
        self,
        *,
        deploy_time_params: TealTemplateParams | None = None,
        on_update: OnUpdate = OnUpdate.Fail,
        on_schema_break: OnSchemaBreak = OnSchemaBreak.Fail,
        create_params: AppClientMethodCallParams | AppClientBareCallParams | None = None,
        update_params: AppClientMethodCallParams | AppClientBareCallParams | None = None,
        delete_params: AppClientMethodCallParams | AppClientBareCallParams | None = None,
        existing_deployments: AppLookup | None = None,
        ignore_cache: bool = False,
        updatable: bool | None = None,
        deletable: bool | None = None,
        app_name: str | None = None,
        max_rounds_to_wait: int | None = None,
        suppress_log: bool = False,
        populate_app_call_resources: bool = False,
    ) -> tuple[AppClient, "AppFactoryDeployResponse"]: ...
