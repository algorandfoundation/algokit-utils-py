import base64
import dataclasses
import json
import logging
from dataclasses import dataclass
from typing import Any, Literal

from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.logic import get_application_address
from algosdk.v2client.indexer import IndexerClient

from algokit_utils._legacy_v2.deploy import (
    AppDeployMetaData,
    AppLookup,
    AppMetaData,
    OnSchemaBreak,
    OnUpdate,
)
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.models.abi import ABIValue
from algokit_utils.transactions.transaction_composer import (
    AppCreateMethodCall,
    AppCreateParams,
    AppDeleteMethodCall,
    AppDeleteParams,
    AppUpdateMethodCall,
)
from algokit_utils.transactions.transaction_sender import (
    AlgorandClientTransactionSender,
    SendAppTransactionResult,
)

APP_DEPLOY_NOTE_DAPP = "algokit_deployer"

logger = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class DeployAppUpdateParams:
    """Parameters for an update transaction in app deployment"""

    sender: str
    signer: TransactionSigner | None = None
    args: list[bytes] | None = None
    note: bytes | None = None
    lease: bytes | None = None
    rekey_to: str | None = None
    boxes: list[tuple[int, bytes]] | None = None
    accounts: list[str] | None = None
    foreign_apps: list[int] | None = None
    foreign_assets: list[int] | None = None


@dataclass(frozen=True, kw_only=True)
class DeployAppDeleteParams:
    """Parameters for a delete transaction in app deployment"""

    sender: str
    signer: TransactionSigner | None = None
    note: bytes | None = None
    lease: bytes | None = None
    rekey_to: str | None = None
    boxes: list[tuple[int, bytes]] | None = None
    accounts: list[str] | None = None
    foreign_apps: list[int] | None = None
    foreign_assets: list[int] | None = None


@dataclass(frozen=True, kw_only=True)
class AppDeployParams:
    """Parameters for deploying an app"""

    metadata: AppDeployMetaData
    deploy_time_params: dict[str, Any] | None = None
    on_schema_break: Literal["replace", "fail", "append"] | OnSchemaBreak = OnSchemaBreak.Fail
    on_update: Literal["update", "replace", "fail", "append"] | OnUpdate = OnUpdate.Fail
    create_params: AppCreateParams | AppCreateMethodCall
    update_params: DeployAppUpdateParams | AppUpdateMethodCall
    delete_params: DeployAppDeleteParams | AppDeleteMethodCall
    existing_deployments: AppLookup | None = None
    ignore_cache: bool = False
    max_fee: int | None = None
    max_rounds_to_wait: int | None = None
    suppress_log: bool = False


@dataclass(frozen=True)
class AppDeploymentResult:
    operation_performed: Literal["create", "update", "replace", "nothing"]
    app_id: int
    app_address: str
    transaction: transaction.Transaction | None = None
    confirmation: dict[str, Any] | None = None
    return_value: ABIValue | None = None
    delete_return: ABIValue | None = None
    delete_result: dict[str, Any] | None = None


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

    def deploy(self, deployment: AppDeployParams) -> AppDeploymentResult | SendAppTransactionResult:
        # Create new instances with updated notes
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
            deployment.create_params.sender,
            deployment.ignore_cache,
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

        return AppDeploymentResult(
            operation_performed="nothing",
            app_id=existing_app.app_id,
            app_address=existing_app.app_address,
        )

    def _create_app(
        self,
        deployment: AppDeployParams,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeploymentResult:
        """Create a new application"""

        if isinstance(deployment.create_params, AppCreateMethodCall):
            create_params = AppCreateMethodCall(
                **{
                    **deployment.create_params.__dict__,
                    "approval_program": approval_program,
                    "clear_state_program": clear_program,
                }
            )
            result = self._transaction_sender.app_create_method_call(create_params)
        else:
            create_params = AppCreateParams(
                **{
                    **deployment.create_params.__dict__,
                    "approval_program": approval_program,
                    "clear_state_program": clear_program,
                }
            )
            result = self._transaction_sender.app_create(create_params)

        app_metadata = AppMetaData(
            app_id=result.app_id,
            app_address=get_application_address(result.app_id),
            **deployment.metadata.__dict__,
            created_metadata=deployment.metadata,
            created_round=result.confirmation["confirmed-round"],
            updated_round=result.confirmation["confirmed-round"],
            deleted=False,
        )

        self._update_app_lookup(deployment.create_params.sender, app_metadata)

        return AppDeploymentResult(
            operation_performed="create",
            app_id=result.app_id,
            app_address=get_application_address(result.app_id),
            transaction=result.transaction,
            confirmation=result.confirmation,
            return_value=result.return_value,
        )

    def _handle_schema_break(
        self,
        deployment: AppDeployParams,
        existing_app: AppMetaData,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeploymentResult:
        if deployment.on_schema_break in (OnSchemaBreak.Fail, "fail"):
            raise ValueError(
                "Schema break detected and onSchemaBreak=OnSchemaBreak.Fail, stopping deployment. "
                "If you want to try deleting and recreating the app then "
                "re-run with onSchemaBreak=OnSchemaBreak.ReplaceApp"
            )

        if deployment.on_schema_break in (OnSchemaBreak.AppendApp, "append"):
            return self._create_app(deployment, approval_program, clear_program)

        if existing_app.deletable:
            return self._create_and_delete_app(deployment, existing_app, approval_program, clear_program)
        else:
            raise ValueError("App is not deletable but onSchemaBreak=ReplaceApp, " "cannot delete and recreate app")

    def _handle_update(
        self,
        deployment: AppDeployParams,
        existing_app: AppMetaData,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeploymentResult:
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
                return self._create_and_delete_app(deployment, existing_app, approval_program, clear_program)
            else:
                raise ValueError("App is not deletable but onUpdate=ReplaceApp, " "cannot delete and recreate app")

        raise ValueError(f"Unsupported onUpdate value: {deployment.on_update}")

    def _create_and_delete_app(
        self,
        deployment: AppDeployParams,
        existing_app: AppMetaData,
        approval_program: bytes,
        clear_program: bytes,
    ) -> AppDeploymentResult:
        composer = self._transaction_sender.new_group()

        # Add create transaction
        if isinstance(deployment.create_params, AppCreateMethodCall):
            create_params = AppCreateMethodCall(
                **{
                    **deployment.create_params.__dict__,
                    "approval_program": approval_program,
                    "clear_state_program": clear_program,
                }
            )
            composer.add_app_create_method_call(create_params)
        else:
            create_params = AppCreateParams(
                **{
                    **deployment.create_params.__dict__,
                    "approval_program": approval_program,
                    "clear_state_program": clear_program,
                }
            )
            composer.add_app_create(create_params)

        # Add delete transaction
        if isinstance(deployment.delete_params, AppDeleteMethodCall):
            delete_params = AppDeleteMethodCall(
                **{
                    **deployment.delete_params.__dict__,
                    "app_id": existing_app.app_id,
                }
            )
            composer.add_app_delete_method_call(delete_params)
        else:
            delete_params = AppDeleteParams(
                **{
                    **deployment.delete_params.__dict__,
                    "app_id": existing_app.app_id,
                }
            )
            composer.add_app_delete(delete_params)

        result = composer.send()

        app_id = int(result.confirmations[0]["application-index"])
        app_metadata = AppMetaData(
            app_id=app_id,
            app_address=get_application_address(app_id),
            **deployment.metadata.__dict__,
            created_metadata=deployment.metadata,
            created_round=result.confirmations[0]["confirmed-round"],
            updated_round=result.confirmations[0]["confirmed-round"],
            deleted=False,
        )
        self._update_app_lookup(deployment.create_params.sender, app_metadata)

        return AppDeploymentResult(
            operation_performed="replace",
            app_id=app_id,
            app_address=get_application_address(app_id),
            transaction=result.transactions[0],
            confirmation=result.confirmations[0],
            return_value=result.returns[0] if result.returns else None,
            delete_return=result.returns[-1] if len(result.returns) > 1 else None,
            delete_result={
                "transaction": result.transactions[-1],
                "confirmation": result.confirmations[-1],
            },
        )

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

    def get_creator_apps_by_name(self, creator_address: str, ignore_cache: bool = False) -> AppLookup:
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
                logger.warning(f"Error processing app {app_id} for creator {creator_address}: {e}")
                continue

        lookup = AppLookup(creator=creator_address, apps=app_lookup)
        self._app_lookups[creator_address] = lookup
        return lookup
