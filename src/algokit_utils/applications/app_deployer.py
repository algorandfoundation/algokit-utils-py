import base64
import dataclasses
import json
from dataclasses import asdict, dataclass
from typing import Literal

from algosdk.logic import get_application_address
from algosdk.v2client.indexer import IndexerClient

from algokit_utils.applications.abi import ABIReturn
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.applications.enums import OnSchemaBreak, OnUpdate, OperationPerformed
from algokit_utils.config import config
from algokit_utils.models.state import TealTemplateParams
from algokit_utils.models.transaction import SendParams
from algokit_utils.transactions.transaction_composer import (
    AppCreateMethodCallParams,
    AppCreateParams,
    AppDeleteMethodCallParams,
    AppDeleteParams,
    AppUpdateMethodCallParams,
    AppUpdateParams,
    TransactionComposer,
)
from algokit_utils.transactions.transaction_sender import (
    AlgorandClientTransactionSender,
    SendAppCreateTransactionResult,
    SendAppTransactionResult,
    SendAppUpdateTransactionResult,
)

__all__ = [
    "APP_DEPLOY_NOTE_DAPP",
    "AppDeployParams",
    "AppDeployResult",
    "AppDeployer",
    "AppDeploymentMetaData",
    "ApplicationLookup",
    "ApplicationMetaData",
    "ApplicationReference",
    "OnSchemaBreak",
    "OnUpdate",
    "OperationPerformed",
]


APP_DEPLOY_NOTE_DAPP: str = "ALGOKIT_DEPLOYER"

logger = config.logger


@dataclasses.dataclass
class AppDeploymentMetaData:
    """Metadata about an application stored in a transaction note during creation."""

    name: str
    version: str
    deletable: bool | None
    updatable: bool | None

    def dictify(self) -> dict[str, str | bool]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclasses.dataclass(frozen=True)
class ApplicationReference:
    """Information about an Algorand app"""

    app_id: int
    app_address: str


@dataclasses.dataclass(frozen=True)
class ApplicationMetaData:
    """Complete metadata about a deployed app"""

    reference: ApplicationReference
    deploy_metadata: AppDeploymentMetaData
    created_round: int
    updated_round: int
    deleted: bool = False

    @property
    def app_id(self) -> int:
        return self.reference.app_id

    @property
    def app_address(self) -> str:
        return self.reference.app_address

    @property
    def name(self) -> str:
        return self.deploy_metadata.name

    @property
    def version(self) -> str:
        return self.deploy_metadata.version

    @property
    def deletable(self) -> bool | None:
        return self.deploy_metadata.deletable

    @property
    def updatable(self) -> bool | None:
        return self.deploy_metadata.updatable


@dataclasses.dataclass
class ApplicationLookup:
    """Cache of {py:class}`ApplicationMetaData` for a specific `creator`

    Can be used as an argument to {py:class}`ApplicationClient` to reduce the number of calls when deploying multiple
    apps or discovering multiple app_ids
    """

    creator: str
    apps: dict[str, ApplicationMetaData] = dataclasses.field(default_factory=dict)


@dataclass(kw_only=True)
class AppDeployParams:
    """Parameters for deploying an app"""

    metadata: AppDeploymentMetaData
    deploy_time_params: TealTemplateParams | None = None
    on_schema_break: (Literal["replace", "fail", "append"] | OnSchemaBreak) | None = None
    on_update: (Literal["update", "replace", "fail", "append"] | OnUpdate) | None = None
    create_params: AppCreateParams | AppCreateMethodCallParams
    update_params: AppUpdateParams | AppUpdateMethodCallParams
    delete_params: AppDeleteParams | AppDeleteMethodCallParams
    existing_deployments: ApplicationLookup | None = None
    ignore_cache: bool = False
    max_fee: int | None = None
    send_params: SendParams | None = None


# Union type for all possible deploy results
@dataclass(frozen=True)
class AppDeployResult:
    app: ApplicationMetaData
    operation_performed: OperationPerformed
    create_result: SendAppCreateTransactionResult[ABIReturn] | None = None
    update_result: SendAppUpdateTransactionResult[ABIReturn] | None = None
    delete_result: SendAppTransactionResult[ABIReturn] | None = None


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
        self._app_lookups: dict[str, ApplicationLookup] = {}

    def deploy(self, deployment: AppDeployParams) -> AppDeployResult:
        # Create new instances with updated notes
        send_params = deployment.send_params or SendParams()
        suppress_log = send_params.get("suppress_log") or False

        logger.info(
            f"Idempotently deploying app \"{deployment.metadata.name}\" from creator "
            f"{deployment.create_params.sender} using {len(deployment.create_params.approval_program)} bytes of "
            f"{'teal code' if isinstance(deployment.create_params.approval_program, str) else 'AVM bytecode'} and "
            f"{len(deployment.create_params.clear_state_program)} bytes of "
            f"{'teal code' if isinstance(deployment.create_params.clear_state_program, str) else 'AVM bytecode'}",
            suppress_log=suppress_log,
        )
        note = TransactionComposer.arc2_note(
            {
                "dapp_name": APP_DEPLOY_NOTE_DAPP,
                "format": "j",
                "data": deployment.metadata.dictify(),
            }
        )
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
                suppress_log=suppress_log,
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

        logger.debug("No detected changes in app, nothing to do.", suppress_log=suppress_log)
        return AppDeployResult(
            app=existing_app,
            operation_performed=OperationPerformed.Nothing,
        )

    def _create_app(
        self,
        deployment: AppDeployParams,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeployResult:
        """Create a new application"""

        if isinstance(deployment.create_params, AppCreateMethodCallParams):
            create_result = self._transaction_sender.app_create_method_call(
                AppCreateMethodCallParams(
                    **{
                        **asdict(deployment.create_params),
                        "approval_program": approval_program,
                        "clear_state_program": clear_program,
                    }
                ),
                send_params=deployment.send_params,
            )
        else:
            create_result = self._transaction_sender.app_create(
                AppCreateParams(
                    **{
                        **asdict(deployment.create_params),
                        "approval_program": approval_program,
                        "clear_state_program": clear_program,
                    }
                ),
                send_params=deployment.send_params,
            )

        app_metadata = ApplicationMetaData(
            reference=ApplicationReference(
                app_id=create_result.app_id, app_address=get_application_address(create_result.app_id)
            ),
            deploy_metadata=deployment.metadata,
            created_round=create_result.confirmation.get("confirmed-round", 0)
            if isinstance(create_result.confirmation, dict)
            else 0,
            updated_round=create_result.confirmation.get("confirmed-round", 0)
            if isinstance(create_result.confirmation, dict)
            else 0,
            deleted=False,
        )

        self._update_app_lookup(deployment.create_params.sender, app_metadata)

        return AppDeployResult(
            app=app_metadata,
            operation_performed=OperationPerformed.Create,
            create_result=create_result,
        )

    def _replace_app(
        self,
        deployment: AppDeployParams,
        existing_app: ApplicationMetaData,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeployResult:
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

        create_result = SendAppCreateTransactionResult[ABIReturn].from_composer_result(result, create_txn_index)
        delete_result = SendAppTransactionResult[ABIReturn].from_composer_result(result, delete_txn_index)

        app_id = int(result.confirmations[0]["application-index"])  # type: ignore[call-overload]
        app_metadata = ApplicationMetaData(
            reference=ApplicationReference(app_id=app_id, app_address=get_application_address(app_id)),
            deploy_metadata=deployment.metadata,
            created_round=result.confirmations[0]["confirmed-round"],  # type: ignore[call-overload]
            updated_round=result.confirmations[0]["confirmed-round"],  # type: ignore[call-overload]
            deleted=False,
        )
        self._update_app_lookup(deployment.create_params.sender, app_metadata)

        return AppDeployResult(
            app=app_metadata,
            operation_performed=OperationPerformed.Replace,
            create_result=create_result,
            update_result=None,
            delete_result=delete_result,
        )

    def _update_app(
        self,
        deployment: AppDeployParams,
        existing_app: ApplicationMetaData,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeployResult:
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
                ),
                send_params=deployment.send_params,
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
                ),
                send_params=deployment.send_params,
            )

        app_metadata = ApplicationMetaData(
            reference=ApplicationReference(app_id=existing_app.app_id, app_address=existing_app.app_address),
            deploy_metadata=deployment.metadata,
            created_round=existing_app.created_round,
            updated_round=result.confirmation.get("confirmed-round", 0) if isinstance(result.confirmation, dict) else 0,
            deleted=False,
        )

        self._update_app_lookup(deployment.create_params.sender, app_metadata)

        return AppDeployResult(
            app=app_metadata,
            operation_performed=OperationPerformed.Update,
            update_result=result,
        )

    def _handle_schema_break(
        self,
        deployment: AppDeployParams,
        existing_app: ApplicationMetaData,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeployResult:
        if deployment.on_schema_break in (OnSchemaBreak.Fail, "fail") or deployment.on_schema_break is None:
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
        existing_app: ApplicationMetaData,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeployResult:
        if deployment.on_update in (OnUpdate.Fail, "fail") or deployment.on_update is None:
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

    def _update_app_lookup(self, sender: str, app_metadata: ApplicationMetaData) -> None:
        """Update the app lookup cache"""

        lookup = self._app_lookups.get(sender)
        if not lookup:
            self._app_lookups[sender] = ApplicationLookup(
                creator=sender,
                apps={app_metadata.name: app_metadata},
            )
        else:
            lookup.apps[app_metadata.name] = app_metadata

    def get_creator_apps_by_name(self, *, creator_address: str, ignore_cache: bool = False) -> ApplicationLookup:
        """Get apps created by an account"""

        if not ignore_cache and creator_address in self._app_lookups:
            return self._app_lookups[creator_address]

        if not self._indexer:
            raise ValueError(
                "Didn't receive an indexer client when this AppManager was created, "
                "but received a call to get_creator_apps"
            )

        app_lookup: dict[str, ApplicationMetaData] = {}

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
                note_prefix=APP_DEPLOY_NOTE_DAPP.encode(),
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
                    app_lookup[metadata["name"]] = ApplicationMetaData(
                        reference=ApplicationReference(app_id=app_id, app_address=get_application_address(app_id)),
                        deploy_metadata=AppDeploymentMetaData(
                            name=metadata["name"],
                            version=metadata.get("version", "1.0"),
                            deletable=metadata.get("deletable"),
                            updatable=metadata.get("updatable"),
                        ),
                        created_round=creation_txn["confirmed-round"],
                        updated_round=creation_txn["confirmed-round"],
                        deleted=app.get("deleted", False),
                    )
            except Exception as e:
                logger.warning(
                    f"Error processing app {app_id} for creator {creator_address}: {e}",
                )
                continue

        lookup = ApplicationLookup(creator=creator_address, apps=app_lookup)
        self._app_lookups[creator_address] = lookup
        return lookup
