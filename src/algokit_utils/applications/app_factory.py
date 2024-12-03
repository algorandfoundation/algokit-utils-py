import base64
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, cast

from algosdk import transaction
from algosdk.abi import Method
from algosdk.atomic_transaction_composer import TransactionSigner

from algokit_utils._legacy_v2.deploy import (
    AppDeployMetaData,
    AppLookup,
    OnSchemaBreak,
    OnUpdate,
)
from algokit_utils.applications.app_client import (
    AppClient,
    AppClientBareCallParams,
    AppClientCompilationParams,
    AppClientMethodCallParams,
    AppClientParams,
    ExposedLogicErrorDetails,
)
from algokit_utils.applications.app_manager import TealTemplateParams
from algokit_utils.applications.utils import (
    get_abi_decoded_value,
    get_abi_struct_from_abi_tuple,
    get_abi_tuple_from_abi_struct,
    get_arc56_method,
)
from algokit_utils.models.application import DELETABLE_TEMPLATE_NAME, UPDATABLE_TEMPLATE_NAME, Arc56Contract
from algokit_utils.protocols.application import AlgorandClientProtocol
from algokit_utils.transactions.transaction_composer import AppCreateParams
from algokit_utils.transactions.transaction_sender import SendAppTransactionResult

if TYPE_CHECKING:
    from algosdk.source_map import SourceMap


T = TypeVar("T")


class ParamsMethodsProtocol(Protocol):
    def create(self, params: AppClientMethodCallParams) -> dict[str, Any]: ...
    def deploy_update(self, params: AppClientMethodCallParams) -> dict[str, Any]: ...
    def deploy_delete(self, params: AppClientMethodCallParams) -> dict[str, Any]: ...

    bare: dict[str, Callable[[AppClientBareCallParams | None], dict[str, Any]]]


@dataclass(kw_only=True)
class AppFactoryParams:
    app_spec: Arc56Contract | str
    algorand: AlgorandClientProtocol
    app_name: str | None = None
    default_sender: str | bytes | None = None
    default_signer: TransactionSigner | None = None
    version: str | None = None
    updatable: bool | None = None
    deletable: bool | None = None
    deploy_time_params: TealTemplateParams | None = None


@dataclass(kw_only=True, frozen=True)
class AppFactoryCreateParams(AppClientBareCallParams, AppClientCompilationParams):
    on_complete: transaction.OnComplete | None = None
    schema: dict[str, int] | None = None
    extra_program_pages: int | None = None


@dataclass(kw_only=True, frozen=True)
class AppFactoryCreateMethodCallParams(AppClientMethodCallParams, AppClientCompilationParams):
    on_complete: transaction.OnComplete | None = None
    schema: dict[str, int] | None = None
    extra_program_pages: int | None = None


@dataclass(kw_only=True, frozen=True)
class AppFactoryDeployParams:
    version: str | None = None
    signer: TransactionSigner | None = None
    sender: str | None = None
    allow_update: bool | None = None
    allow_delete: bool | None = None
    on_update: OnUpdate = OnUpdate.Fail
    on_schema_break: OnSchemaBreak = OnSchemaBreak.Fail
    template_values: TealTemplateParams | None = None
    create_args: AppClientMethodCallParams | AppClientBareCallParams | None = None
    update_args: AppClientMethodCallParams | AppClientBareCallParams | None = None
    delete_args: AppClientMethodCallParams | AppClientBareCallParams | None = None
    existing_deployments: AppLookup | None = None
    ignore_cache: bool = False
    updatable: bool | None = None
    deletable: bool | None = None
    app_name: str | None = None


class AppFactory:
    def __init__(self, params: AppFactoryParams) -> None:
        self._app_spec = AppClient.normalise_app_spec(params.app_spec)
        self._app_name = params.app_name or self._app_spec.name
        self._algorand = params.algorand
        self._version = params.version or "1.0"
        self._default_sender = params.default_sender
        self._default_signer = params.default_signer
        self._deploy_time_params = params.deploy_time_params
        self._updatable = params.updatable
        self._deletable = params.deletable
        self._approval_source_map: SourceMap | None = None
        self._clear_source_map: SourceMap | None = None

    @property
    def app_name(self) -> str:
        return self._app_name

    @property
    def app_spec(self) -> Arc56Contract:
        return self._app_spec

    @property
    def algorand(self) -> AlgorandClientProtocol:
        return self._algorand

    def get_app_client_by_id(self, params: AppClientParams) -> AppClient:
        return AppClient(
            AppClientParams(
                app_id=params.app_id,
                algorand=self._algorand,
                app_spec=self._app_spec,
                app_name=params.app_name or self._app_name,
                default_sender=params.default_sender or self._default_sender,
                default_signer=params.default_signer or self._default_signer,
                approval_source_map=params.approval_source_map or self._approval_source_map,
                clear_source_map=params.clear_source_map or self._clear_source_map,
            )
        )

    def create_bare(self, params: AppFactoryCreateParams | None = None) -> tuple[AppClient, SendAppTransactionResult]:
        updatable = params.updatable if params and params.updatable is not None else self._updatable
        deletable = params.deletable if params and params.deletable is not None else self._deletable
        deploy_time_params = (
            params.deploy_time_params if params and params.deploy_time_params is not None else self._deploy_time_params
        )

        compiled = self.compile(
            AppClientCompilationParams(
                deploy_time_params=deploy_time_params,
                updatable=updatable,
                deletable=deletable,
            )
        )

        result = self._handle_call_errors(
            lambda: self._algorand.send.app_create(
                self._get_bare_params(
                    params=AppCreateParams(
                        **(params.__dict__ if params else {}),
                        updatable=updatable,
                        deletable=deletable,
                        deploy_time_params=deploy_time_params,
                    ),
                    on_complete=params.on_complete if params else transaction.OnComplete.NoOpOC,
                )
            )
        )

        return (
            self.get_app_client_by_id(
                AppClientParams(app_id=result.app_id, app_spec=self._app_spec, algorand=self._algorand)
            ),
            SendAppTransactionResult(**{**result.__dict__, **(compiled.__dict__ if compiled else {})}),
        )

    def create(self, params: AppFactoryCreateMethodCallParams) -> tuple[AppClient, SendAppTransactionResult]:
        updatable = params.updatable if params.updatable is not None else self._updatable
        deletable = params.deletable if params.deletable is not None else self._deletable
        deploy_time_params = (
            params.deploy_time_params if params.deploy_time_params is not None else self._deploy_time_params
        )

        compiled = self.compile(
            AppClientCompilationParams(
                deploy_time_params=deploy_time_params,
                updatable=updatable,
                deletable=deletable,
            )
        )

        result = self._handle_call_errors(
            lambda: self._get_arc56_return_value(
                self._algorand.send.app_create_method_call(
                    self._get_abi_params(
                        {
                            **params.__dict__,
                            "updatable": updatable,
                            "deletable": deletable,
                            "deploy_time_params": deploy_time_params,
                        },
                        params.on_complete or transaction.OnComplete.NoOpOC,
                    )
                ),
                get_arc56_method(params.method, self._app_spec),
            )
        )

        return (
            self.get_app_client_by_id(
                AppClientParams(app_id=result.app_id, app_spec=self._app_spec, algorand=self._algorand)
            ),
            SendAppTransactionResult(**{**result.__dict__, **(compiled.__dict__ if compiled else {})}),
        )

    def deploy(self, params: AppFactoryDeployParams) -> tuple[AppClient, SendAppTransactionResult]:
        updatable = params.updatable if params.updatable is not None else self._updatable
        deletable = params.deletable if params.deletable is not None else self._deletable
        deploy_time_params = params.template_values

        compiled = self.compile(
            AppClientCompilationParams(
                deploy_time_params=deploy_time_params,
                updatable=updatable,
                deletable=deletable,
            )
        )

        deploy_result = self._algorand.app_deployer.deploy(
            {
                **params.__dict__,
                "create_params": (
                    self._get_abi_params(params.create_args.__dict__, transaction.OnComplete.NoOpOC)
                    if params.create_args and hasattr(params.create_args, "method")
                    else self._get_bare_params(
                        params.create_args.__dict__ if params.create_args else {},
                        transaction.OnComplete.NoOpOC,
                    )
                )
                if params.create_args
                else None,
                "update_params": (
                    self._get_abi_params(params.update_args.__dict__, transaction.OnComplete.UpdateApplicationOC)
                    if params.update_args and hasattr(params.update_args, "method")
                    else self._get_bare_params(
                        params.update_args.__dict__ if params.update_args else {},
                        transaction.OnComplete.UpdateApplicationOC,
                    )
                )
                if params.update_args
                else None,
                "delete_params": (
                    self._get_abi_params(params.delete_args.__dict__, transaction.OnComplete.DeleteApplicationOC)
                    if params.delete_args and hasattr(params.delete_args, "method")
                    else self._get_bare_params(
                        params.delete_args.__dict__ if params.delete_args else {},
                        transaction.OnComplete.DeleteApplicationOC,
                    )
                )
                if params.delete_args
                else None,
                "metadata": AppDeployMetaData(
                    name=params.app_name or self._app_name,
                    version=self._version,
                    updatable=updatable,
                    deletable=deletable,
                ),
            }
        )

        app_client = self.get_app_client_by_id(
            AppClientParams(
                app_id=deploy_result.app_id, app_name=params.app_name, app_spec=self._app_spec, algorand=self._algorand
            )
        )

        result = {**deploy_result.__dict__, **(compiled.__dict__ if compiled else {})}

        return_value = None
        if hasattr(result, "return"):
            if result["operationPerformed"] == "update":
                if params.update_args and hasattr(params.update_args, "method"):
                    return_value = self._get_arc56_return_value(
                        result["return"],
                        get_arc56_method(params.update_args.method, self._app_spec),
                    )
            elif params.create_args and hasattr(params.create_args, "method"):
                return_value = self._get_arc56_return_value(
                    result["return"],
                    get_arc56_method(params.create_args.method, self._app_spec),
                )

        delete_return = None
        if hasattr(result, "deleteReturn") and params.delete_args and hasattr(params.delete_args, "method"):
            delete_return = self._get_arc56_return_value(
                result["deleteReturn"],
                get_arc56_method(params.delete_args.method, self._app_spec),
            )

        result["return"] = return_value
        result["deleteReturn"] = delete_return

        return app_client, SendAppTransactionResult(**result)

    def compile(self, compilation: AppClientCompilationParams | None = None) -> Any:
        result = AppClient.compile(
            self._app_spec,
            self._algorand.app,
            cast(TealTemplateParams | None, compilation.deploy_time_params if compilation else None),
        )

        if result.compiled_approval:
            self._approval_source_map = result.compiled_approval.source_map
        if result.compiled_clear:
            self._clear_source_map = result.compiled_clear.source_map

        return result

    def _handle_call_errors(self, call: Callable[[], T]) -> T:
        try:
            return call()
        except Exception as e:
            raise self.expose_logic_error(e) from None

    def expose_logic_error(self, e: Exception, is_clear_state_program: bool = False) -> Exception:
        return AppClient.expose_logic_error_static(
            e,
            self._app_spec,
            ExposedLogicErrorDetails(
                is_clear_state_program=is_clear_state_program,
                approval_source_map=self._approval_source_map,
                clear_source_map=self._clear_source_map,
                program=None,
                approval_source_info=None,
                clear_source_info=None,
            ),
        )

    def _get_arc56_return_value(self, return_value: Any, method: Method) -> Any:
        if method.returns.type == "void" or return_value is None:
            return None

        if hasattr(return_value, "decode_error"):
            raise ValueError(return_value["decode_error"])

        raw_value = return_value.get("raw_return_value")

        if method.returns.type == "AVMBytes":
            return raw_value
        if method.returns.type == "AVMString" and raw_value:
            return raw_value.decode("utf-8")
        if method.returns.type == "AVMUint64" and raw_value:
            return get_abi_decoded_value(raw_value, "uint64", self._app_spec.structs)

        if method.returns.struct and method.returns.struct in self._app_spec.structs:
            return_tuple = return_value.get("return_value")
            return get_abi_struct_from_abi_tuple(
                return_tuple, self._app_spec.structs[method.returns.struct], self._app_spec.structs
            )

        return return_value.get("return_value")

    def _get_deploy_time_control(self, control: str) -> bool | None:
        approval = (
            base64.b64decode(self._app_spec.source["approval"]).decode("utf-8")
            if self._app_spec.source and "approval" in self._app_spec.source
            else None
        )

        template_name = UPDATABLE_TEMPLATE_NAME if control == "updatable" else DELETABLE_TEMPLATE_NAME
        if not approval or template_name not in approval:
            return None

        on_complete = "UpdateApplication" if control == "updatable" else "DeleteApplication"
        return on_complete in self._app_spec.bare_actions.get("call", []) or any(
            m.actions.call and on_complete in m.actions.call for m in self._app_spec.methods
        )

    @property
    def params(self) -> ParamsMethodsProtocol:
        return cast(ParamsMethodsProtocol, self._get_params_methods())

    def _get_params_methods(self) -> dict[str, Any]:
        return {
            "create": lambda params: self._get_abi_params(
                {
                    **params.__dict__,
                    "deploy_time_params": params.deploy_time_params or self._deploy_time_params,
                    "schema": params.schema
                    or {
                        "global_bytes": self._app_spec.state.schemas["global"]["bytes"],
                        "global_ints": self._app_spec.state.schemas["global"]["ints"],
                        "local_bytes": self._app_spec.state.schemas["local"]["bytes"],
                        "local_ints": self._app_spec.state.schemas["local"]["ints"],
                    },
                    "approval_program": self.compile(params).approval_program,
                    "clear_state_program": self.compile(params).clear_state_program,
                },
                params.on_complete or transaction.OnComplete.NoOpOC,
            ),
            "deploy_update": lambda params: self._get_abi_params(
                params.__dict__, transaction.OnComplete.UpdateApplicationOC
            ),
            "deploy_delete": lambda params: self._get_abi_params(
                params.__dict__, transaction.OnComplete.DeleteApplicationOC
            ),
            "bare": {
                "create": lambda params: self._get_bare_params(
                    {
                        **(params.__dict__ if params else {}),
                        "deploy_time_params": (params.deploy_time_params if params else None)
                        or self._deploy_time_params,
                        "schema": (params.schema if params else None)
                        or {
                            "global_bytes": self._app_spec.state.schemas["global"]["bytes"],
                            "global_ints": self._app_spec.state.schemas["global"]["ints"],
                            "local_bytes": self._app_spec.state.schemas["local"]["bytes"],
                            "local_ints": self._app_spec.state.schemas["local"]["ints"],
                        },
                        **(self.compile(params).__dict__ if params else {}),
                    },
                    (params.on_complete if params else None) or transaction.OnComplete.NoOpOC,
                ),
                "deploy_update": lambda params: self._get_bare_params(
                    params.__dict__ if params else {}, transaction.OnComplete.UpdateApplicationOC
                ),
                "deploy_delete": lambda params: self._get_bare_params(
                    params.__dict__ if params else {}, transaction.OnComplete.DeleteApplicationOC
                ),
            },
        }

    def _get_bare_params(self, params: dict[str, Any], on_complete: transaction.OnComplete) -> dict[str, Any]:
        return {
            **params,
            "sender": self._get_sender(params.get("sender")),
            "on_complete": on_complete,
        }

    def _get_abi_params(self, params: dict[str, Any], on_complete: transaction.OnComplete) -> dict[str, Any]:
        return {
            **params,
            "sender": self._get_sender(params.get("sender")),
            "method": get_arc56_method(params["method"], self._app_spec),
            "args": self._get_create_abi_args_with_default_values(params["method"], params.get("args")),
            "on_complete": on_complete,
        }

    def _get_sender(self, sender: str | bytes | None) -> str:
        if not sender and not self._default_sender:
            raise Exception(
                f"No sender provided and no default sender present in app client for call to app {self._app_name}"
            )
        return str(sender or self._default_sender)

    def _get_create_abi_args_with_default_values(
        self, method_name_or_signature: str, args: list[Any] | None
    ) -> list[Any]:
        method = get_arc56_method(method_name_or_signature, self._app_spec)
        result = []

        for i, method_arg in enumerate(method.args):
            arg_value = args[i] if args and i < len(args) else None

            if arg_value is not None:
                if hasattr(method_arg, "struct") and method_arg.struct and isinstance(arg_value, dict):
                    arg_value = get_abi_tuple_from_abi_struct(
                        arg_value, self._app_spec.structs[method_arg.struct], self._app_spec.structs
                    )
                result.append(arg_value)
                continue

            if hasattr(method_arg, "default_value") and method_arg.default_value:
                if method_arg.default_value.source == "literal":
                    value_raw = base64.b64decode(method_arg.default_value.data)
                    value_type = method_arg.default_value.type or str(method_arg.type)
                    result.append(get_abi_decoded_value(value_raw, value_type, self._app_spec.structs))
                else:
                    raise ValueError(
                        f"Can't provide default value for {method_arg.default_value.source} for a contract creation call"
                    )
            else:
                raise ValueError(
                    f"No value provided for required argument {method_arg.name or f'arg{i+1}'} in call to method {method.name}"
                )

        return result
