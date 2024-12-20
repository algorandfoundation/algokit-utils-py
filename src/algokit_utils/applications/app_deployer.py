import base64
import dataclasses
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Literal

from algosdk.logic import get_application_address
from algosdk.v2client.indexer import IndexerClient

from algokit_utils.applications.app_manager import AppManager
from algokit_utils.config import config
from algokit_utils.models.state import TealTemplateParams
from algokit_utils.transactions.transaction_composer import (
    AppCreateMethodCallParams,
    AppCreateParams,
    AppDeleteMethodCallParams,
    AppDeleteParams,
    AppUpdateMethodCallParams,
    AppUpdateParams,
)
from algokit_utils.transactions.transaction_sender import (
    AlgorandClientTransactionSender,
    SendAppCreateTransactionResult,
    SendAppTransactionResult,
    SendAppUpdateTransactionResult,
)

__all__ = [
    "APP_DEPLOY_NOTE_DAPP",
    "AppDeployMetaData",
    "AppDeployParams",
    "AppDeployResponse",
    "AppDeployer",
    "AppLookup",
    "AppMetaData",
    "AppReference",
    "OnSchemaBreak",
    "OnUpdate",
    "OperationPerformed",
]


APP_DEPLOY_NOTE_DAPP: str = "ALGOKIT_DEPLOYER"

logger = config.logger


@dataclasses.dataclass
class AppReference:
    """Information about an Algorand app"""

    app_id: int
    app_address: str


@dataclasses.dataclass
class AppDeployMetaData:
    """Metadata about an application stored in a transaction note during creation.

    The note is serialized as JSON and prefixed with {py:data}`NOTE_PREFIX` and stored in the transaction note field
    as part of {py:meth}`ApplicationClient.deploy`
    """

    name: str
    version: str
    deletable: bool | None
    updatable: bool | None


@dataclasses.dataclass
class AppMetaData(AppReference, AppDeployMetaData):
    """Metadata about a deployed app"""

    created_round: int
    updated_round: int
    created_metadata: AppDeployMetaData
    deleted: bool


@dataclasses.dataclass
class AppLookup:
    """Cache of {py:class}`AppMetaData` for a specific `creator`

    Can be used as an argument to {py:class}`ApplicationClient` to reduce the number of calls when deploying multiple
    apps or discovering multiple app_ids
    """

    creator: str
    apps: dict[str, AppMetaData] = dataclasses.field(default_factory=dict)


class OnSchemaBreak(str, Enum):
    """Action to take if an Application's schema has breaking changes"""

    Fail = "fail"
    """Fail the deployment"""
    ReplaceApp = "replace_app"
    """Create a new Application and delete the old Application in a single transaction"""
    AppendApp = "append_app"
    """Create a new Application"""


class OnUpdate(str, Enum):
    """Action to take if an Application has been updated"""

    Fail = "fail"
    """Fail the deployment"""
    UpdateApp = "update_app"
    """Update the Application with the new approval and clear programs"""
    ReplaceApp = "replace_app"
    """Create a new Application and delete the old Application in a single transaction"""
    AppendApp = "append_app"
    """Create a new application"""


class OperationPerformed(str, Enum):
    """Describes the actions taken during deployment"""

    Nothing = "nothing"
    """An existing Application was found"""
    Create = "create"
    """No existing Application was found, created a new Application"""
    Update = "update"
    """An existing Application was found, but was out of date, updated to latest version"""
    Replace = "replace"
    """An existing Application was found, but was out of date, created a new Application and deleted the original"""


@dataclass(kw_only=True)
class AppDeployParams:
    """Parameters for deploying an app"""

    metadata: AppDeployMetaData
    deploy_time_params: TealTemplateParams | None = None
    on_schema_break: Literal["replace", "fail", "append"] | OnSchemaBreak = OnSchemaBreak.Fail
    on_update: Literal["update", "replace", "fail", "append"] | OnUpdate = OnUpdate.Fail
    create_params: AppCreateParams | AppCreateMethodCallParams
    update_params: AppUpdateParams | AppUpdateMethodCallParams
    delete_params: AppDeleteParams | AppDeleteMethodCallParams
    existing_deployments: AppLookup | None = None
    ignore_cache: bool = False
    max_fee: int | None = None
    max_rounds_to_wait: int | None = None
    suppress_log: bool = False
    populate_app_call_resources: bool = False


# Union type for all possible deploy results
@dataclass(frozen=True)
class AppDeployResponse:
    app: AppMetaData
    operation_performed: OperationPerformed
    create_response: SendAppCreateTransactionResult | None = None
    update_response: SendAppUpdateTransactionResult | None = None
    delete_response: SendAppTransactionResult | None = None


class AppDeployer:
    """Manages deployment and deployment metadata of applications"""

    def __init__(
        self,
        app_manager: AppManager,
        transaction_sender: AlgorandClientTransactionSender,
        indexer: IndexerClient | None = None,
    ):
        self._app_manager = app_manager
        self._transaction_sender = transaction_sender
        self._indexer = indexer
        self._app_lookups: dict[str, AppLookup] = {}

    def _create_deploy_note(self, metadata: AppDeployMetaData) -> bytes:
        note = {
            "dapp_name": APP_DEPLOY_NOTE_DAPP,
            "format": "j",
            "data": metadata.__dict__,
        }
        return json.dumps(note).encode()

    def deploy(self, deployment: AppDeployParams) -> AppDeployResponse:
        # Create new instances with updated notes
        logger.info(
            f"Idempotently deploying app \"{deployment.metadata.name}\" from creator "
            f"{deployment.create_params.sender} using {len(deployment.create_params.approval_program)} bytes of "
            f"{'teal code' if isinstance(deployment.create_params.approval_program, str) else 'AVM bytecode'} and "
            f"{len(deployment.create_params.clear_state_program)} bytes of "
            f"{'teal code' if isinstance(deployment.create_params.clear_state_program, str) else 'AVM bytecode'}",
            suppress_log=deployment.suppress_log,
        )
        note = self._create_deploy_note(deployment.metadata)
        create_params = dataclasses.replace(deployment.create_params, note=note)
        update_params = dataclasses.replace(deployment.update_params, note=note)

        deployment = dataclasses.replace(
            deployment,
            create_params=create_params,
            update_params=update_params,
        )

        # Validate inputs
        if (
            deployment.existing_deployments
            and deployment.existing_deployments.creator != deployment.create_params.sender
        ):
            raise ValueError(
                f"Received invalid existingDeployments value for creator "
                f"{deployment.existing_deployments.creator} when attempting to deploy "
                f"for creator {deployment.create_params.sender}"
            )

        if not deployment.existing_deployments and not self._indexer:
            raise ValueError(
                "Didn't receive an indexer client when this AppManager was created, "
                "but also didn't receive an existingDeployments cache - one of them must be provided"
            )

        # Compile code if needed
        approval_program = deployment.create_params.approval_program
        clear_program = deployment.create_params.clear_state_program

        if isinstance(approval_program, str):
            compiled_approval = self._app_manager.compile_teal_template(
                approval_program,
                deployment.deploy_time_params,
                deployment.metadata.__dict__,
            )
            approval_program = compiled_approval.compiled_base64_to_bytes

        if isinstance(clear_program, str):
            compiled_clear = self._app_manager.compile_teal_template(
                clear_program,
                deployment.deploy_time_params,
            )
            clear_program = compiled_clear.compiled_base64_to_bytes

        # Get existing app metadata
        apps = deployment.existing_deployments or self.get_creator_apps_by_name(
            creator_address=deployment.create_params.sender,
            ignore_cache=deployment.ignore_cache,
        )

        existing_app = apps.apps.get(deployment.metadata.name)
        if not existing_app or existing_app.deleted:
            return self._create_app(
                deployment=deployment,
                approval_program=approval_program,
                clear_program=clear_program,
            )

        # Check for changes
        existing_app_record = self._app_manager.get_by_id(existing_app.app_id)

        existing_approval = base64.b64encode(existing_app_record.approval_program).decode()
        existing_clear = base64.b64encode(existing_app_record.clear_state_program).decode()

        new_approval = base64.b64encode(approval_program).decode()
        new_clear = base64.b64encode(clear_program).decode()

        is_update = new_approval != existing_approval or new_clear != existing_clear
        is_schema_break = (
            existing_app_record.local_ints
            < (deployment.create_params.schema.get("local_ints", 0) if deployment.create_params.schema else 0)
            or existing_app_record.global_ints
            < (deployment.create_params.schema.get("global_ints", 0) if deployment.create_params.schema else 0)
            or existing_app_record.local_byte_slices
            < (deployment.create_params.schema.get("local_byte_slices", 0) if deployment.create_params.schema else 0)
            or existing_app_record.global_byte_slices
            < (deployment.create_params.schema.get("global_byte_slices", 0) if deployment.create_params.schema else 0)
        )

        if is_schema_break:
            logger.warning(
                f"Detected a breaking app schema change in app {existing_app.app_id}:",
                extra={
                    "from": {
                        "global_ints": existing_app_record.global_ints,
                        "global_byte_slices": existing_app_record.global_byte_slices,
                        "local_ints": existing_app_record.local_ints,
                        "local_byte_slices": existing_app_record.local_byte_slices,
                    },
                    "to": deployment.create_params.schema,
                },
                suppress_log=deployment.suppress_log,
            )

            return self._handle_schema_break(
                deployment=deployment,
                existing_app=existing_app,
                approval_program=approval_program,
                clear_program=clear_program,
            )

        if is_update:
            return self._handle_update(
                deployment=deployment,
                existing_app=existing_app,
                approval_program=approval_program,
                clear_program=clear_program,
            )

        logger.debug("No detected changes in app, nothing to do.", suppress_log=deployment.suppress_log)
        return AppDeployResponse(
            app=existing_app,
            operation_performed=OperationPerformed.Nothing,
        )

    def _create_app(
        self,
        deployment: AppDeployParams,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeployResponse:
        """Create a new application"""

        if isinstance(deployment.create_params, AppCreateMethodCallParams):
            create_response = self._transaction_sender.app_create_method_call(
                AppCreateMethodCallParams(
                    **{
                        **asdict(deployment.create_params),
                        "approval_program": approval_program,
                        "clear_state_program": clear_program,
                    }
                )
            )
        else:
            create_response = self._transaction_sender.app_create(
                AppCreateParams(
                    **{
                        **asdict(deployment.create_params),
                        "approval_program": approval_program,
                        "clear_state_program": clear_program,
                    }
                )
            )

        app_metadata = AppMetaData(
            app_id=create_response.app_id,
            app_address=get_application_address(create_response.app_id),
            **asdict(deployment.metadata),
            created_metadata=deployment.metadata,
            created_round=create_response.confirmation.get("confirmed-round", 0)
            if isinstance(create_response.confirmation, dict)
            else 0,
            updated_round=create_response.confirmation.get("confirmed-round", 0)
            if isinstance(create_response.confirmation, dict)
            else 0,
            deleted=False,
        )

        self._update_app_lookup(deployment.create_params.sender, app_metadata)

        return AppDeployResponse(
            app=app_metadata,
            operation_performed=OperationPerformed.Create,
            create_response=create_response,
        )

    def _replace_app(
        self,
        deployment: AppDeployParams,
        existing_app: AppMetaData,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeployResponse:
        composer = self._transaction_sender.new_group()

        # Add create transaction
        if isinstance(deployment.create_params, AppCreateMethodCallParams):
            composer.add_app_create_method_call(
                AppCreateMethodCallParams(
                    **{
                        **deployment.create_params.__dict__,
                        "approval_program": approval_program,
                        "clear_state_program": clear_program,
                    }
                )
            )
        else:
            composer.add_app_create(
                AppCreateParams(
                    **{
                        **deployment.create_params.__dict__,
                        "approval_program": approval_program,
                        "clear_state_program": clear_program,
                    }
                )
            )
        create_txn_index = composer.count() - 1

        # Add delete transaction
        if isinstance(deployment.delete_params, AppDeleteMethodCallParams):
            delete_call_params = AppDeleteMethodCallParams(
                **{
                    **deployment.delete_params.__dict__,
                    "app_id": existing_app.app_id,
                }
            )
            composer.add_app_delete_method_call(delete_call_params)
        else:
            delete_params = AppDeleteParams(
                **{
                    **deployment.delete_params.__dict__,
                    "app_id": existing_app.app_id,
                }
            )
            composer.add_app_delete(delete_params)
        delete_txn_index = composer.count() - 1

        result = composer.send()

        create_response = SendAppCreateTransactionResult.from_composer_result(result, create_txn_index)
        delete_response = SendAppTransactionResult.from_composer_result(result, delete_txn_index)

        app_id = int(result.confirmations[0]["application-index"])  # type: ignore[call-overload]
        app_metadata = AppMetaData(
            app_id=app_id,
            app_address=get_application_address(app_id),
            **deployment.metadata.__dict__,
            created_metadata=deployment.metadata,
            created_round=result.confirmations[0]["confirmed-round"],  # type: ignore[call-overload]
            updated_round=result.confirmations[0]["confirmed-round"],  # type: ignore[call-overload]
            deleted=False,
        )
        self._update_app_lookup(deployment.create_params.sender, app_metadata)

        return AppDeployResponse(
            app=app_metadata,
            operation_performed=OperationPerformed.Replace,
            create_response=create_response,
            update_response=None,
            delete_response=delete_response,
        )

    def _update_app(
        self,
        deployment: AppDeployParams,
        existing_app: AppMetaData,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeployResponse:
        """Update an existing application"""

        if isinstance(deployment.update_params, AppUpdateMethodCallParams):
            result = self._transaction_sender.app_update_method_call(
                AppUpdateMethodCallParams(
                    **{
                        **deployment.update_params.__dict__,
                        "app_id": existing_app.app_id,
                        "approval_program": approval_program,
                        "clear_state_program": clear_program,
                    }
                )
            )
        else:
            result = self._transaction_sender.app_update(
                AppUpdateParams(
                    **{
                        **deployment.update_params.__dict__,
                        "app_id": existing_app.app_id,
                        "approval_program": approval_program,
                        "clear_state_program": clear_program,
                    }
                )
            )

        app_metadata = AppMetaData(
            app_id=existing_app.app_id,
            app_address=existing_app.app_address,
            created_metadata=existing_app.created_metadata,
            created_round=existing_app.created_round,
            updated_round=result.confirmation.get("confirmed-round", 0) if isinstance(result.confirmation, dict) else 0,
            **deployment.metadata.__dict__,
            deleted=False,
        )

        self._update_app_lookup(deployment.create_params.sender, app_metadata)

        return AppDeployResponse(
            app=app_metadata,
            operation_performed=OperationPerformed.Update,
            update_response=result,
        )

    def _handle_schema_break(
        self,
        deployment: AppDeployParams,
        existing_app: AppMetaData,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeployResponse:
        if deployment.on_schema_break in (OnSchemaBreak.Fail, "fail"):
            raise ValueError(
                "Schema break detected and onSchemaBreak=OnSchemaBreak.Fail, stopping deployment. "
                "If you want to try deleting and recreating the app then "
                "re-run with onSchemaBreak=OnSchemaBreak.ReplaceApp"
            )

        if deployment.on_schema_break in (OnSchemaBreak.AppendApp, "append"):
            return self._create_app(deployment, approval_program, clear_program)

        if existing_app.deletable:
            return self._replace_app(deployment, existing_app, approval_program, clear_program)
        else:
            raise ValueError("App is not deletable but onSchemaBreak=ReplaceApp, " "cannot delete and recreate app")

    def _handle_update(
        self,
        deployment: AppDeployParams,
        existing_app: AppMetaData,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeployResponse:
        if deployment.on_update in (OnUpdate.Fail, "fail"):
            raise ValueError(
                "Update detected and onUpdate=Fail, stopping deployment. " "Try a different onUpdate value to not fail."
            )

        if deployment.on_update in (OnUpdate.AppendApp, "append"):
            return self._create_app(deployment, approval_program, clear_program)

        if deployment.on_update in (OnUpdate.UpdateApp, "update"):
            if existing_app.updatable:
                return self._update_app(deployment, existing_app, approval_program, clear_program)
            else:
                raise ValueError("App is not updatable but onUpdate=UpdateApp, cannot update app")

        if deployment.on_update in (OnUpdate.ReplaceApp, "replace"):
            if existing_app.deletable:
                return self._replace_app(deployment, existing_app, approval_program, clear_program)
            else:
                raise ValueError("App is not deletable but onUpdate=ReplaceApp, " "cannot delete and recreate app")

        raise ValueError(f"Unsupported onUpdate value: {deployment.on_update}")

    def _update_app_lookup(self, sender: str, app_metadata: AppMetaData) -> None:
        """Update the app lookup cache"""

        lookup = self._app_lookups.get(sender)
        if not lookup:
            self._app_lookups[sender] = AppLookup(
                creator=sender,
                apps={app_metadata.name: app_metadata},
            )
        else:
            lookup.apps[app_metadata.name] = app_metadata

    def get_creator_apps_by_name(self, *, creator_address: str, ignore_cache: bool = False) -> AppLookup:
        """Get apps created by an account"""

        if not ignore_cache and creator_address in self._app_lookups:
            return self._app_lookups[creator_address]

        if not self._indexer:
            raise ValueError(
                "Didn't receive an indexer client when this AppManager was created, "
                "but received a call to get_creator_apps"
            )

        app_lookup: dict[str, AppMetaData] = {}

        # Get all apps created by account
        created_apps = self._indexer.search_applications(creator=creator_address)

        for app in created_apps["applications"]:
            app_id = app["id"]

            # Get creation transaction
            creation_txns = self._indexer.search_transactions(
                application_id=app_id,
                min_round=app["created-at-round"],
                address=creator_address,
                address_role="sender",
                note_prefix=base64.b64encode(APP_DEPLOY_NOTE_DAPP.encode()),
                limit=1,
            )

            if not creation_txns["transactions"]:
                continue

            creation_txn = creation_txns["transactions"][0]

            try:
                note = base64.b64decode(creation_txn["note"]).decode()
                if not note.startswith(f"{APP_DEPLOY_NOTE_DAPP}:j"):
                    continue

                metadata = json.loads(note[len(APP_DEPLOY_NOTE_DAPP) + 2 :])

                if metadata.get("name"):
                    app_lookup[metadata["name"]] = AppMetaData(
                        app_id=app_id,
                        app_address=get_application_address(app_id),
                        created_metadata=metadata,
                        created_round=creation_txn["confirmed-round"],
                        **metadata,
                        updated_round=creation_txn["confirmed-round"],
                        deleted=app.get("deleted", False),
                    )
            except Exception as e:
                logger.warning(
                    f"Error processing app {app_id} for creator {creator_address}: {e}",
                )
                continue

        lookup = AppLookup(creator=creator_address, apps=app_lookup)
        self._app_lookups[creator_address] = lookup
        return lookup
