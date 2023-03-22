import base64
import dataclasses
import logging
import re
from collections.abc import Sequence
from enum import Enum
from math import ceil
from typing import Any, cast, overload

import algosdk
from algosdk import transaction
from algosdk.abi import ABIType, Method, Returns
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import (
    ABI_RETURN_HASH,
    ABIResult,
    AccountTransactionSigner,
    AtomicTransactionComposer,
    AtomicTransactionResponse,
    LogicSigTransactionSigner,
    MultisigTransactionSigner,
    TransactionSigner,
    TransactionWithSigner,
)
from algosdk.constants import APP_PAGE_MAX_SIZE
from algosdk.logic import get_application_address
from algosdk.source_map import SourceMap
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from algokit_utils.app import (
    DELETABLE_TEMPLATE_NAME,
    UPDATABLE_TEMPLATE_NAME,
    AppDeployMetaData,
    AppLookup,
    AppMetaData,
    AppReference,
    DeploymentFailedError,
    TemplateValueDict,
    _add_deploy_template_variables,
    _check_template_variables,
    _schema_is_less,
    _schema_str,
    _state_schema,
    _strip_comments,
    get_creator_apps,
    replace_template_variables,
)
from algokit_utils.application_specification import (
    ApplicationSpecification,
    CallConfig,
    DefaultArgumentDict,
    MethodConfigDict,
    MethodHints,
    OnCompleteActionName,
)
from algokit_utils.logic_error import LogicError, parse_logic_error
from algokit_utils.models import Account

logger = logging.getLogger(__name__)

ABIArgsDict = dict[str, Any]

__all__ = [
    "ABICallArgs",
    "ApplicationClient",
    "DeployResponse",
    "OnUpdate",
    "OnSchemaBreak",
    "OperationPerformed",
    "Program",
    "TransactionResponse",
    "get_app_id_from_tx_id",
    "get_next_version",
    "num_extra_program_pages",
]


class Program:
    """A compiled TEAL program"""

    def __init__(self, program: str, client: AlgodClient):
        """
        Fully compile the program source to binary and generate a
        source map for matching pc to line number
        """
        self.teal = program
        result: dict = client.compile(self.teal, source_map=True)
        self.raw_binary = base64.b64decode(result["result"])
        self.binary_hash: str = result["hash"]
        self.source_map = SourceMap(result["sourcemap"])


def num_extra_program_pages(approval: bytes, clear: bytes) -> int:
    return ceil(((len(approval) + len(clear)) - APP_PAGE_MAX_SIZE) / APP_PAGE_MAX_SIZE)


@dataclasses.dataclass(kw_only=True)
class ABICallArgs:
    method: Method | str | bool | None
    args: ABIArgsDict = dataclasses.field(default_factory=dict)
    bare: bool = False
    lease: str | bytes | None = dataclasses.field(default=None)


class OnUpdate(Enum):
    Fail = 0
    UpdateApp = 1
    ReplaceApp = 2
    # TODO: AppendApp


class OnSchemaBreak(Enum):
    Fail = 0
    ReplaceApp = 2


class OperationPerformed(Enum):
    Nothing = 0
    Create = 1
    Update = 2
    Replace = 3


@dataclasses.dataclass
class DeployResponse:
    app: AppMetaData
    action_taken: OperationPerformed = OperationPerformed.Nothing


@dataclasses.dataclass(kw_only=True)
class TransactionResponse:
    tx_id: str
    abi_result: ABIResult | None
    confirmed_round: int | None = None


class ApplicationClient:
    @overload
    def __init__(
        self,
        algod_client: AlgodClient,
        app_spec: ApplicationSpecification,
        *,
        app_id: int = 0,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
    ):
        ...

    @overload
    def __init__(
        self,
        algod_client: AlgodClient,
        app_spec: ApplicationSpecification,
        *,
        creator: str | Account,
        indexer_client: IndexerClient | None = None,
        existing_deployments: AppLookup | None = None,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
    ):
        ...

    def __init__(
        self,
        algod_client: AlgodClient,
        app_spec: ApplicationSpecification,
        *,
        app_id: int = 0,
        creator: str | Account | None = None,
        indexer_client: IndexerClient | None = None,
        existing_deployments: AppLookup | None = None,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
    ):
        self.algod_client = algod_client
        self.app_spec = app_spec
        self._approval_program: Program | None = None
        self._clear_program: Program | None = None
        self._approval_source_map: SourceMap | None = None
        self.existing_deployments = existing_deployments
        self._indexer_client = indexer_client
        if creator is not None:
            if not self.existing_deployments and not self._indexer_client:
                raise Exception(
                    "If using the creator parameter either existing_deployments or indexer_client must also be provided"
                )
            self._creator: str | None = creator.address if isinstance(creator, Account) else creator
            if self.existing_deployments and self.existing_deployments.creator != self._creator:
                raise Exception(
                    "Attempt to create application client with invalid existing_deployments against"
                    f"a different creator ({self.existing_deployments.creator} instead of "
                    f"expected creator {self._creator}"
                )
            self.app_id = 0
        else:
            self.app_id = app_id
            self._creator = None

        self.signer: TransactionSigner | None
        if signer:
            self.signer = (
                signer if isinstance(signer, TransactionSigner) else AccountTransactionSigner(signer.private_key)
            )
        elif isinstance(creator, Account):
            self.signer = AccountTransactionSigner(creator.private_key)
        else:
            self.signer = None
        self.sender = sender
        self.suggested_params = suggested_params

    @property
    def app_address(self) -> str:
        return get_application_address(self.app_id)

    # TODO: source map changes
    @property
    def approval(self) -> Program:
        if not self._approval_program:
            self._approval_program = Program(self.app_spec.approval_program, self.algod_client)
        return self._approval_program

    @property
    def clear(self) -> Program:
        if not self._clear_program:
            self._clear_program = Program(self.app_spec.clear_program, self.algod_client)
        return self._clear_program

    def deploy(
        self,
        version: str | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        allow_update: bool | None = None,
        allow_delete: bool | None = None,
        on_update: OnUpdate = OnUpdate.Fail,
        on_schema_break: OnSchemaBreak = OnSchemaBreak.Fail,
        template_values: TemplateValueDict | None = None,
        create_args: ABICallArgs | None = None,
        update_args: ABICallArgs | None = None,
        delete_args: ABICallArgs | None = None,
    ) -> DeployResponse:
        """Ensures app associated with app client's creator is present and up to date"""
        if self.app_id:
            raise DeploymentFailedError(f"Attempt to deploy app which already has an app index of {self.app_id}")
        signer, sender = self._resolve_signer_sender(signer, sender)
        if not sender:
            raise DeploymentFailedError("No sender provided, unable to deploy app")
        if not self._creator:
            raise DeploymentFailedError("No creator provided, unable to deploy app")
        if self._creator != sender:
            raise DeploymentFailedError(
                f"Attempt to deploy contract with a sender address {sender} that differs "
                f"from the given creator address for this application client: {self._creator}"
            )
        # make a copy
        template_values = template_values or {}
        _add_deploy_template_variables(template_values, allow_update=allow_update, allow_delete=allow_delete)
        approval_program, clear_program = self._substitute_template_and_compile(template_values)

        updatable = (
            allow_update
            if allow_update is not None
            else _get_deploy_control(self.app_spec, UPDATABLE_TEMPLATE_NAME, transaction.OnComplete.UpdateApplicationOC)
        )
        deletable = (
            allow_delete
            if allow_delete is not None
            else _get_deploy_control(self.app_spec, DELETABLE_TEMPLATE_NAME, transaction.OnComplete.DeleteApplicationOC)
        )

        name = self.app_spec.contract.name

        # TODO: allow resolve app id via environment variable
        app = self._load_app_reference()

        if version is None:
            if app.app_id == 0:
                version = "v1.0"
            else:
                assert isinstance(app, AppDeployMetaData)
                version = get_next_version(app.version)
        app_spec_note = AppDeployMetaData(name, version, updatable=updatable, deletable=deletable)

        def unpack_args(
            args: ABICallArgs | None,
        ) -> tuple[Method | str | bool | None, ABIArgsDict | None, bytes | None]:
            if args is None:
                return None, None, None
            return args.method, args.args, args.lease.encode("utf-8") if isinstance(args.lease, str) else args.lease

        def create_metadata(
            created_round: int, updated_round: int | None = None, original_metadata: AppDeployMetaData | None = None
        ) -> AppMetaData:
            app_metadata = AppMetaData(
                app_id=self.app_id,
                app_address=self.app_address,
                created_metadata=original_metadata or app_spec_note,
                created_round=created_round,
                updated_round=updated_round or created_round,
                **app_spec_note.__dict__,
                deleted=False,
            )
            return app_metadata

        def create_app() -> DeployResponse:
            assert self.existing_deployments
            method, args, lease = unpack_args(create_args)
            create_result = self.create(
                abi_method=method,
                args=args,
                note=app_spec_note.encode(),
                signer=signer,
                sender=sender,
                template_values=template_values,
                lease=lease,
            )
            logger.info(f"{name} ({version}) deployed successfully, with app id {self.app_id}.")
            assert create_result.confirmed_round is not None
            app_metadata = create_metadata(create_result.confirmed_round)
            self.existing_deployments.apps[name] = app_metadata
            return DeployResponse(app_metadata, action_taken=OperationPerformed.Create)

        if app.app_id == 0:
            logger.info(f"{name} not found in {self._creator} account, deploying app.")
            return create_app()

        assert isinstance(app, AppMetaData)
        logger.debug(f"{name} found in {self._creator} account, with app id {app.app_id}, version={app.version}.")

        application_info = cast(dict[str, Any], self.algod_client.application_info(app.app_id))
        application_create_params = application_info["params"]

        current_approval = base64.b64decode(application_create_params["approval-program"])
        current_clear = base64.b64decode(application_create_params["clear-state-program"])
        current_global_schema = _state_schema(application_create_params["global-state-schema"])
        current_local_schema = _state_schema(application_create_params["local-state-schema"])

        required_global_schema = self.app_spec.global_state_schema
        required_local_schema = self.app_spec.local_state_schema
        new_approval = approval_program.raw_binary
        new_clear = clear_program.raw_binary

        app_updated = current_approval != new_approval or current_clear != new_clear

        schema_breaking_change = _schema_is_less(current_global_schema, required_global_schema) or _schema_is_less(
            current_local_schema, required_local_schema
        )

        def create_and_delete_app() -> DeployResponse:
            assert isinstance(app, AppMetaData)
            assert self.existing_deployments
            logger.info(f"Replacing {name} ({app.version}) with {name} ({version}) in {self._creator} account.")
            create_method, c_args, create_lease = unpack_args(create_args)
            delete_method, d_args, delete_lease = unpack_args(delete_args)
            atc = AtomicTransactionComposer()
            self.compose_create(
                atc,
                abi_method=create_method,
                args=c_args,
                note=app_spec_note.encode(),
                signer=signer,
                sender=sender,
                template_values=template_values,
                lease=create_lease,
            )
            self.compose_delete(
                atc,
                abi_method=delete_method,
                args=d_args,
                signer=signer,
                sender=sender,
                lease=delete_lease,
            )
            create_delete_result = self._execute_atc(atc)
            self._set_app_id_from_tx_id(create_delete_result.tx_ids[0])
            logger.info(f"{name} ({version}) deployed successfully, with app id {self.app_id}.")
            logger.info(f"{name} ({app.version}) with app id {app.app_id}, deleted successfully.")

            app_metadata = create_metadata(create_delete_result.confirmed_round)
            self.existing_deployments.apps[name] = app_metadata
            # TODO: include transaction responses
            return DeployResponse(app_metadata, action_taken=OperationPerformed.Replace)

        def update_app() -> DeployResponse:
            assert on_update == OnUpdate.UpdateApp
            assert isinstance(app, AppMetaData)
            assert self.existing_deployments
            logger.info(f"Updating {name} to {version} in {self._creator} account, with app id {app.app_id}")
            method, args, lease = unpack_args(update_args)
            update_result = self.update(
                abi_method=method,
                args=args,
                note=app_spec_note.encode(),
                signer=signer,
                sender=sender,
                template_values=template_values,
                lease=lease,
            )
            app_metadata = create_metadata(
                app.created_round, updated_round=update_result.confirmed_round, original_metadata=app.created_metadata
            )
            self.existing_deployments.apps[name] = app_metadata
            return DeployResponse(app_metadata, action_taken=OperationPerformed.Update)

        if schema_breaking_change:
            logger.warning(
                f"Detected a breaking app schema change from: "
                f"{_schema_str(current_global_schema, current_local_schema)} to "
                f"{_schema_str(required_global_schema, required_local_schema)}."
            )

            if on_schema_break == OnSchemaBreak.Fail:
                raise DeploymentFailedError(
                    "Schema break detected and on_schema_break=OnSchemaBreak.Fail, stopping deployment. "
                    "If you want to try deleting and recreating the app then "
                    "re-run with on_schema_break=OnSchemaBreak.ReplaceApp"
                )
            if app.deletable:
                logger.info(
                    "App is deletable and on_schema_break=ReplaceApp, will attempt to create new app and delete old app"
                )
            elif app.deletable is False:
                logger.warning(
                    "App is not deletable but on_schema_break=ReplaceApp, "
                    "will attempt to delete app, delete will most likely fail"
                )
            else:
                logger.warning(
                    "Cannot determine if App is deletable but on_schema_break=ReplaceApp, " "will attempt to delete app"
                )
            return create_and_delete_app()
        elif app_updated:
            logger.info(f"Detected a TEAL update in app id {app.app_id}")

            if on_update == OnUpdate.Fail:
                raise DeploymentFailedError(
                    "Update detected and on_update=Fail, stopping deployment. "
                    "If you want to try updating the app then re-run with on_update=UpdateApp"
                )
            if app.updatable and on_update == OnUpdate.UpdateApp:
                logger.info("App is updatable and on_update=UpdateApp, will update app")
                return update_app()
            elif app.updatable and on_update == OnUpdate.ReplaceApp:
                logger.warning(
                    "App is updatable but on_update=ReplaceApp, will attempt to create new app and delete old app"
                )
                return create_and_delete_app()
            elif on_update == OnUpdate.ReplaceApp:
                if app.updatable is False:
                    logger.warning(
                        "App is not updatable and on_update=ReplaceApp, "
                        "will attempt to create new app and delete old app"
                    )
                else:
                    logger.warning(
                        "Cannot determine if App is updatable and on_update=ReplaceApp, "
                        "will attempt to create new app and delete old app"
                    )
                return create_and_delete_app()
            else:
                if app.updatable is False:
                    logger.warning(
                        "App is not updatable but on_update=UpdateApp, "
                        "will attempt to update app, update will most likely fail"
                    )
                else:
                    logger.warning(
                        "Cannot determine if App is updatable and on_update=UpdateApp, " "will attempt to update app"
                    )
                return update_app()

        logger.info("No detected changes in app, nothing to do.")

        return DeployResponse(app)

    def compose_create(
        self,
        atc: AtomicTransactionComposer,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        on_complete: transaction.OnComplete = transaction.OnComplete.NoOpOC,
        template_values: TemplateValueDict | None = None,
        extra_pages: int | None = None,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> None:
        """Adds a signed transaction with application id == 0 and the schema and source of client's app_spec to atc"""

        approval_program, clear_program = self._substitute_template_and_compile(template_values)

        if extra_pages is None:
            extra_pages = num_extra_program_pages(approval_program.raw_binary, clear_program.raw_binary)

        create_method = self._resolve_method(abi_method, args, on_complete, CallConfig.CREATE)
        self._add_method_call(
            atc,
            app_id=0,
            method=create_method,
            abi_args=args,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            on_complete=on_complete,
            approval_program=approval_program.raw_binary,
            clear_program=clear_program.raw_binary,
            global_schema=self.app_spec.global_state_schema,
            local_schema=self.app_spec.local_state_schema,
            extra_pages=extra_pages,
            note=note,
            lease=lease,
        )

    def create(
        self,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        on_complete: transaction.OnComplete = transaction.OnComplete.NoOpOC,
        template_values: TemplateValueDict | None = None,
        extra_pages: int | None = None,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> TransactionResponse:
        """Submits a signed transaction with application id == 0 and the schema and source of client's app_spec"""

        atc = AtomicTransactionComposer()

        self.compose_create(
            atc,
            abi_method,
            args,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            on_complete=on_complete,
            template_values=template_values,
            extra_pages=extra_pages,
            note=note,
            lease=lease,
        )
        create_result = self._execute_atc_tr(atc)
        self._set_app_id_from_tx_id(create_result.tx_id)
        return create_result

    def compose_update(
        self,
        atc: AtomicTransactionComposer,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        template_values: TemplateValueDict | None = None,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> None:
        """Adds a signed transaction with on_complete=UpdateApplication to atc"""

        self._load_reference_and_check_app_id()
        approval_program, clear_program = self._substitute_template_and_compile(template_values)

        update_method = self._resolve_method(abi_method, args, transaction.OnComplete.UpdateApplicationOC)
        self._add_method_call(
            atc=atc,
            method=update_method,
            abi_args=args,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            on_complete=transaction.OnComplete.UpdateApplicationOC,
            approval_program=approval_program.raw_binary,
            clear_program=clear_program.raw_binary,
            note=note,
            lease=lease,
        )

    def update(
        self,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        template_values: TemplateValueDict | None = None,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> TransactionResponse:
        """Submits a signed transaction with on_complete=UpdateApplication"""

        atc = AtomicTransactionComposer()
        self.compose_update(
            atc,
            abi_method,
            args,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            template_values=template_values,
            note=note,
            lease=lease,
        )
        return self._execute_atc_tr(atc)

    def compose_delete(
        self,
        atc: AtomicTransactionComposer,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        lease: bytes | None = None,
    ) -> None:
        """Adds a signed transaction with on_complete=DeleteApplication to atc"""

        delete_method = self._resolve_method(abi_method, args, on_complete=transaction.OnComplete.DeleteApplicationOC)
        self.compose_call(
            atc,
            delete_method,
            args,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            on_complete=transaction.OnComplete.DeleteApplicationOC,
            lease=lease,
        )

    def delete(
        self,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        lease: bytes | None = None,
    ) -> TransactionResponse:
        """Submits a signed transaction with on_complete=DeleteApplication"""

        atc = AtomicTransactionComposer()
        self.compose_delete(
            atc,
            abi_method,
            args,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            lease=lease,
        )
        return self._execute_atc_tr(atc)

    def compose_call(
        self,
        atc: AtomicTransactionComposer,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        on_complete: transaction.OnComplete = transaction.OnComplete.NoOpOC,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> None:
        """Adds a signed transaction with specified parameters to atc"""

        self._load_reference_and_check_app_id()
        method = self._resolve_method(abi_method, args, on_complete)
        self._add_method_call(
            atc,
            method=method,
            abi_args=args,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            on_complete=on_complete,
            note=note,
            lease=lease,
        )

    def call(
        self,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        on_complete: transaction.OnComplete = transaction.OnComplete.NoOpOC,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> TransactionResponse:
        """Submits a signed transaction with specified parameters"""

        atc = AtomicTransactionComposer()
        method = self._resolve_method(abi_method, args, on_complete)
        self.compose_call(
            atc,
            abi_method=method,
            args=args,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            on_complete=on_complete,
            note=note,
            lease=lease,
        )

        # If its a read-only method, use dryrun (TODO: swap with simulate later?)
        if method:
            hints = self._method_hints(method)
            if hints and hints.read_only:
                dr_req = transaction.create_dryrun(self.algod_client, atc.gather_signatures())  # type: ignore[arg-type]
                dr_result = self.algod_client.dryrun(dr_req)  # type: ignore[arg-type]
                for txn in dr_result["txns"]:
                    if "app-call-messages" in txn and "REJECT" in txn["app-call-messages"]:
                        msg = ", ".join(txn["app-call-messages"])
                        raise Exception(f"Dryrun for readonly method failed: {msg}")

                method_results = _parse_result({0: method}, dr_result["txns"], atc.tx_ids)
                return TransactionResponse(abi_result=method_results[0], tx_id=atc.tx_ids[0])

        return self._execute_atc_tr(atc)

    def compose_opt_in(
        self,
        atc: AtomicTransactionComposer,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> None:
        """Adds a signed transaction with on_complete=OptIn to atc"""
        self.compose_call(
            atc,
            abi_method=abi_method,
            args=args,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            on_complete=transaction.OnComplete.OptInOC,
            note=note,
            lease=lease,
        )

    def opt_in(
        self,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> TransactionResponse:
        """Submits a signed transaction with on_complete=OptIn"""
        atc = AtomicTransactionComposer()
        self.compose_opt_in(
            atc,
            abi_method=abi_method,
            args=args,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            note=note,
            lease=lease,
        )
        return self._execute_atc_tr(atc)

    def compose_close_out(
        self,
        atc: AtomicTransactionComposer,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> None:
        """Adds a signed transaction with on_complete=CloseOut to ac"""
        return self.compose_call(
            atc,
            abi_method=abi_method,
            args=args,
            signer=signer,
            sender=sender,
            on_complete=transaction.OnComplete.CloseOutOC,
            suggested_params=suggested_params,
            note=note,
            lease=lease,
        )

    def close_out(
        self,
        abi_method: Method | str | bool | None = None,
        args: ABIArgsDict | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> TransactionResponse:
        """Submits a signed transaction with on_complete=CloseOut"""
        atc = AtomicTransactionComposer()
        self.compose_close_out(
            atc,
            abi_method=abi_method,
            args=args,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            note=note,
            lease=lease,
        )
        return self._execute_atc_tr(atc)

    def compose_clear_state(
        self,
        atc: AtomicTransactionComposer,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> None:
        """Adds a signed transaction with on_complete=ClearState to atc"""
        return self.compose_call(
            atc,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            on_complete=transaction.OnComplete.ClearStateOC,
            note=note,
            lease=lease,
        )

    def clear_state(
        self,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        note: bytes | str | None = None,
        lease: bytes | None = None,
    ) -> TransactionResponse:
        """Submits a signed transaction with on_complete=ClearState"""
        atc = AtomicTransactionComposer()
        self.compose_clear_state(
            atc,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            note=note,
            lease=lease,
        )
        return self._execute_atc_tr(atc)

    def get_global_state(self, *, raw: bool = False) -> dict[bytes | str, bytes | str | int]:
        """gets the global state info for the app id set"""
        global_state = cast(dict[str, Any], self.algod_client.application_info(self.app_id))
        return cast(
            dict[bytes | str, bytes | str | int],
            _decode_state(global_state.get("params", {}).get("global-state", {}), raw=raw),
        )

    def get_local_state(self, account: str | None = None, *, raw: bool = False) -> dict[bytes | str, bytes | str | int]:
        """gets the local state info for the app id set and the account specified"""

        if account is None:
            _, account = self._resolve_signer_sender(self.signer, self.sender)

        acct_state = cast(dict[str, Any], self.algod_client.account_application_info(account, self.app_id))
        return cast(
            dict[bytes | str, bytes | str | int],
            _decode_state(acct_state.get("app-local-state", {}).get("key-value", {}), raw=raw),
        )

    def resolve(self, to_resolve: DefaultArgumentDict) -> int | str | bytes:
        def _data_check(value: Any) -> int | str | bytes:
            if isinstance(value, (str, bytes, bytes)):
                return value
            raise ValueError("Unexpected type for constant data")

        match to_resolve:
            case {"source": "constant", "data": data}:
                return _data_check(data)
            case {"source": "global-state", "data": str() as key}:
                global_state = self.get_global_state(raw=True)
                return global_state[key.encode()]
            case {"source": "local-state", "data": str() as key}:
                _, sender = self._resolve_signer_sender(self.signer, self.sender)
                acct_state = self.get_local_state(sender, raw=True)
                return acct_state[key.encode()]
            case {"source": "abi-method", "data": dict() as method_dict}:
                method = Method.undictify(method_dict)
                response = self.call(method)
                assert isinstance(response, ABIResult)
                return _data_check(response.return_value)

            case {"source": source}:
                raise ValueError(f"Unrecognized default argument source: {source}")
            case _:
                raise TypeError("Unable to interpret default argument specification")

    def _load_reference_and_check_app_id(self) -> None:
        self._load_app_reference()
        self._check_app_id()

    def _load_app_reference(self) -> AppReference | AppMetaData:
        if not self.existing_deployments and self._creator:
            assert self._indexer_client
            self.existing_deployments = get_creator_apps(self._indexer_client, self._creator)

        if self.existing_deployments and self.app_id == 0:
            app = self.existing_deployments.apps.get(self.app_spec.contract.name)
            if app:
                self.app_id = app.app_id
                return app

        return AppReference(self.app_id, self.app_address)

    def _check_app_id(self) -> None:
        if self.app_id == 0:
            raise Exception(
                "ApplicationClient is not associated with an app instance, to resolve either:\n"
                "1.) provide an app_id on construction OR\n"
                "2.) provide a creator address so an app can be searched for OR\n"
                "3.) create an app first using create or deploy methods"
            )

    def _resolve_method(
        self,
        abi_method: Method | str | bool | None,
        args: ABIArgsDict | None,
        on_complete: transaction.OnComplete,
        call_config: CallConfig = CallConfig.CALL,
    ) -> Method | None:
        matches: list[Method | None] = []
        match abi_method:
            case str() | Method():  # abi method specified
                return self._resolve_abi_method(abi_method)
            case bool() | None:  # find abi method
                has_bare_config = call_config in _get_call_config(self.app_spec.bare_call_config, on_complete)
                abi_methods = self._find_abi_methods(args, on_complete, call_config)
                if abi_method is not False:
                    matches += abi_methods
                if has_bare_config and abi_method is not True:
                    matches += [None]

        if len(matches) == 1:  # exact match
            return matches[0]
        elif len(matches) > 1:  # ambiguous match
            signatures = ", ".join((m.get_signature() if isinstance(m, Method) else "bare") for m in matches)
            raise Exception(
                f"Could not find an exact method to use for {on_complete} with call_config of {call_config}, "
                f"specify the exact method using abi_method and args parameters, considered: {signatures}"
            )
        else:  # no match
            raise Exception(f"Could not find any methods to use for {on_complete} with call_config of {call_config}")

    def _substitute_template_and_compile(
        self,
        template_values: TemplateValueDict | None,
    ) -> tuple[Program, Program]:
        template_values = dict(template_values or {})
        clear = replace_template_variables(self.app_spec.clear_program, template_values)

        _check_template_variables(self.app_spec.approval_program, template_values)
        approval = replace_template_variables(self.app_spec.approval_program, template_values)

        self._approval_program = Program(approval, self.algod_client)
        self._clear_program = Program(clear, self.algod_client)
        return self._approval_program, self._clear_program

    def _get_approval_source_map(self) -> SourceMap:
        def _find_template_vars(program: str) -> list[str]:
            pattern = re.compile(r"\bTMPL_(\w*)\b")
            return pattern.findall(program)

        if not self._approval_source_map:
            if self._approval_program:
                self._approval_source_map = self._approval_program.source_map
            else:
                # TODO: this will produce an incorrect source map for bytes as their length is not fixed
                template_values: TemplateValueDict = {k: 0 for k in _find_template_vars(self.app_spec.approval_program)}
                approval_program = replace_template_variables(self.app_spec.approval_program, template_values)
                approval = Program(approval_program, self.algod_client)
                self._approval_source_map = approval.source_map
        return self._approval_source_map

    def _add_method_call(
        self,
        atc: AtomicTransactionComposer,
        method: Method | None = None,
        app_id: int | None = None,
        sender: str | None = None,
        signer: TransactionSigner | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        on_complete: transaction.OnComplete = transaction.OnComplete.NoOpOC,
        local_schema: transaction.StateSchema | None = None,
        global_schema: transaction.StateSchema | None = None,
        approval_program: bytes | None = None,
        clear_program: bytes | None = None,
        extra_pages: int | None = None,
        accounts: list[str] | None = None,
        foreign_apps: list[int] | None = None,
        foreign_assets: list[int] | None = None,
        boxes: Sequence[tuple[int, bytes | bytearray | str | int]] | None = None,
        note: bytes | str | None = None,
        lease: bytes | str | None = None,
        rekey_to: str | None = None,
        abi_args: ABIArgsDict | None = None,
    ) -> AtomicTransactionComposer:
        """Adds a transaction to the AtomicTransactionComposer passed"""
        if app_id is None:
            app_id = self.app_id
        sp = suggested_params or self.suggested_params or self.algod_client.suggested_params()
        signer, sender = self._resolve_signer_sender(signer, sender)
        if boxes is not None:
            # TODO: algosdk actually does this, but it's type hints say otherwise...
            encoded_boxes = [(id_, algosdk.encoding.encode_as_bytes(name)) for id_, name in boxes]
        else:
            encoded_boxes = None

        if lease is not None:
            encoded_lease = lease if isinstance(lease, bytes) else lease.encode("utf-8")
        else:
            encoded_lease = None

        if not method:  # not an abi method, treat as a regular call
            if abi_args:
                raise Exception(f"ABI arguments specified on a bare call: {', '.join(abi_args)}")
            atc.add_transaction(
                TransactionWithSigner(
                    txn=transaction.ApplicationCallTxn(  # type: ignore[no-untyped-call]
                        sender=sender,
                        sp=sp,
                        index=app_id,
                        on_complete=on_complete,
                        approval_program=approval_program,
                        clear_program=clear_program,
                        global_schema=global_schema,
                        local_schema=local_schema,
                        extra_pages=extra_pages,
                        accounts=accounts,
                        foreign_apps=foreign_apps,
                        foreign_assets=foreign_assets,
                        boxes=encoded_boxes,
                        note=note,
                        lease=encoded_lease,
                        rekey_to=rekey_to,
                    ),
                    signer=signer,
                )
            )
        else:  # resolve ABI method args
            hints = self._method_hints(method)

            args: list = []
            abi_args = abi_args or {}
            for method_arg in method.args:
                name = method_arg.name
                if name in abi_args:
                    argument = abi_args.pop(name)
                    if isinstance(argument, dict):
                        if hints.structs is None or name not in hints.structs:
                            raise Exception(f"Argument missing struct hint: {name}. Check argument name and type")

                        elements = hints.structs[name]["elements"]

                        argument_tuple = tuple(argument[field_name] for field_name, field_type in elements)
                        args.append(argument_tuple)
                    else:
                        args.append(argument)

                elif hints.default_arguments is not None and name in hints.default_arguments:
                    default_arg = hints.default_arguments[name]
                    if default_arg is not None:
                        args.append(self.resolve(default_arg))
                else:
                    raise Exception(f"Unspecified argument: {name}")
            if abi_args:
                raise Exception(f"Unused arguments specified: {', '.join(abi_args)}")
            atc.add_method_call(
                app_id,
                method,
                sender,
                sp,
                signer,
                method_args=args,
                on_complete=on_complete,
                local_schema=local_schema,
                global_schema=global_schema,
                approval_program=approval_program,
                clear_program=clear_program,
                extra_pages=extra_pages or 0,
                accounts=accounts,
                foreign_apps=foreign_apps,
                foreign_assets=foreign_assets,
                boxes=encoded_boxes,
                note=note.encode("utf-8") if isinstance(note, str) else note,
                lease=encoded_lease,
                rekey_to=rekey_to,
            )

        return atc

    def _method_matches(
        self, method: Method, args: ABIArgsDict | None, on_complete: transaction.OnComplete, call_config: CallConfig
    ) -> bool:
        hints = self._method_hints(method)
        if call_config not in _get_call_config(hints.call_config, on_complete):
            return False
        method_args = {m.name for m in method.args}
        provided_args = set(args or {}) | set(hints.default_arguments)

        # TODO: also match on types?
        return method_args == provided_args

    def _find_abi_methods(
        self, args: ABIArgsDict | None, on_complete: transaction.OnComplete, call_config: CallConfig
    ) -> list[Method]:
        return [
            method
            for method in self.app_spec.contract.methods
            if self._method_matches(method, args, on_complete, call_config)
        ]

    def _resolve_abi_method(self, method: Method | str) -> Method:
        if isinstance(method, str):
            try:
                return next(iter(m for m in self.app_spec.contract.methods if m.get_signature() == method))
            except StopIteration:
                pass
            return self.app_spec.contract.get_method_by_name(method)
        else:
            return method

    def _method_hints(self, method: Method) -> MethodHints:
        sig = method.get_signature()
        if sig not in self.app_spec.hints:
            return MethodHints()
        return self.app_spec.hints[sig]

    def _execute_atc_tr(self, atc: AtomicTransactionComposer) -> TransactionResponse:
        result = self._execute_atc(atc)
        return TransactionResponse(
            tx_id=result.tx_ids[0],
            abi_result=result.abi_results[0] if result.abi_results else None,
            confirmed_round=result.confirmed_round,
        )

    def _execute_atc(self, atc: AtomicTransactionComposer, wait_rounds: int = 4) -> AtomicTransactionResponse:
        try:
            return atc.execute(self.algod_client, wait_rounds=wait_rounds)
        except Exception as ex:
            logic_error_data = parse_logic_error(str(ex))
            if logic_error_data is not None:
                source_map = self._get_approval_source_map()
                if source_map:
                    raise LogicError(
                        logic_error=ex,
                        program=self.app_spec.approval_program,
                        source_map=source_map,
                        **logic_error_data,
                    ) from ex
            raise ex

    def _set_app_id_from_tx_id(self, tx_id: str) -> None:
        self.app_id = get_app_id_from_tx_id(self.algod_client, tx_id)

    def _resolve_signer_sender(
        self, signer: TransactionSigner | None, sender: str | None
    ) -> tuple[TransactionSigner, str]:
        resolved_signer = signer or self.signer
        if not resolved_signer:
            raise Exception("No signer specified")
        if sender is not None:
            resolved_sender = sender
        elif signer is None and self.sender is not None:
            resolved_sender = self.sender
        else:
            resolved_sender = _get_sender_from_signer(resolved_signer)
        return resolved_signer, resolved_sender


def get_app_id_from_tx_id(algod_client: AlgodClient, tx_id: str) -> int:
    result = cast(dict[str, Any], algod_client.pending_transaction_info(tx_id))
    return cast(int, result["application-index"])


def get_next_version(current_version: str) -> str:
    pattern = re.compile(r"(?P<prefix>\w*)(?P<version>(?:\d+\.)*\d+)(?P<suffix>\w*)")
    match = pattern.match(current_version)
    if match:
        version = match.group("version")
        new_version = _increment_version(version)

        def replacement(m: re.Match) -> str:
            return f"{m.group('prefix')}{new_version}{m.group('suffix')}"

        return re.sub(pattern, replacement, current_version)
    raise DeploymentFailedError(
        f"Could not auto increment {current_version}, please specify the next version using the version parameter"
    )


def _get_sender_from_signer(signer: TransactionSigner) -> str:
    if isinstance(signer, AccountTransactionSigner):
        return cast(str, address_from_private_key(signer.private_key))  # type: ignore[no-untyped-call]
    elif isinstance(signer, MultisigTransactionSigner):
        return cast(str, signer.msig.address())  # type: ignore[no-untyped-call]
    elif isinstance(signer, LogicSigTransactionSigner):
        return signer.lsig.address()
    else:
        raise Exception(f"Cannot determine sender from {signer}")


# TEMPORARY, use SDK one when available
def _parse_result(
    methods: dict[int, Method],
    txns: list[dict[str, Any]],
    txids: list[str],
) -> list[ABIResult]:
    method_results = []
    for i, tx_info in enumerate(txns):
        raw_value = b""
        return_value = None
        decode_error = None

        if i not in methods:
            continue

        # Parse log for ABI method return value
        try:
            if methods[i].returns.type == Returns.VOID:
                method_results.append(
                    ABIResult(
                        tx_id=txids[i],
                        raw_value=raw_value,
                        return_value=return_value,
                        decode_error=decode_error,
                        tx_info=tx_info,
                        method=methods[i],
                    )
                )
                continue

            logs = tx_info["logs"] if "logs" in tx_info else []

            # Look for the last returned value in the log
            if not logs:
                raise Exception("No logs")

            result = logs[-1]
            # Check that the first four bytes is the hash of "return"
            result_bytes = base64.b64decode(result)
            if len(result_bytes) < 4 or result_bytes[:4] != ABI_RETURN_HASH:
                raise Exception("no logs")

            raw_value = result_bytes[4:]
            abi_return_type = methods[i].returns.type
            if isinstance(abi_return_type, ABIType):
                return_value = abi_return_type.decode(raw_value)
            else:
                return_value = raw_value

        except Exception as e:
            decode_error = e

        method_results.append(
            ABIResult(
                tx_id=txids[i],
                raw_value=raw_value,
                return_value=return_value,
                decode_error=decode_error,
                tx_info=tx_info,
                method=methods[i],
            )
        )

    return method_results


def _increment_version(version: str) -> str:
    split = list(map(int, version.split(".")))
    split[-1] = split[-1] + 1
    return ".".join(str(x) for x in split)


def _get_call_config(method_config: MethodConfigDict, on_complete: transaction.OnComplete) -> CallConfig:
    def get(key: OnCompleteActionName) -> CallConfig:
        return method_config.get(key, CallConfig.NEVER)

    match on_complete:
        case transaction.OnComplete.NoOpOC:
            return get("no_op")
        case transaction.OnComplete.UpdateApplicationOC:
            return get("update_application")
        case transaction.OnComplete.DeleteApplicationOC:
            return get("delete_application")
        case transaction.OnComplete.OptInOC:
            return get("opt_in")
        case transaction.OnComplete.CloseOutOC:
            return get("close_out")
        case transaction.OnComplete.ClearStateOC:
            return get("clear_state")


def _str_or_hex(v: bytes) -> str:
    decoded: str
    try:
        decoded = v.decode("utf-8")
    except UnicodeDecodeError:
        decoded = v.hex()

    return decoded


def _decode_state(state: list[dict[str, Any]], *, raw: bool = False) -> dict[str | bytes, bytes | str | int | None]:
    decoded_state: dict[str | bytes, bytes | str | int | None] = {}

    for state_value in state:
        raw_key = base64.b64decode(state_value["key"])

        key: str | bytes = raw_key if raw else _str_or_hex(raw_key)
        val: str | bytes | int | None

        action = state_value["value"]["action"] if "action" in state_value["value"] else state_value["value"]["type"]

        match action:
            case 1:
                raw_val = base64.b64decode(state_value["value"]["bytes"])
                val = raw_val if raw else _str_or_hex(raw_val)
            case 2:
                val = state_value["value"]["uint"]
            case 3:
                val = None
            case _:
                raise NotImplementedError

        decoded_state[key] = val
    return decoded_state


def _get_deploy_control(
    app_spec: ApplicationSpecification, template_var: str, on_complete: transaction.OnComplete
) -> bool | None:
    if template_var not in _strip_comments(app_spec.approval_program):
        return None
    return _get_call_config(app_spec.bare_call_config, on_complete) != CallConfig.NEVER or any(
        h for h in app_spec.hints.values() if _get_call_config(h.call_config, on_complete) != CallConfig.NEVER
    )
