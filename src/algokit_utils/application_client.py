import base64
import dataclasses
import logging
import re
from collections.abc import Sequence
from math import ceil
from typing import Any, Literal, TypedDict, cast, overload

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

import algokit_utils.application_specification as au_spec
import algokit_utils.deploy as au_deploy
from algokit_utils.deploy import check_app_and_deploy
from algokit_utils.logic_error import LogicError, parse_logic_error
from algokit_utils.models import ABITransactionResponse, Account, TransactionResponse

logger = logging.getLogger(__name__)

ABIArgType = Any
ABIArgsDict = dict[str, ABIArgType]

__all__ = [
    "ABICallArgs",
    "ABICallArgsDict",
    "ApplicationClient",
    "CommonCallParameters",
    "CommonCallParametersDict",
    "OnCompleteCallParameters",
    "OnCompleteCallParametersDict",
    "CreateCallParameters",
    "CreateCallParametersDict",
    "Program",
    "execute_atc_with_logic_error",
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
class CommonCallParameters:
    signer: TransactionSigner | None = None
    sender: str | None = None
    suggested_params: transaction.SuggestedParams | None = None
    note: bytes | str | None = None
    lease: bytes | str | None = None
    accounts: list[str] | None = None
    foreign_apps: list[int] | None = None
    foreign_assets: list[int] | None = None
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]] | None = None
    rekey_to: str | None = None


@dataclasses.dataclass(kw_only=True)
class OnCompleteCallParameters(CommonCallParameters):
    on_complete: transaction.OnComplete | None = None


@dataclasses.dataclass(kw_only=True)
class CreateCallParameters(OnCompleteCallParameters):
    extra_pages: int | None = None


class CommonCallParametersDict(TypedDict, total=False):
    signer: TransactionSigner
    sender: str
    suggested_params: transaction.SuggestedParams
    note: bytes | str
    lease: bytes | str


class OnCompleteCallParametersDict(TypedDict, CommonCallParametersDict, total=False):
    on_complete: transaction.OnComplete


class CreateCallParametersDict(TypedDict, OnCompleteCallParametersDict, total=False):
    extra_pages: int


@dataclasses.dataclass(kw_only=True)
class ABICallArgs:
    method: Method | str | bool | None = None
    args: ABIArgsDict = dataclasses.field(default_factory=dict)
    suggested_params: transaction.SuggestedParams | None = None
    lease: bytes | str | None = None
    accounts: list[str] | None = None
    foreign_apps: list[int] | None = None
    foreign_assets: list[int] | None = None
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]] | None = None
    rekey_to: str | None = None


@dataclasses.dataclass(kw_only=True)
class ABICreateCallArgs(ABICallArgs):
    extra_pages: int | None = None
    on_complete: transaction.OnComplete | None = None


class ABICallArgsDict(TypedDict, total=False):
    method: Method | str | bool
    args: ABIArgsDict
    suggested_params: transaction.SuggestedParams
    lease: bytes | str
    accounts: list[str]
    foreign_apps: list[int]
    foreign_assets: list[int]
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]]
    rekey_to: str


class ABICreateCallArgsDict(TypedDict, ABICallArgsDict, total=False):
    extra_pages: int | None
    on_complete: transaction.OnComplete


class ApplicationClient:
    @overload
    def __init__(
        self,
        algod_client: AlgodClient,
        app_spec: au_spec.ApplicationSpecification,
        *,
        app_id: int = 0,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        template_values: au_deploy.TemplateValueDict | None = None,
    ):
        ...

    @overload
    def __init__(
        self,
        algod_client: AlgodClient,
        app_spec: au_spec.ApplicationSpecification,
        *,
        creator: str | Account,
        indexer_client: IndexerClient | None = None,
        existing_deployments: au_deploy.AppLookup | None = None,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        template_values: au_deploy.TemplateValueDict | None = None,
    ):
        ...

    def __init__(
        self,
        algod_client: AlgodClient,
        app_spec: au_spec.ApplicationSpecification,
        *,
        app_id: int = 0,
        creator: str | Account | None = None,
        indexer_client: IndexerClient | None = None,
        existing_deployments: au_deploy.AppLookup | None = None,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        template_values: au_deploy.TemplateValueDict | None = None,
    ):
        self.algod_client = algod_client
        self.app_spec = app_spec
        self._approval_program: Program | None
        self._clear_program: Program | None

        if template_values:
            self._approval_program, self._clear_program = substitute_template_and_compile(
                self.algod_client, app_spec, template_values
            )
        elif not au_deploy.has_template_vars(app_spec):
            self._approval_program = Program(self.app_spec.approval_program, self.algod_client)
            self._clear_program = Program(self.app_spec.clear_program, self.algod_client)
        else:  # can't compile programs yet
            self._approval_program = None
            self._clear_program = None

        self.approval_source_map: SourceMap | None = None
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
        if sender:
            self.sender: str | None = sender
        elif self.signer:
            self.sender = _get_sender_from_signer(self.signer)
        else:
            self.sender = None
        self.suggested_params = suggested_params

    @property
    def app_address(self) -> str:
        return get_application_address(self.app_id)

    @property
    def approval(self) -> Program | None:
        return self._approval_program

    @property
    def clear(self) -> Program | None:
        return self._clear_program

    def prepare(
        self,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        app_id: int | None = None,
        template_values: au_deploy.TemplateValueDict | None = None,
    ) -> "ApplicationClient":
        import copy

        new_client = copy.copy(self)
        new_client._prepare(new_client, signer=signer, sender=sender, app_id=app_id, template_values=template_values)
        return new_client

    def _prepare(
        self,
        target: "ApplicationClient",
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        app_id: int | None = None,
        template_values: au_deploy.TemplateValueDict | None = None,
    ) -> None:
        target.app_id = self.app_id if app_id is None else app_id
        if signer or sender:
            target.signer, target.sender = target._resolve_signer_sender(
                AccountTransactionSigner(signer.private_key) if isinstance(signer, Account) else signer, sender
            )
        if template_values:
            target._approval_program, target._clear_program = substitute_template_and_compile(
                target.algod_client, target.app_spec, template_values
            )

    def deploy(
        self,
        version: str | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        allow_update: bool | None = None,
        allow_delete: bool | None = None,
        on_update: au_deploy.OnUpdate = au_deploy.OnUpdate.Fail,
        on_schema_break: au_deploy.OnSchemaBreak = au_deploy.OnSchemaBreak.Fail,
        template_values: au_deploy.TemplateValueDict | None = None,
        create_args: ABICreateCallArgs | ABICreateCallArgsDict | None = None,
        update_args: ABICallArgs | ABICallArgsDict | None = None,
        delete_args: ABICallArgs | ABICallArgsDict | None = None,
    ) -> au_deploy.DeployResponse:
        before = self._approval_program, self._clear_program, self.sender, self.signer, self.app_id
        try:
            return self._deploy(
                version,
                signer=signer,
                sender=sender,
                allow_update=allow_update,
                allow_delete=allow_delete,
                on_update=on_update,
                on_schema_break=on_schema_break,
                template_values=template_values,
                create_args=create_args,
                update_args=update_args,
                delete_args=delete_args,
            )
        except Exception as ex:
            # undo any prepare changes if there was an error
            self._approval_program, self._clear_program, self.sender, self.signer, self.app_id = before
            raise ex from None

    def _deploy(
        self,
        version: str | None,
        *,
        signer: TransactionSigner | None,
        sender: str | None,
        allow_update: bool | None,
        allow_delete: bool | None,
        on_update: au_deploy.OnUpdate,
        on_schema_break: au_deploy.OnSchemaBreak,
        template_values: au_deploy.TemplateValueDict | None,
        create_args: ABICallArgs | ABICallArgsDict | None,
        update_args: ABICallArgs | ABICallArgsDict | None,
        delete_args: ABICallArgs | ABICallArgsDict | None,
    ) -> au_deploy.DeployResponse:
        """Ensures app associated with app client's creator is present and up to date"""
        if self.app_id:
            raise au_deploy.DeploymentFailedError(
                f"Attempt to deploy app which already has an app index of {self.app_id}"
            )
        signer, sender = self._resolve_signer_sender(signer, sender)
        if not sender:
            raise au_deploy.DeploymentFailedError("No sender provided, unable to deploy app")
        if not self._creator:
            raise au_deploy.DeploymentFailedError("No creator provided, unable to deploy app")
        if self._creator != sender:
            raise au_deploy.DeploymentFailedError(
                f"Attempt to deploy contract with a sender address {sender} that differs "
                f"from the given creator address for this application client: {self._creator}"
            )

        # make a copy
        template_values = dict(template_values or {})
        au_deploy.add_deploy_template_variables(template_values, allow_update=allow_update, allow_delete=allow_delete)

        self._prepare(self, template_values=template_values)
        approval_program, clear_program = self._check_is_compiled()

        updatable = (
            allow_update
            if allow_update is not None
            else au_deploy.get_deploy_control(
                self.app_spec, au_deploy.UPDATABLE_TEMPLATE_NAME, transaction.OnComplete.UpdateApplicationOC
            )
        )
        deletable = (
            allow_delete
            if allow_delete is not None
            else au_deploy.get_deploy_control(
                self.app_spec, au_deploy.DELETABLE_TEMPLATE_NAME, transaction.OnComplete.DeleteApplicationOC
            )
        )

        name = self.app_spec.contract.name

        # TODO: allow resolve app id via environment variable
        app = self._load_app_reference()

        if version is None:
            if app.app_id == 0:
                version = "v1.0"
            else:
                assert isinstance(app, au_deploy.AppDeployMetaData)
                version = get_next_version(app.version)
        app_spec_note = au_deploy.AppDeployMetaData(name, version, updatable=updatable, deletable=deletable)

        def create_app() -> au_deploy.DeployResponse:
            assert self.existing_deployments

            method, abi_args, parameters = _convert_deploy_args(create_args, app_spec_note, signer, sender)
            create_response = self.create(
                method,
                parameters,
                **abi_args,
            )
            logger.info(f"{name} ({version}) deployed successfully, with app id {self.app_id}.")
            assert create_response.confirmed_round is not None
            app_metadata = _create_metadata(app_spec_note, self.app_id, create_response.confirmed_round)
            self.existing_deployments.apps[name] = app_metadata
            return au_deploy.DeployResponse(
                app=app_metadata, create_response=create_response, action_taken=au_deploy.OperationPerformed.Create
            )

        if app.app_id == 0:
            logger.info(f"{name} not found in {self._creator} account, deploying app.")
            return create_app()

        def create_and_delete_app() -> au_deploy.DeployResponse:
            assert isinstance(app, au_deploy.AppMetaData)
            assert self.existing_deployments

            logger.info(f"Replacing {name} ({app.version}) with {name} ({version}) in {self._creator} account.")
            atc = AtomicTransactionComposer()
            create_method, create_abi_args, create_parameters = _convert_deploy_args(
                create_args, app_spec_note, signer, sender
            )
            self.compose_create(
                atc,
                create_method,
                create_parameters,
                **create_abi_args,
            )
            delete_method, delete_abi_args, delete_parameters = _convert_deploy_args(
                delete_args, app_spec_note, signer, sender
            )
            self.compose_delete(
                atc,
                delete_method,
                delete_parameters,
                **delete_abi_args,
            )
            create_delete_response = self.execute_atc(atc)
            create_response = _tr_from_atr(atc, create_delete_response, 0)
            delete_response = _tr_from_atr(atc, create_delete_response, 1)
            self._set_app_id_from_tx_id(create_response.tx_id)
            logger.info(f"{name} ({version}) deployed successfully, with app id {self.app_id}.")
            logger.info(f"{name} ({app.version}) with app id {app.app_id}, deleted successfully.")

            app_metadata = _create_metadata(app_spec_note, self.app_id, create_delete_response.confirmed_round)
            self.existing_deployments.apps[name] = app_metadata

            return au_deploy.DeployResponse(
                app=app_metadata,
                create_response=create_response,
                delete_response=delete_response,
                action_taken=au_deploy.OperationPerformed.Replace,
            )

        def update_app() -> au_deploy.DeployResponse:
            assert on_update == au_deploy.OnUpdate.UpdateApp
            assert isinstance(app, au_deploy.AppMetaData)
            assert self.existing_deployments
            logger.info(f"Updating {name} to {version} in {self._creator} account, with app id {app.app_id}")
            method, abi_args, parameters = _convert_deploy_args(update_args, app_spec_note, signer, sender)
            update_response = self.update(
                method,
                parameters,
                **abi_args,
            )
            app_metadata = _create_metadata(
                app_spec_note,
                self.app_id,
                app.created_round,
                updated_round=update_response.confirmed_round,
                original_metadata=app.created_metadata,
            )
            self.existing_deployments.apps[name] = app_metadata
            return au_deploy.DeployResponse(
                app=app_metadata, update_response=update_response, action_taken=au_deploy.OperationPerformed.Update
            )

        assert isinstance(app, au_deploy.AppMetaData)
        logger.debug(f"{name} found in {self._creator} account, with app id {app.app_id}, version={app.version}.")

        app_changes = au_deploy.check_for_app_changes(
            self.algod_client,
            new_approval=approval_program.raw_binary,
            new_clear=clear_program.raw_binary,
            new_global_schema=self.app_spec.global_state_schema,
            new_local_schema=self.app_spec.local_state_schema,
            app_id=app.app_id,
        )

        return check_app_and_deploy(
            app,
            app_changes,
            on_update=on_update,
            on_schema_break=on_schema_break,
            update_app=update_app,
            create_and_delete_app=create_and_delete_app,
        )

    def compose_create(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with application id == 0 and the schema and source of client's app_spec to atc"""
        approval_program, clear_program = self._check_is_compiled()
        transaction_parameters = _convert_call_parameters(transaction_parameters)

        extra_pages = transaction_parameters.extra_pages or num_extra_program_pages(
            approval_program.raw_binary, clear_program.raw_binary
        )

        self.add_method_call(
            atc,
            app_id=0,
            abi_method=call_abi_method,
            abi_args=abi_kwargs,
            on_complete=transaction_parameters.on_complete or transaction.OnComplete.NoOpOC,
            call_config=au_spec.CallConfig.CREATE,
            parameters=transaction_parameters,
            approval_program=approval_program.raw_binary,
            clear_program=clear_program.raw_binary,
            global_schema=self.app_spec.global_state_schema,
            local_schema=self.app_spec.local_state_schema,
            extra_pages=extra_pages,
        )

    @overload
    def create(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = ...,
    ) -> TransactionResponse:
        ...

    @overload
    def create(
        self,
        call_abi_method: Method | str | Literal[True],
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse:
        ...

    @overload
    def create(
        self,
        call_abi_method: Method | str | bool | None = ...,
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def create(
        self,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with application id == 0 and the schema and source of client's app_spec"""

        atc = AtomicTransactionComposer()

        self.compose_create(
            atc,
            call_abi_method,
            transaction_parameters,
            **abi_kwargs,
        )
        create_result = self._execute_atc_tr(atc)
        self._set_app_id_from_tx_id(create_result.tx_id)
        return create_result

    def compose_update(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with on_complete=UpdateApplication to atc"""
        approval_program, clear_program = self._check_is_compiled()

        self.add_method_call(
            atc=atc,
            abi_method=call_abi_method,
            abi_args=abi_kwargs,
            parameters=transaction_parameters,
            on_complete=transaction.OnComplete.UpdateApplicationOC,
            approval_program=approval_program.raw_binary,
            clear_program=clear_program.raw_binary,
        )

    @overload
    def update(
        self,
        call_abi_method: Method | str | Literal[True],
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse:
        ...

    @overload
    def update(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = ...,
    ) -> TransactionResponse:
        ...

    @overload
    def update(
        self,
        call_abi_method: Method | str | bool | None = ...,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def update(
        self,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with on_complete=UpdateApplication"""

        atc = AtomicTransactionComposer()
        self.compose_update(
            atc,
            call_abi_method,
            transaction_parameters=transaction_parameters,
            **abi_kwargs,
        )
        return self._execute_atc_tr(atc)

    def compose_delete(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with on_complete=DeleteApplication to atc"""

        self.add_method_call(
            atc,
            call_abi_method,
            abi_args=abi_kwargs,
            parameters=transaction_parameters,
            on_complete=transaction.OnComplete.DeleteApplicationOC,
        )

    @overload
    def delete(
        self,
        call_abi_method: Method | str | Literal[True],
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse:
        ...

    @overload
    def delete(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = ...,
    ) -> TransactionResponse:
        ...

    @overload
    def delete(
        self,
        call_abi_method: Method | str | bool | None = ...,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def delete(
        self,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with on_complete=DeleteApplication"""

        atc = AtomicTransactionComposer()
        self.compose_delete(
            atc,
            call_abi_method,
            transaction_parameters=transaction_parameters,
            **abi_kwargs,
        )
        return self._execute_atc_tr(atc)

    def compose_call(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with specified parameters to atc"""
        _parameters = _convert_call_parameters(transaction_parameters)
        self.add_method_call(
            atc,
            abi_method=call_abi_method,
            abi_args=abi_kwargs,
            parameters=_parameters,
            on_complete=_parameters.on_complete or transaction.OnComplete.NoOpOC,
        )

    @overload
    def call(
        self,
        call_abi_method: Method | str | Literal[True],
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse:
        ...

    @overload
    def call(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = ...,
    ) -> TransactionResponse:
        ...

    @overload
    def call(
        self,
        call_abi_method: Method | str | bool | None = ...,
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def call(
        self,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with specified parameters"""
        atc = AtomicTransactionComposer()
        _parameters = _convert_call_parameters(transaction_parameters)
        self.compose_call(
            atc,
            call_abi_method=call_abi_method,
            transaction_parameters=_parameters,
            **abi_kwargs,
        )

        method = self._resolve_method(
            call_abi_method, abi_kwargs, _parameters.on_complete or transaction.OnComplete.NoOpOC
        )
        # If its a read-only method, use dryrun (TODO: swap with simulate later?)
        if method:
            response = self._try_dry_run_call(method, atc)
            if response:
                return response

        return self._execute_atc_tr(atc)

    def compose_opt_in(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with on_complete=OptIn to atc"""
        self.add_method_call(
            atc,
            abi_method=call_abi_method,
            abi_args=abi_kwargs,
            parameters=transaction_parameters,
            on_complete=transaction.OnComplete.OptInOC,
        )

    @overload
    def opt_in(
        self,
        call_abi_method: Method | str | Literal[True] = ...,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse:
        ...

    @overload
    def opt_in(
        self,
        call_abi_method: Literal[False] = ...,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
    ) -> TransactionResponse:
        ...

    @overload
    def opt_in(
        self,
        call_abi_method: Method | str | bool | None = ...,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def opt_in(
        self,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with on_complete=OptIn"""
        atc = AtomicTransactionComposer()
        self.compose_opt_in(
            atc,
            call_abi_method=call_abi_method,
            transaction_parameters=transaction_parameters,
            **abi_kwargs,
        )
        return self._execute_atc_tr(atc)

    def compose_close_out(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with on_complete=CloseOut to ac"""
        self.add_method_call(
            atc,
            abi_method=call_abi_method,
            abi_args=abi_kwargs,
            parameters=transaction_parameters,
            on_complete=transaction.OnComplete.CloseOutOC,
        )

    @overload
    def close_out(
        self,
        call_abi_method: Method | str | Literal[True],
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse:
        ...

    @overload
    def close_out(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = ...,
    ) -> TransactionResponse:
        ...

    @overload
    def close_out(
        self,
        call_abi_method: Method | str | bool | None = ...,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def close_out(
        self,
        call_abi_method: Method | str | bool | None = None,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with on_complete=CloseOut"""
        atc = AtomicTransactionComposer()
        self.compose_close_out(
            atc,
            call_abi_method=call_abi_method,
            transaction_parameters=transaction_parameters,
            **abi_kwargs,
        )
        return self._execute_atc_tr(atc)

    def compose_clear_state(
        self,
        atc: AtomicTransactionComposer,
        /,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        app_args: list[bytes] | None = None,
    ) -> None:
        """Adds a signed transaction with on_complete=ClearState to atc"""
        return self.add_method_call(
            atc,
            parameters=transaction_parameters,
            on_complete=transaction.OnComplete.ClearStateOC,
            app_args=app_args,
        )

    def clear_state(
        self,
        transaction_parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        app_args: list[bytes] | None = None,
    ) -> TransactionResponse:
        """Submits a signed transaction with on_complete=ClearState"""
        atc = AtomicTransactionComposer()
        self.compose_clear_state(
            atc,
            transaction_parameters=transaction_parameters,
            app_args=app_args,
        )
        return self._execute_atc_tr(atc)

    def get_global_state(self, *, raw: bool = False) -> dict[bytes | str, bytes | str | int]:
        """gets the global state info for the app id set"""
        global_state = self.algod_client.application_info(self.app_id)
        assert isinstance(global_state, dict)
        return cast(
            dict[bytes | str, bytes | str | int],
            _decode_state(global_state.get("params", {}).get("global-state", {}), raw=raw),
        )

    def get_local_state(self, account: str | None = None, *, raw: bool = False) -> dict[bytes | str, bytes | str | int]:
        """gets the local state info for the app id set and the account specified"""

        if account is None:
            _, account = self._resolve_signer_sender(self.signer, self.sender)

        acct_state = self.algod_client.account_application_info(account, self.app_id)
        assert isinstance(acct_state, dict)
        return cast(
            dict[bytes | str, bytes | str | int],
            _decode_state(acct_state.get("app-local-state", {}).get("key-value", {}), raw=raw),
        )

    def resolve(self, to_resolve: au_spec.DefaultArgumentDict) -> int | str | bytes:
        def _data_check(value: Any) -> int | str | bytes:
            if isinstance(value, (int, str, bytes)):
                return value
            raise ValueError(f"Unexpected type for constant data: {value}")

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
                assert isinstance(response, ABITransactionResponse)
                return _data_check(response.return_value)

            case {"source": source}:
                raise ValueError(f"Unrecognized default argument source: {source}")
            case _:
                raise TypeError("Unable to interpret default argument specification")

    def _check_is_compiled(self) -> tuple[Program, Program]:
        if self._approval_program is None or self._clear_program is None:
            raise Exception(
                "Compiled programs are not available, please provide template_values before creating or updating"
            )
        return self._approval_program, self._clear_program

    def _try_dry_run_call(self, method: Method, atc: AtomicTransactionComposer) -> ABITransactionResponse | None:
        hints = self._method_hints(method)
        if hints and hints.read_only:
            dr_req = transaction.create_dryrun(self.algod_client, atc.gather_signatures())  # type: ignore[arg-type]
            dr_result = self.algod_client.dryrun(dr_req)  # type: ignore[arg-type]
            for txn in dr_result["txns"]:
                if "app-call-messages" in txn and "REJECT" in txn["app-call-messages"]:
                    msg = ", ".join(txn["app-call-messages"])
                    raise Exception(f"Dryrun for readonly method failed: {msg}")

            method_results = _parse_result({0: method}, dr_result["txns"], atc.tx_ids)
            return ABITransactionResponse(**method_results[0].__dict__, confirmed_round=None)
        return None

    def _load_reference_and_check_app_id(self) -> None:
        self._load_app_reference()
        self._check_app_id()

    def _load_app_reference(self) -> au_deploy.AppReference | au_deploy.AppMetaData:
        if not self.existing_deployments and self._creator:
            assert self._indexer_client
            self.existing_deployments = au_deploy.get_creator_apps(self._indexer_client, self._creator)

        if self.existing_deployments and self.app_id == 0:
            app = self.existing_deployments.apps.get(self.app_spec.contract.name)
            if app:
                self.app_id = app.app_id
                return app

        return au_deploy.AppReference(self.app_id, self.app_address)

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
        call_config: au_spec.CallConfig = au_spec.CallConfig.CALL,
    ) -> Method | None:
        matches: list[Method | None] = []
        match abi_method:
            case str() | Method():  # abi method specified
                return self._resolve_abi_method(abi_method)
            case bool() | None:  # find abi method
                has_bare_config = (
                    call_config in au_deploy.get_call_config(self.app_spec.bare_call_config, on_complete)
                    or on_complete == transaction.OnComplete.ClearStateOC
                )
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
                f"Could not find an exact method to use for {on_complete.name} with call_config of {call_config.name}, "
                f"specify the exact method using abi_method and args parameters, considered: {signatures}"
            )
        else:  # no match
            raise Exception(
                f"Could not find any methods to use for {on_complete.name} with call_config of {call_config.name}"
            )

    def _get_approval_source_map(self) -> SourceMap | None:
        if self.approval:
            return self.approval.source_map

        return self.approval_source_map

    def add_method_call(
        self,
        atc: AtomicTransactionComposer,
        abi_method: Method | str | bool | None = None,
        abi_args: ABIArgsDict | None = None,
        app_id: int | None = None,
        parameters: CommonCallParameters | CommonCallParametersDict | None = None,
        on_complete: transaction.OnComplete = transaction.OnComplete.NoOpOC,
        local_schema: transaction.StateSchema | None = None,
        global_schema: transaction.StateSchema | None = None,
        approval_program: bytes | None = None,
        clear_program: bytes | None = None,
        extra_pages: int | None = None,
        app_args: list[bytes] | None = None,
        call_config: au_spec.CallConfig = au_spec.CallConfig.CALL,
    ) -> None:
        """Adds a transaction to the AtomicTransactionComposer passed"""
        if app_id is None:
            self._load_reference_and_check_app_id()
            app_id = self.app_id
        parameters = _convert_call_parameters(parameters)
        method = self._resolve_method(abi_method, abi_args, on_complete, call_config)
        sp = parameters.suggested_params or self.suggested_params or self.algod_client.suggested_params()
        signer, sender = self._resolve_signer_sender(parameters.signer, parameters.sender)
        if parameters.boxes is not None:
            # TODO: algosdk actually does this, but it's type hints say otherwise...
            encoded_boxes = [(id_, algosdk.encoding.encode_as_bytes(name)) for id_, name in parameters.boxes]
        else:
            encoded_boxes = None

        encoded_lease = parameters.lease.encode("utf-8") if isinstance(parameters.lease, str) else parameters.lease

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
                        accounts=parameters.accounts,
                        foreign_apps=parameters.foreign_apps,
                        foreign_assets=parameters.foreign_assets,
                        boxes=encoded_boxes,
                        note=parameters.note,
                        lease=encoded_lease,
                        rekey_to=parameters.rekey_to,
                        app_args=app_args,
                    ),
                    signer=signer,
                )
            )
        else:  # resolve ABI method args
            hints = self._method_hints(method)

            args: list = []
            # copy args so we don't mutate original
            abi_args = dict(abi_args or {})
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
                accounts=parameters.accounts,
                foreign_apps=parameters.foreign_apps,
                foreign_assets=parameters.foreign_assets,
                boxes=encoded_boxes,
                note=parameters.note.encode("utf-8") if isinstance(parameters.note, str) else parameters.note,
                lease=encoded_lease,
                rekey_to=parameters.rekey_to,
            )

    def _method_matches(
        self,
        method: Method,
        args: ABIArgsDict | None,
        on_complete: transaction.OnComplete,
        call_config: au_spec.CallConfig,
    ) -> bool:
        hints = self._method_hints(method)
        if call_config not in au_deploy.get_call_config(hints.call_config, on_complete):
            return False
        method_args = {m.name for m in method.args}
        provided_args = set(args or {}) | set(hints.default_arguments)

        # TODO: also match on types?
        return method_args == provided_args

    def _find_abi_methods(
        self, args: ABIArgsDict | None, on_complete: transaction.OnComplete, call_config: au_spec.CallConfig
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

    def _method_hints(self, method: Method) -> au_spec.MethodHints:
        sig = method.get_signature()
        if sig not in self.app_spec.hints:
            return au_spec.MethodHints()
        return self.app_spec.hints[sig]

    def _execute_atc_tr(self, atc: AtomicTransactionComposer) -> TransactionResponse:
        result = self.execute_atc(atc)
        return _tr_from_atr(atc, result)

    def execute_atc(self, atc: AtomicTransactionComposer) -> AtomicTransactionResponse:
        return execute_atc_with_logic_error(
            atc,
            self.algod_client,
            approval_program=self.approval.teal if self.approval else self.app_spec.approval_program,
            approval_source_map=self._get_approval_source_map(),
        )

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


def substitute_template_and_compile(
    algod_client: AlgodClient,
    app_spec: au_spec.ApplicationSpecification,
    template_values: au_deploy.TemplateValueDict,
) -> tuple[Program, Program]:
    template_values = dict(template_values or {})
    clear = au_deploy.replace_template_variables(app_spec.clear_program, template_values)

    au_deploy.check_template_variables(app_spec.approval_program, template_values)
    approval = au_deploy.replace_template_variables(app_spec.approval_program, template_values)

    return Program(approval, algod_client), Program(clear, algod_client)


def get_app_id_from_tx_id(algod_client: AlgodClient, tx_id: str) -> int:
    result = algod_client.pending_transaction_info(tx_id)
    assert isinstance(result, dict)
    app_id = result["application-index"]
    assert isinstance(app_id, int)
    return app_id


def get_next_version(current_version: str) -> str:
    pattern = re.compile(r"(?P<prefix>\w*)(?P<version>(?:\d+\.)*\d+)(?P<suffix>\w*)")
    match = pattern.match(current_version)
    if match:
        version = match.group("version")
        new_version = _increment_version(version)

        def replacement(m: re.Match) -> str:
            return f"{m.group('prefix')}{new_version}{m.group('suffix')}"

        return re.sub(pattern, replacement, current_version)
    raise au_deploy.DeploymentFailedError(
        f"Could not auto increment {current_version}, please specify the next version using the version parameter"
    )


def execute_atc_with_logic_error(
    atc: AtomicTransactionComposer,
    algod_client: AlgodClient,
    wait_rounds: int = 4,
    approval_program: str | None = None,
    approval_source_map: SourceMap | None = None,
) -> AtomicTransactionResponse:
    try:
        return atc.execute(algod_client, wait_rounds=wait_rounds)
    except Exception as ex:
        if approval_source_map and approval_program:
            logic_error_data = parse_logic_error(str(ex))
            if logic_error_data is not None:
                raise LogicError(
                    logic_error=ex,
                    program=approval_program,
                    source_map=approval_source_map,
                    **logic_error_data,
                ) from ex
        raise ex


def _create_metadata(
    app_spec_note: au_deploy.AppDeployMetaData,
    app_id: int,
    created_round: int,
    updated_round: int | None = None,
    original_metadata: au_deploy.AppDeployMetaData | None = None,
) -> au_deploy.AppMetaData:
    app_metadata = au_deploy.AppMetaData(
        app_id=app_id,
        app_address=get_application_address(app_id),
        created_metadata=original_metadata or app_spec_note,
        created_round=created_round,
        updated_round=updated_round or created_round,
        **app_spec_note.__dict__,
        deleted=False,
    )
    return app_metadata


def _convert_call_parameters(args: CommonCallParameters | CommonCallParametersDict | None) -> CreateCallParameters:
    _args = dataclasses.asdict(args) if isinstance(args, CommonCallParameters) else (args or {})
    return CreateCallParameters(**_args)


def _convert_deploy_args(
    _args: ABICallArgs | ABICallArgsDict | None,
    note: au_deploy.AppDeployMetaData,
    signer: TransactionSigner | None,
    sender: str | None,
) -> tuple[Method | str | bool | None, ABIArgsDict, CreateCallParameters]:
    args = dataclasses.asdict(_args) if isinstance(_args, ABICallArgs) else (_args or {})

    # return most derived type, unused parameters are ignored
    parameters = CreateCallParameters(
        note=note.encode(),
        signer=signer,
        sender=sender,
        suggested_params=args.get("suggested_params"),
        lease=args.get("lease"),
        accounts=args.get("accounts"),
        foreign_assets=args.get("foreign_assets"),
        foreign_apps=args.get("foreign_apps"),
        boxes=args.get("boxes"),
        rekey_to=args.get("rekey_to"),
        extra_pages=args.get("extra_pages"),
        on_complete=args.get("on_complete"),
    )

    return args.get("method"), args.get("args") or {}, parameters


def _get_sender_from_signer(signer: TransactionSigner) -> str:
    if isinstance(signer, AccountTransactionSigner):
        sender = address_from_private_key(signer.private_key)  # type: ignore[no-untyped-call]
        assert isinstance(sender, str)
        return sender
    elif isinstance(signer, MultisigTransactionSigner):
        sender = signer.msig.address()  # type: ignore[no-untyped-call]
        assert isinstance(sender, str)
        return sender
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


def _tr_from_atr(
    atc: AtomicTransactionComposer, result: AtomicTransactionResponse, transaction_index: int = 0
) -> TransactionResponse:
    if result.abi_results and transaction_index in atc.method_dict:  # expecting an ABI result
        abi_index = 0
        # count how many of the earlier transactions were also ABI
        for index in range(transaction_index):
            if index in atc.method_dict:
                abi_index += 1
        return ABITransactionResponse(
            **result.abi_results[abi_index].__dict__,
            confirmed_round=result.confirmed_round,
        )
    else:
        return TransactionResponse(
            tx_id=result.tx_ids[transaction_index],
            confirmed_round=result.confirmed_round,
        )
