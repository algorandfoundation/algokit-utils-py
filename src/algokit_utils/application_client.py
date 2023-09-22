import base64
import copy
import json
import logging
import re
import typing
from math import ceil
from pathlib import Path
from typing import Any, Literal, cast, overload

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
    EmptySigner,
    LogicSigTransactionSigner,
    MultisigTransactionSigner,
    SimulateAtomicTransactionResponse,
    TransactionSigner,
    TransactionWithSigner,
)
from algosdk.constants import APP_PAGE_MAX_SIZE
from algosdk.logic import get_application_address
from algosdk.source_map import SourceMap
from algosdk.v2client.models import SimulateRequest, SimulateRequestTransactionGroup, SimulateTraceConfig

import algokit_utils.application_specification as au_spec
import algokit_utils.deploy as au_deploy
from algokit_utils.config import config
from algokit_utils.logic_error import LogicError, parse_logic_error
from algokit_utils.models import (
    ABIArgsDict,
    ABIArgType,
    ABIMethod,
    ABITransactionResponse,
    Account,
    CreateCallParameters,
    CreateCallParametersDict,
    OnCompleteCallParameters,
    OnCompleteCallParametersDict,
    TransactionParameters,
    TransactionParametersDict,
    TransactionResponse,
)

if typing.TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient
    from algosdk.v2client.indexer import IndexerClient


logger = logging.getLogger(__name__)


"""A dictionary `dict[str, Any]` representing ABI argument names and values"""

__all__ = [
    "ApplicationClient",
    "Program",
    "execute_atc_with_logic_error",
    "get_next_version",
    "get_sender_from_signer",
    "num_extra_program_pages",
]

"""Alias for {py:class}`pyteal.ABIReturnSubroutine`, {py:class}`algosdk.abi.method.Method` or a {py:class}`str`
representing an ABI method name or signature"""


class Program:
    """A compiled TEAL program"""

    def __init__(self, program: str, client: "AlgodClient"):
        """
        Fully compile the program source to binary and generate a
        source map for matching pc to line number
        """
        self.teal = program
        result: dict = client.compile(au_deploy.strip_comments(self.teal), source_map=True)
        self.raw_binary = base64.b64decode(result["result"])
        self.binary_hash: str = result["hash"]
        self.source_map = SourceMap(result["sourcemap"])


def num_extra_program_pages(approval: bytes, clear: bytes) -> int:
    """Calculate minimum number of extra_pages required for provided approval and clear programs"""

    return ceil(((len(approval) + len(clear)) - APP_PAGE_MAX_SIZE) / APP_PAGE_MAX_SIZE)


class ApplicationClient:
    """A class that wraps an ARC-0032 app spec and provides high productivity methods to deploy and call the app"""

    @overload
    def __init__(
        self,
        algod_client: "AlgodClient",
        app_spec: au_spec.ApplicationSpecification | Path,
        *,
        app_id: int = 0,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        template_values: au_deploy.TemplateValueMapping | None = None,
    ):
        ...

    @overload
    def __init__(
        self,
        algod_client: "AlgodClient",
        app_spec: au_spec.ApplicationSpecification | Path,
        *,
        creator: str | Account,
        indexer_client: "IndexerClient | None" = None,
        existing_deployments: au_deploy.AppLookup | None = None,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        template_values: au_deploy.TemplateValueMapping | None = None,
        app_name: str | None = None,
    ):
        ...

    def __init__(
        self,
        algod_client: "AlgodClient",
        app_spec: au_spec.ApplicationSpecification | Path,
        *,
        app_id: int = 0,
        creator: str | Account | None = None,
        indexer_client: "IndexerClient | None" = None,
        existing_deployments: au_deploy.AppLookup | None = None,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        suggested_params: transaction.SuggestedParams | None = None,
        template_values: au_deploy.TemplateValueMapping | None = None,
        app_name: str | None = None,
    ):
        """ApplicationClient can be created with an app_id to interact with an existing application, alternatively
        it can be created with a creator and indexer_client specified to find existing applications by name and creator.

        :param AlgodClient algod_client: AlgoSDK algod client
        :param ApplicationSpecification | Path app_spec: An Application Specification or the path to one
        :param int app_id: The app_id of an existing application, to instead find the application by creator and name
        use the creator and indexer_client parameters
        :param str | Account creator: The address or Account of the app creator to resolve the app_id
        :param IndexerClient indexer_client: AlgoSDK indexer client, only required if deploying or finding app_id by
        creator and app name
        :param AppLookup existing_deployments:
        :param TransactionSigner | Account signer: Account or signer to use to sign transactions, if not specified and
        creator was passed as an Account will use that.
        :param str sender: Address to use as the sender for all transactions, will use the address associated with the
        signer if not specified.
        :param TemplateValueMapping template_values: Values to use for TMPL_* template variables, dictionary keys should
        *NOT* include the TMPL_ prefix
        :param str | None app_name: Name of application to use when deploying, defaults to name defined on the
        Application Specification
        """
        self.algod_client = algod_client
        self.app_spec = (
            au_spec.ApplicationSpecification.from_json(app_spec.read_text()) if isinstance(app_spec, Path) else app_spec
        )
        self._app_name = app_name
        self._approval_program: Program | None = None
        self._approval_source_map: SourceMap | None = None
        self._clear_program: Program | None = None

        self.template_values: au_deploy.TemplateValueMapping = template_values or {}
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
    def app_name(self) -> str:
        return self._app_name or self.app_spec.contract.name

    @app_name.setter
    def app_name(self, value: str) -> None:
        self._app_name = value

    @property
    def app_address(self) -> str:
        return get_application_address(self.app_id)

    @property
    def approval(self) -> Program | None:
        return self._approval_program

    @property
    def approval_source_map(self) -> SourceMap | None:
        if self._approval_source_map:
            return self._approval_source_map
        if self._approval_program:
            return self._approval_program.source_map
        return None

    @approval_source_map.setter
    def approval_source_map(self, value: SourceMap) -> None:
        self._approval_source_map = value

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
        """Creates a copy of this ApplicationClient, using the new signer, sender and app_id values if provided.
        Will also substitute provided template_values into the associated app_spec in the copy"""
        new_client: "ApplicationClient" = copy.copy(self)
        new_client._prepare(  # noqa: SLF001
            new_client, signer=signer, sender=sender, app_id=app_id, template_values=template_values
        )
        return new_client

    def _prepare(
        self,
        target: "ApplicationClient",
        *,
        signer: TransactionSigner | Account | None = None,
        sender: str | None = None,
        app_id: int | None = None,
        template_values: au_deploy.TemplateValueDict | None = None,
    ) -> None:
        target.app_id = self.app_id if app_id is None else app_id
        target.signer, target.sender = target.get_signer_sender(
            AccountTransactionSigner(signer.private_key) if isinstance(signer, Account) else signer, sender
        )
        target.template_values = self.template_values | (template_values or {})

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
        template_values: au_deploy.TemplateValueMapping | None = None,
        create_args: au_deploy.ABICreateCallArgs
        | au_deploy.ABICreateCallArgsDict
        | au_deploy.DeployCreateCallArgs
        | None = None,
        update_args: au_deploy.ABICallArgs | au_deploy.ABICallArgsDict | au_deploy.DeployCallArgs | None = None,
        delete_args: au_deploy.ABICallArgs | au_deploy.ABICallArgsDict | au_deploy.DeployCallArgs | None = None,
    ) -> au_deploy.DeployResponse:
        """Deploy an application and update client to reference it.

        Idempotently deploy (create, update/delete if changed) an app against the given name via the given creator
        account, including deploy-time template placeholder substitutions.
        To understand the architecture decisions behind this functionality please see
        <https://github.com/algorandfoundation/algokit-cli/blob/main/docs/architecture-decisions/2023-01-12_smart-contract-deployment.md>

        ```{note}
        If there is a breaking state schema change to an existing app (and `on_schema_break` is set to
        'ReplaceApp' the existing app will be deleted and re-created.
        ```

        ```{note}
        If there is an update (different TEAL code) to an existing app (and `on_update` is set to 'ReplaceApp')
        the existing app will be deleted and re-created.
        ```

        :param str version: version to use when creating or updating app, if None version will be auto incremented
        :param algosdk.atomic_transaction_composer.TransactionSigner signer: signer to use when deploying app
        , if None uses self.signer
        :param str sender: sender address to use when deploying app, if None uses self.sender
        :param bool allow_delete: Used to set the `TMPL_DELETABLE` template variable to conditionally control if an app
        can be deleted
        :param bool allow_update: Used to set the `TMPL_UPDATABLE` template variable to conditionally control if an app
        can be updated
        :param OnUpdate on_update: Determines what action to take if an application update is required
        :param OnSchemaBreak on_schema_break: Determines what action to take if an application schema requirements
        has increased beyond the current allocation
        :param dict[str, int|str|bytes] template_values: Values to use for `TMPL_*` template variables, dictionary keys
        should *NOT* include the TMPL_ prefix
        :param ABICreateCallArgs create_args: Arguments used when creating an application
        :param ABICallArgs | ABICallArgsDict update_args: Arguments used when updating an application
        :param ABICallArgs | ABICallArgsDict delete_args: Arguments used when deleting an application
        :return DeployResponse: details action taken and relevant transactions
        :raises DeploymentError: If the deployment failed
        """
        # check inputs
        if self.app_id:
            raise au_deploy.DeploymentFailedError(
                f"Attempt to deploy app which already has an app index of {self.app_id}"
            )
        try:
            resolved_signer, resolved_sender = self.resolve_signer_sender(signer, sender)
        except ValueError as ex:
            raise au_deploy.DeploymentFailedError(f"{ex}, unable to deploy app") from None
        if not self._creator:
            raise au_deploy.DeploymentFailedError("No creator provided, unable to deploy app")
        if self._creator != resolved_sender:
            raise au_deploy.DeploymentFailedError(
                f"Attempt to deploy contract with a sender address {resolved_sender} that differs "
                f"from the given creator address for this application client: {self._creator}"
            )

        # make a copy and prepare variables
        template_values = self.template_values | dict(template_values or {})
        au_deploy.add_deploy_template_variables(template_values, allow_update=allow_update, allow_delete=allow_delete)

        existing_app_metadata_or_reference = self._load_app_reference()

        self._approval_program, self._clear_program = substitute_template_and_compile(
            self.algod_client, self.app_spec, template_values
        )
        deployer = au_deploy.Deployer(
            app_client=self,
            creator=self._creator,
            signer=resolved_signer,
            sender=resolved_sender,
            new_app_metadata=self._get_app_deploy_metadata(version, allow_update, allow_delete),
            existing_app_metadata_or_reference=existing_app_metadata_or_reference,
            on_update=on_update,
            on_schema_break=on_schema_break,
            create_args=create_args,
            update_args=update_args,
            delete_args=delete_args,
        )

        return deployer.deploy()

    def compose_create(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with application id == 0 and the schema and source of client's app_spec to atc"""
        approval_program, clear_program = self._check_is_compiled()
        transaction_parameters = _convert_transaction_parameters(transaction_parameters)

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
        call_abi_method: ABIMethod | Literal[True],
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse:
        ...

    @overload
    def create(
        self,
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: CreateCallParameters | CreateCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def create(
        self,
        call_abi_method: ABIMethod | bool | None = None,
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
        self.app_id = au_deploy.get_app_id_from_tx_id(self.algod_client, create_result.tx_id)
        return create_result

    def compose_update(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
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
        call_abi_method: ABIMethod | Literal[True],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse:
        ...

    @overload
    def update(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
    ) -> TransactionResponse:
        ...

    @overload
    def update(
        self,
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def update(
        self,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
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
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
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
        call_abi_method: ABIMethod | Literal[True],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse:
        ...

    @overload
    def delete(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
    ) -> TransactionResponse:
        ...

    @overload
    def delete(
        self,
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def delete(
        self,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
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
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> None:
        """Adds a signed transaction with specified parameters to atc"""
        _parameters = _convert_transaction_parameters(transaction_parameters)
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
        call_abi_method: ABIMethod | Literal[True],
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
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def call(
        self,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: OnCompleteCallParameters | OnCompleteCallParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        """Submits a signed transaction with specified parameters"""
        atc = AtomicTransactionComposer()
        _parameters = _convert_transaction_parameters(transaction_parameters)
        self.compose_call(
            atc,
            call_abi_method=call_abi_method,
            transaction_parameters=_parameters,
            **abi_kwargs,
        )

        method = self._resolve_method(
            call_abi_method, abi_kwargs, _parameters.on_complete or transaction.OnComplete.NoOpOC
        )
        if method:
            hints = self._method_hints(method)
            if hints and hints.read_only:
                return self._simulate_readonly_call(method, atc)

        return self._execute_atc_tr(atc)

    def compose_opt_in(
        self,
        atc: AtomicTransactionComposer,
        /,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
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
        call_abi_method: ABIMethod | Literal[True] = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse:
        ...

    @overload
    def opt_in(
        self,
        call_abi_method: Literal[False] = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
    ) -> TransactionResponse:
        ...

    @overload
    def opt_in(
        self,
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def opt_in(
        self,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
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
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
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
        call_abi_method: ABIMethod | Literal[True],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> ABITransactionResponse:
        ...

    @overload
    def close_out(
        self,
        call_abi_method: Literal[False],
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
    ) -> TransactionResponse:
        ...

    @overload
    def close_out(
        self,
        call_abi_method: ABIMethod | bool | None = ...,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = ...,
        **abi_kwargs: ABIArgType,
    ) -> TransactionResponse | ABITransactionResponse:
        ...

    def close_out(
        self,
        call_abi_method: ABIMethod | bool | None = None,
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
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
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
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
        transaction_parameters: TransactionParameters | TransactionParametersDict | None = None,
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
        """Gets the global state info associated with app_id"""
        global_state = self.algod_client.application_info(self.app_id)
        assert isinstance(global_state, dict)
        return cast(
            dict[bytes | str, bytes | str | int],
            _decode_state(global_state.get("params", {}).get("global-state", {}), raw=raw),
        )

    def get_local_state(self, account: str | None = None, *, raw: bool = False) -> dict[bytes | str, bytes | str | int]:
        """Gets the local state info for associated app_id and account/sender"""

        if account is None:
            _, account = self.resolve_signer_sender(self.signer, self.sender)

        acct_state = self.algod_client.account_application_info(account, self.app_id)
        assert isinstance(acct_state, dict)
        return cast(
            dict[bytes | str, bytes | str | int],
            _decode_state(acct_state.get("app-local-state", {}).get("key-value", {}), raw=raw),
        )

    def resolve(self, to_resolve: au_spec.DefaultArgumentDict) -> int | str | bytes:
        """Resolves the default value for an ABI method, based on app_spec"""

        def _data_check(value: object) -> int | str | bytes:
            if isinstance(value, int | str | bytes):
                return value
            raise ValueError(f"Unexpected type for constant data: {value}")

        match to_resolve:
            case {"source": "constant", "data": data}:
                return _data_check(data)
            case {"source": "global-state", "data": str() as key}:
                global_state = self.get_global_state(raw=True)
                return global_state[key.encode()]
            case {"source": "local-state", "data": str() as key}:
                _, sender = self.resolve_signer_sender(self.signer, self.sender)
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

    def _get_app_deploy_metadata(
        self, version: str | None, allow_update: bool | None, allow_delete: bool | None
    ) -> au_deploy.AppDeployMetaData:
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

        app = self._load_app_reference()

        if version is None:
            if app.app_id == 0:
                version = "v1.0"
            else:
                assert isinstance(app, au_deploy.AppDeployMetaData)
                version = get_next_version(app.version)
        return au_deploy.AppDeployMetaData(self.app_name, version, updatable=updatable, deletable=deletable)

    def _check_is_compiled(self) -> tuple[Program, Program]:
        if self._approval_program is None or self._clear_program is None:
            self._approval_program, self._clear_program = substitute_template_and_compile(
                self.algod_client, self.app_spec, self.template_values
            )
        return self._approval_program, self._clear_program

    def _simulate_readonly_call(
        self, method: Method, atc: AtomicTransactionComposer
    ) -> ABITransactionResponse | TransactionResponse:
        simulate_response = _simulate_response(atc, self.algod_client)
        traces = None
        if config.debug:
            traces = _create_simulate_traces(simulate_response)
        if simulate_response.failure_message:
            raise _try_convert_to_logic_error(
                simulate_response.failure_message,
                self.app_spec.approval_program,
                self._get_approval_source_map,
                traces,
            ) or Exception(
                f"Simulate failed for readonly method {method.get_signature()}: {simulate_response.failure_message}"
            )

        return TransactionResponse.from_atr(simulate_response)

    def _load_reference_and_check_app_id(self) -> None:
        self._load_app_reference()
        self._check_app_id()

    def _load_app_reference(self) -> au_deploy.AppReference | au_deploy.AppMetaData:
        if not self.existing_deployments and self._creator:
            assert self._indexer_client
            self.existing_deployments = au_deploy.get_creator_apps(self._indexer_client, self._creator)

        if self.existing_deployments:
            app = self.existing_deployments.apps.get(self.app_name)
            if app:
                if self.app_id == 0:
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
        abi_method: ABIMethod | bool | None,
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
            case _:
                return abi_method.method_spec()

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
        if self.approval_source_map:
            return self.approval_source_map

        try:
            approval, _ = self._check_is_compiled()
        except au_deploy.DeploymentFailedError:
            return None
        return approval.source_map

    def export_source_map(self) -> str | None:
        """Export approval source map to JSON, can be later re-imported with `import_source_map`"""
        source_map = self._get_approval_source_map()
        if source_map:
            return json.dumps(
                {
                    "version": source_map.version,
                    "sources": source_map.sources,
                    "mappings": source_map.mappings,
                }
            )
        return None

    def import_source_map(self, source_map_json: str) -> None:
        """Import approval source from JSON exported by `export_source_map`"""
        source_map = json.loads(source_map_json)
        self._approval_source_map = SourceMap(source_map)

    def add_method_call(
        self,
        atc: AtomicTransactionComposer,
        abi_method: ABIMethod | bool | None = None,
        *,
        abi_args: ABIArgsDict | None = None,
        app_id: int | None = None,
        parameters: TransactionParameters | TransactionParametersDict | None = None,
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
        parameters = _convert_transaction_parameters(parameters)
        method = self._resolve_method(abi_method, abi_args, on_complete, call_config)
        sp = parameters.suggested_params or self.suggested_params or self.algod_client.suggested_params()
        signer, sender = self.resolve_signer_sender(parameters.signer, parameters.sender)
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
            return
        # resolve ABI method args
        args = self._get_abi_method_args(abi_args, method)
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

    def _get_abi_method_args(self, abi_args: ABIArgsDict | None, method: Method) -> list:
        args: list = []
        hints = self._method_hints(method)
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
        return args

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

    def _resolve_abi_method(self, method: ABIMethod) -> Method:
        if isinstance(method, str):
            try:
                return next(iter(m for m in self.app_spec.contract.methods if m.get_signature() == method))
            except StopIteration:
                pass
            return self.app_spec.contract.get_method_by_name(method)
        elif hasattr(method, "method_spec"):
            return method.method_spec()
        else:
            return method

    def _method_hints(self, method: Method) -> au_spec.MethodHints:
        sig = method.get_signature()
        if sig not in self.app_spec.hints:
            return au_spec.MethodHints()
        return self.app_spec.hints[sig]

    def _execute_atc_tr(self, atc: AtomicTransactionComposer) -> TransactionResponse:
        result = self.execute_atc(atc)
        return TransactionResponse.from_atr(result)

    def execute_atc(self, atc: AtomicTransactionComposer) -> AtomicTransactionResponse:
        return execute_atc_with_logic_error(
            atc,
            self.algod_client,
            approval_program=self.app_spec.approval_program,
            approval_source_map=self._get_approval_source_map,
        )

    def get_signer_sender(
        self, signer: TransactionSigner | None = None, sender: str | None = None
    ) -> tuple[TransactionSigner | None, str | None]:
        """Return signer and sender, using default values on client if not specified

        Will use provided values if given, otherwise will fall back to values defined on client.
        If no sender is specified then will attempt to obtain sender from signer"""
        resolved_signer = signer or self.signer
        resolved_sender = sender or get_sender_from_signer(signer) or self.sender or get_sender_from_signer(self.signer)
        return resolved_signer, resolved_sender

    def resolve_signer_sender(
        self, signer: TransactionSigner | None = None, sender: str | None = None
    ) -> tuple[TransactionSigner, str]:
        """Return signer and sender, using default values on client if not specified

        Will use provided values if given, otherwise will fall back to values defined on client.
        If no sender is specified then will attempt to obtain sender from signer

        :raises ValueError: Raised if a signer or sender is not provided. See `get_signer_sender`
        for variant with no exception"""
        resolved_signer, resolved_sender = self.get_signer_sender(signer, sender)
        if not resolved_signer:
            raise ValueError("No signer provided")
        if not resolved_sender:
            raise ValueError("No sender provided")
        return resolved_signer, resolved_sender

    # TODO: remove private implementation, kept in the 1.0.2 release to not impact existing beaker 1.0 installs
    _resolve_signer_sender = resolve_signer_sender


def substitute_template_and_compile(
    algod_client: "AlgodClient",
    app_spec: au_spec.ApplicationSpecification,
    template_values: au_deploy.TemplateValueMapping,
) -> tuple[Program, Program]:
    """Substitutes the provided template_values into app_spec and compiles"""
    template_values = dict(template_values or {})
    clear = au_deploy.replace_template_variables(app_spec.clear_program, template_values)

    au_deploy.check_template_variables(app_spec.approval_program, template_values)
    approval = au_deploy.replace_template_variables(app_spec.approval_program, template_values)

    return Program(approval, algod_client), Program(clear, algod_client)


def get_next_version(current_version: str) -> str:
    """Calculates the next version from `current_version`

    Next version is calculated by finding a semver like
    version string and incrementing the lower. This function is used by {py:meth}`ApplicationClient.deploy` when
    a version is not specified, and is intended mostly for convenience during local development.

    :params str current_version: An existing version string with a semver like version contained within it,
    some valid inputs and incremented outputs:
    `1` -> `2`
    `1.0` -> `1.1`
    `v1.1` -> `v1.2`
    `v1.1-beta1` -> `v1.2-beta1`
    `v1.2.3.4567` -> `v1.2.3.4568`
    `v1.2.3.4567-alpha` -> `v1.2.3.4568-alpha`
    :raises DeploymentFailedError: If `current_version` cannot be parsed"""
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


def _try_convert_to_logic_error(
    source_ex: Exception | str,
    approval_program: str,
    approval_source_map: SourceMap | typing.Callable[[], SourceMap | None] | None = None,
    simulate_traces: list | None = None,
) -> Exception | None:
    source_ex_str = str(source_ex)
    logic_error_data = parse_logic_error(source_ex_str)
    if logic_error_data:
        return LogicError(
            logic_error_str=source_ex_str,
            logic_error=source_ex if isinstance(source_ex, Exception) else None,
            program=approval_program,
            source_map=approval_source_map() if callable(approval_source_map) else approval_source_map,
            **logic_error_data,
            traces=simulate_traces,
        )

    return None


def execute_atc_with_logic_error(
    atc: AtomicTransactionComposer,
    algod_client: "AlgodClient",
    approval_program: str,
    wait_rounds: int = 4,
    approval_source_map: SourceMap | typing.Callable[[], SourceMap | None] | None = None,
) -> AtomicTransactionResponse:
    """Calls {py:meth}`AtomicTransactionComposer.execute` on provided `atc`, but will parse any errors
    and raise a {py:class}`LogicError` if possible

    ```{note}
    `approval_program` and `approval_source_map` are required to be able to parse any errors into a
    {py:class}`LogicError`
    ```
    """
    try:
        return atc.execute(algod_client, wait_rounds=wait_rounds)
    except Exception as ex:
        if config.debug:
            simulate = _simulate_response(atc, algod_client)
            traces = _create_simulate_traces(simulate)
        else:
            traces = None
            logger.info("An error occurred while executing the transaction.")
            logger.info("To see more details, enable debug mode by setting config.debug = True ")

        logic_error = _try_convert_to_logic_error(ex, approval_program, approval_source_map, traces)
        if logic_error:
            raise logic_error from ex
        raise ex


def _create_simulate_traces(simulate: SimulateAtomicTransactionResponse) -> list[dict[str, Any]]:
    traces = []
    if hasattr(simulate, "simulate_response") and hasattr(simulate, "failed_at") and simulate.failed_at:
        for txn_group in simulate.simulate_response["txn-groups"]:
            app_budget_added = txn_group.get("app-budget-added", None)
            app_budget_consumed = txn_group.get("app-budget-consumed", None)
            failure_message = txn_group.get("failure-message", None)
            txn_result = txn_group.get("txn-results", [{}])[0]
            exec_trace = txn_result.get("exec-trace", {})
            traces.append(
                {
                    "app-budget-added": app_budget_added,
                    "app-budget-consumed": app_budget_consumed,
                    "failure-message": failure_message,
                    "exec-trace": exec_trace,
                }
            )
    return traces


def _simulate_response(
    atc: AtomicTransactionComposer, algod_client: "AlgodClient"
) -> SimulateAtomicTransactionResponse:
    unsigned_txn_groups = atc.build_group()
    empty_signer = EmptySigner()
    txn_list = [txn_group.txn for txn_group in unsigned_txn_groups]
    fake_signed_transactions = empty_signer.sign_transactions(txn_list, [])
    txn_group = [SimulateRequestTransactionGroup(txns=fake_signed_transactions)]
    trace_config = SimulateTraceConfig(enable=True, stack_change=True, scratch_change=True)

    simulate_request = SimulateRequest(
        txn_groups=txn_group, allow_more_logs=True, allow_empty_signatures=True, exec_trace_config=trace_config
    )
    return atc.simulate(algod_client, simulate_request)


def _convert_transaction_parameters(
    args: TransactionParameters | TransactionParametersDict | None,
) -> CreateCallParameters:
    _args = args.__dict__ if isinstance(args, TransactionParameters) else (args or {})
    return CreateCallParameters(**_args)


def get_sender_from_signer(signer: TransactionSigner | None) -> str | None:
    """Returns the associated address of a signer, return None if no address found"""

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
    return None


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
            if len(result_bytes) < len(ABI_RETURN_HASH) or result_bytes[: len(ABI_RETURN_HASH)] != ABI_RETURN_HASH:
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
