import base64
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeGuard, TypeVar

import algosdk
from algosdk import transaction
from algosdk.abi import Method
from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.source_map import SourceMap
from algosdk.transaction import OnComplete, Transaction

from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils._legacy_v2.deploy import AppDeployMetaData, AppLookup, OnSchemaBreak, OnUpdate, OperationPerformed
from algokit_utils.applications.app_client import (
    AppClient,
    AppClientBareCallParams,
    AppClientCompilationParams,
    AppClientCompilationResult,
    AppClientMethodCallParams,
    AppClientParams,
    AppSourceMaps,
    ExposedLogicErrorDetails,
)
from algokit_utils.applications.app_deployer import AppDeployParams, DeployAppDeleteParams, DeployAppUpdateParams
from algokit_utils.applications.app_manager import TealTemplateParams
from algokit_utils.applications.utils import (
    get_abi_decoded_value,
    get_abi_tuple_from_abi_struct,
    get_arc56_method,
    get_arc56_return_value,
)
from algokit_utils.models.application import (
    DELETABLE_TEMPLATE_NAME,
    UPDATABLE_TEMPLATE_NAME,
    Arc56Contract,
    Arc56Method,
    CompiledTeal,
    MethodArg,
)
from algokit_utils.models.transaction import SendParams
from algokit_utils.protocols.application import AlgorandClientProtocol
from algokit_utils.transactions.transaction_composer import (
    AppCreateMethodCall,
    AppCreateParams,
    AppDeleteMethodCall,
    AppUpdateMethodCall,
    BuiltTransactions,
)
from algokit_utils.transactions.transaction_sender import SendAppTransactionResult

T = TypeVar("T")


@dataclass(kw_only=True, frozen=True)
class AppFactoryParams:
    algorand: AlgorandClientProtocol
    app_spec: Arc56Contract | ApplicationSpecification | str
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
class AppFactoryCreateWithSendParams(AppFactoryCreateParams, SendParams):
    pass


@dataclass(kw_only=True, frozen=True)
class AppFactoryCreateMethodCallParams(AppClientMethodCallParams, AppClientCompilationParams):
    on_complete: transaction.OnComplete | None = None
    schema: dict[str, int] | None = None
    extra_program_pages: int | None = None


@dataclass(kw_only=True, frozen=True)
class AppFactoryCreateMethodCallWithSendParams(AppFactoryCreateMethodCallParams, SendParams):
    pass


@dataclass(frozen=True, kw_only=True)
class AppFactoryCreateResult(SendAppTransactionResult):
    """Result from creating an application via AppFactory"""

    app_id: int
    """The ID of the created application"""
    app_address: str
    """The address of the created application"""
    compiled_approval: CompiledTeal | None = None
    """The compiled approval program if source was provided"""
    compiled_clear: CompiledTeal | None = None
    """The compiled clear program if source was provided"""


@dataclass(kw_only=True, frozen=True)
class AppFactoryDeployResult:
    """Represents the result object from app deployment"""

    app_address: str
    app_id: int
    approval_program: bytes  # Uint8Array
    clear_state_program: bytes  # Uint8Array
    compiled_approval: dict  # Contains teal, compiled, compiledHash, compiledBase64ToBytes, sourceMap
    compiled_clear: dict  # Contains teal, compiled, compiledHash, compiledBase64ToBytes, sourceMap
    confirmation: algosdk.v2client.algod.AlgodResponseType
    confirmations: list[algosdk.v2client.algod.AlgodResponseType] | None = None
    created_metadata: dict  # {name: str, version: str, updatable: bool, deletable: bool}
    created_round: int
    deletable: bool
    deleted: bool
    delete_return: Any | None = None
    group_id: str | None = None
    name: str
    operation_performed: OperationPerformed
    return_value: Any | None = None
    returns: list[Any] | None = None
    transaction: Transaction
    transactions: list[Transaction]
    tx_id: str
    tx_ids: list[str]
    updatable: bool
    updated_round: int
    version: str


class _AppFactoryBareParamsAccessor:
    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._algorand = factory._algorand

    def create(self, params: AppFactoryCreateParams | None = None) -> AppCreateParams:
        create_args = {}
        if params:
            create_args = {**params.__dict__}
            del create_args["schema"]
            del create_args["sender"]
            del create_args["on_complete"]
            del create_args["deploy_time_params"]
            del create_args["updatable"]
            del create_args["deletable"]
            compiled = self._factory.compile(params)
            create_args["approval_program"] = compiled.approval_program
            create_args["clear_state_program"] = compiled.clear_state_program

        return AppCreateParams(
            **create_args,
            schema=(params.schema if params else None)
            or {
                "global_bytes": self._factory._app_spec.state.schemas["global"]["bytes"],
                "global_ints": self._factory._app_spec.state.schemas["global"]["ints"],
                "local_bytes": self._factory._app_spec.state.schemas["local"]["bytes"],
                "local_ints": self._factory._app_spec.state.schemas["local"]["ints"],
            },
            sender=self._factory._get_sender(params.sender if params else None),
            on_complete=(params.on_complete if params else None) or OnComplete.NoOpOC,
        )

    def deploy_update(self, params: AppClientBareCallParams | None = None) -> dict[str, Any]:
        return {
            **(params.__dict__ if params else {}),
            "sender": self._factory._get_sender(params.sender if params else None),
            "on_complete": OnComplete.UpdateApplicationOC,
        }

    def deploy_delete(self, params: AppClientBareCallParams | None = None) -> dict[str, Any]:
        return {
            **(params.__dict__ if params else {}),
            "sender": self._factory._get_sender(params.sender if params else None),
            "on_complete": OnComplete.DeleteApplicationOC,
        }


class _AppFactoryParamsAccessor:
    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._bare = _AppFactoryBareParamsAccessor(factory)

    @property
    def bare(self) -> _AppFactoryBareParamsAccessor:
        return self._bare

    def create(self, params: AppFactoryCreateMethodCallParams) -> AppCreateMethodCall:
        compiled = self._factory.compile(params)
        params_dict = params.__dict__
        params_dict["schema"] = params.schema or {
            "global_bytes": self._factory._app_spec.state.schemas["global"]["bytes"],
            "global_ints": self._factory._app_spec.state.schemas["global"]["ints"],
            "local_bytes": self._factory._app_spec.state.schemas["local"]["bytes"],
            "local_ints": self._factory._app_spec.state.schemas["local"]["ints"],
        }
        params_dict["sender"] = self._factory._get_sender(params.sender)
        params_dict["method"] = get_arc56_method(params.method, self._factory._app_spec)
        params_dict["args"] = self._factory._get_create_abi_args_with_default_values(params.method, params.args)
        params_dict["on_complete"] = params.on_complete or OnComplete.NoOpOC
        del params_dict["deploy_time_params"]
        del params_dict["updatable"]
        del params_dict["deletable"]
        return AppCreateMethodCall(
            **params_dict,
            app_id=0,
            approval_program=compiled.approval_program,
            clear_state_program=compiled.clear_state_program,
        )

    def deploy_update(self, params: AppClientMethodCallParams) -> AppUpdateMethodCall:
        return AppUpdateMethodCall(
            **params.__dict__,
            sender=self._factory._get_sender(params.sender),
            method=get_arc56_method(params.method, self._factory._app_spec),
            args=self._factory._get_create_abi_args_with_default_values(params.method, params.args),
            on_complete=OnComplete.UpdateApplicationOC,
        )

    def deploy_delete(self, params: AppClientMethodCallParams) -> AppDeleteMethodCall:
        return AppDeleteMethodCall(
            **params.__dict__,
            sender=self._factory._get_sender(params.sender),
            method=get_arc56_method(params.method, self._factory._app_spec),
            args=self._factory._get_create_abi_args_with_default_values(params.method, params.args),
            on_complete=OnComplete.DeleteApplicationOC,
        )


class _AppFactoryBareCreateTransactionAccessor:
    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory

    def create(self, params: AppFactoryCreateParams | None = None) -> Transaction:
        return self._factory._algorand.create_transaction.app_create(self._factory.params.bare.create(params))


class _AppFactoryCreateTransactionAccessor:
    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._bare = _AppFactoryBareCreateTransactionAccessor(factory)

    @property
    def bare(self) -> _AppFactoryBareCreateTransactionAccessor:
        return self._bare

    def create(self, params: AppFactoryCreateMethodCallParams) -> BuiltTransactions:
        return self._factory._algorand.create_transaction.app_create_method_call(self._factory.params.create(params))


class _AppFactoryBareSendAccessor:
    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._algorand = factory._algorand

    def create(self, params: AppFactoryCreateWithSendParams | None = None) -> tuple[AppClient, AppFactoryCreateResult]:
        updatable = params.updatable if params and params.updatable is not None else self._factory._updatable
        deletable = params.deletable if params and params.deletable is not None else self._factory._deletable
        deploy_time_params = (
            params.deploy_time_params
            if params and params.deploy_time_params is not None
            else self._factory._deploy_time_params
        )

        compiled = self._factory.compile(
            AppClientCompilationParams(
                deploy_time_params=deploy_time_params,
                updatable=updatable,
                deletable=deletable,
            )
        )

        create_args = {}
        if params:
            create_args = {**params.__dict__}
            del create_args["max_rounds_to_wait"]
            del create_args["suppress_log"]
            del create_args["populate_app_call_resources"]

        create_args["updatable"] = updatable
        create_args["deletable"] = deletable
        create_args["deploy_time_params"] = deploy_time_params

        result = self._factory._handle_call_errors(
            lambda: self._algorand.send.app_create(
                self._factory.params.bare.create(AppFactoryCreateParams(**create_args))
            )
        ).__dict__

        result["compiled_approval"] = compiled.compiled_approval
        result["compiled_clear"] = compiled.compiled_clear

        return (
            self._factory.get_app_client_by_id(
                app_id=result["app_id"],
            ),
            AppFactoryCreateResult(**result),
        )


class _AppFactorySendAccessor:
    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._algorand = factory._algorand
        self._bare = _AppFactoryBareSendAccessor(factory)

    @property
    def bare(self) -> _AppFactoryBareSendAccessor:
        return self._bare

    def create(self, params: AppFactoryCreateMethodCallParams) -> tuple[AppClient, AppFactoryDeployResult]:
        updatable = params.updatable if params.updatable is not None else self._factory._updatable
        deletable = params.deletable if params.deletable is not None else self._factory._deletable
        deploy_time_params = (
            params.deploy_time_params if params.deploy_time_params is not None else self._factory._deploy_time_params
        )

        compiled = self._factory.compile(
            AppClientCompilationParams(
                deploy_time_params=deploy_time_params,
                updatable=updatable,
                deletable=deletable,
            )
        )

        result = self._factory._handle_call_errors(
            lambda: self._algorand.send.app_create_method_call(
                self._factory.params.create(
                    AppFactoryCreateMethodCallParams(
                        **params.__dict__,
                        updatable=updatable,
                        deletable=deletable,
                        deploy_time_params=deploy_time_params,
                    )
                )
            )
        )

        return (
            self._factory.get_app_client_by_id(
                app_id=result.app_id,
            ),
            AppFactoryDeployResult(**{**result.__dict__, **(compiled.__dict__ if compiled else {})}),
        )


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
        self._params_accessor = _AppFactoryParamsAccessor(self)
        self._send_accessor = _AppFactorySendAccessor(self)
        self._create_transaction_accessor = _AppFactoryCreateTransactionAccessor(self)

    @property
    def app_name(self) -> str:
        return self._app_name

    @property
    def app_spec(self) -> Arc56Contract:
        return self._app_spec

    @property
    def algorand(self) -> AlgorandClientProtocol:
        return self._algorand

    @property
    def params(self) -> _AppFactoryParamsAccessor:
        return self._params_accessor

    @property
    def send(self) -> _AppFactorySendAccessor:
        return self._send_accessor

    @property
    def create_transaction(self) -> _AppFactoryCreateTransactionAccessor:
        return self._create_transaction_accessor

    def deploy(
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
    ) -> tuple[AppClient, AppFactoryDeployResult]:
        updatable = (
            updatable if updatable is not None else self._updatable or self._get_deploy_time_control("updatable")
        )
        deletable = (
            deletable if deletable is not None else self._deletable or self._get_deploy_time_control("deletable")
        )
        deploy_time_params = deploy_time_params if deploy_time_params is not None else self._deploy_time_params

        compiled = self.compile(
            AppClientCompilationParams(
                deploy_time_params=deploy_time_params,
                updatable=updatable,
                deletable=deletable,
            )
        )

        def _is_method_call_params(
            params: AppClientMethodCallParams | AppClientBareCallParams | None,
        ) -> TypeGuard[AppClientMethodCallParams]:
            return params is not None and hasattr(params, "method")

        update_args: DeployAppUpdateParams | AppUpdateMethodCall
        if _is_method_call_params(update_params):
            update_args = self.params.deploy_update(update_params)  # type: ignore[arg-type]
        else:
            update_args = DeployAppUpdateParams(
                **self.params.bare.deploy_update(
                    update_params if isinstance(update_params, AppClientBareCallParams) else None
                )
            )

        delete_args: DeployAppDeleteParams | AppDeleteMethodCall
        if _is_method_call_params(delete_params):
            delete_args = self.params.deploy_delete(delete_params)  # type: ignore[arg-type]
        else:
            delete_args = DeployAppDeleteParams(
                **self.params.bare.deploy_delete(
                    delete_params if isinstance(delete_params, AppClientBareCallParams) else None
                )
            )

        app_deploy_params = AppDeployParams(
            deploy_time_params=deploy_time_params,
            on_schema_break=on_schema_break,
            on_update=on_update,
            existing_deployments=existing_deployments,
            ignore_cache=ignore_cache,
            create_params=(
                self.params.create(
                    AppFactoryCreateMethodCallParams(
                        **create_params.__dict__,
                        updatable=updatable,
                        deletable=deletable,
                        deploy_time_params=deploy_time_params,
                    )
                )
                if create_params and hasattr(create_params, "method")
                else self.params.bare.create(
                    AppFactoryCreateParams(
                        **create_params.__dict__ if create_params else {},
                        updatable=updatable,
                        deletable=deletable,
                        deploy_time_params=deploy_time_params,
                    )
                )
            ),
            update_params=update_args,
            delete_params=delete_args,
            metadata=AppDeployMetaData(
                name=app_name or self._app_name,
                version=self._version,
                updatable=updatable,
                deletable=deletable,
            ),
        )
        deploy_result = self._algorand.app_deployer.deploy(app_deploy_params)

        app_client = self.get_app_client_by_id(
            app_id=deploy_result.app_id or 0,
            app_name=app_name,
            default_sender=self._default_sender,
            default_signer=self._default_signer,
        )

        result = {**deploy_result.__dict__, **(compiled.__dict__ if compiled else {})}

        if hasattr(result, "return_value"):
            if result["operation_performed"] == "update":
                if update_params and hasattr(update_params, "method"):
                    result["return_value"] = get_arc56_return_value(
                        result["return_value"],
                        get_arc56_method(update_params.method, self._app_spec),  # type: ignore[arg-type]
                        self._app_spec.structs,
                    )
            elif create_params and hasattr(create_params, "method"):
                result["return_value"] = get_arc56_return_value(
                    result["return_value"],
                    get_arc56_method(create_params.method, self._app_spec),  # type: ignore[arg-type]
                    self._app_spec.structs,
                )

        if "delete_return" in result and delete_params and hasattr(delete_params, "method"):
            result["delete_return"] = get_arc56_return_value(
                result["delete_return"],
                get_arc56_method(delete_params.method, self._app_spec),  # type: ignore[arg-type]
                self._app_spec.structs,
            )

        del result["delete_result"]
        result["transactions"] = []
        result["tx_id"] = ""
        result["tx_ids"] = []

        return app_client, AppFactoryDeployResult(**result)

    def get_app_client_by_id(
        self,
        app_id: int,
        app_name: str | None = None,
        default_sender: str | bytes | None = None,  # Address can be string or bytes
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
        return AppClient(
            AppClientParams(
                app_id=app_id,
                algorand=self._algorand,
                app_spec=self._app_spec,
                app_name=app_name or self._app_name,
                default_sender=default_sender or self._default_sender,
                default_signer=default_signer or self._default_signer,
                approval_source_map=approval_source_map or self._approval_source_map,
                clear_source_map=clear_source_map or self._clear_source_map,
            )
        )

    def expose_logic_error(self, e: Exception, is_clear_state_program: bool = False) -> Exception:
        return AppClient.expose_logic_error_static(
            e,
            self._app_spec,
            ExposedLogicErrorDetails(
                is_clear_state_program=is_clear_state_program,
                approval_source_map=self._approval_source_map,
                clear_source_map=self._clear_source_map,
                program=None,
                approval_source_info=(
                    self._app_spec.source_info.get("approval")
                    if self._app_spec.source_info and hasattr(self._app_spec, "source_info")
                    else None
                ),
                clear_source_info=(
                    self._app_spec.source_info.get("clear")
                    if self._app_spec.source_info and hasattr(self._app_spec, "source_info")
                    else None
                ),
            ),
        )

    def export_source_maps(self) -> AppSourceMaps:
        if not self._approval_source_map or not self._clear_source_map:
            raise ValueError(
                "Unable to export source maps; they haven't been loaded into this client - "
                "you need to call create, update, or deploy first"
            )
        return AppSourceMaps(
            approval_source_map=self._approval_source_map,
            clear_source_map=self._clear_source_map,
        )

    def import_source_maps(self, source_maps: AppSourceMaps) -> None:
        self._approval_source_map = source_maps.approval_source_map
        self._clear_source_map = source_maps.clear_source_map

    def compile(self, compilation: AppClientCompilationParams | None = None) -> AppClientCompilationResult:
        result = AppClient.compile(
            self._app_spec,
            self._algorand.app,
            deploy_time_params=compilation.deploy_time_params if compilation else None,
            updatable=compilation.updatable if compilation else None,
            deletable=compilation.deletable if compilation else None,
        )

        if result.compiled_approval:
            self._approval_source_map = result.compiled_approval.source_map
        if result.compiled_clear:
            self._clear_source_map = result.compiled_clear.source_map

        return result

    def _get_deploy_time_control(self, control: str) -> bool | None:
        approval = (
            self._app_spec.source["approval"] if self._app_spec.source and "approval" in self._app_spec.source else None
        )

        template_name = UPDATABLE_TEMPLATE_NAME if control == "updatable" else DELETABLE_TEMPLATE_NAME
        if not approval or template_name not in approval:
            return None

        on_complete = "UpdateApplication" if control == "updatable" else "DeleteApplication"
        return on_complete in self._app_spec.bare_actions.get("call", []) or any(
            on_complete in m.actions.call for m in self._app_spec.methods if m.actions and m.actions.call
        )

    def _get_sender(self, sender: str | bytes | None) -> str:
        if not sender and not self._default_sender:
            raise Exception(
                f"No sender provided and no default sender present in app client for call to app {self._app_name}"
            )
        return str(sender or self._default_sender)

    def _handle_call_errors(self, call: Callable[[], T]) -> T:
        try:
            return call()
        except Exception as e:
            raise self.expose_logic_error(e) from None

    def _parse_method_call_return(self, result: SendAppTransactionResult, method: Method) -> SendAppTransactionResult:
        return_value = result.return_value
        if isinstance(return_value, dict):
            return_value = get_arc56_return_value(return_value, method, self._app_spec.structs)
        return SendAppTransactionResult(
            **{
                **result.__dict__,
                "return_value": return_value,
            }
        )

    def _get_create_abi_args_with_default_values(
        self,
        method_name_or_signature: str | Arc56Method,
        args: list[Any] | None,
    ) -> list[Any]:
        method = (
            get_arc56_method(method_name_or_signature, self._app_spec)
            if isinstance(method_name_or_signature, str)
            else method_name_or_signature
        )
        result = []

        def _has_struct(arg: Any) -> TypeGuard[MethodArg]:  # noqa: ANN401
            return hasattr(arg, "struct")

        for i, method_arg in enumerate(method.args):
            arg = method_arg
            arg_value = args[i] if args and i < len(args) else None

            if arg_value is not None:
                if _has_struct(arg) and arg.struct and isinstance(arg_value, dict):
                    arg_value = get_abi_tuple_from_abi_struct(
                        arg_value,
                        self._app_spec.structs[arg.struct],
                        self._app_spec.structs,
                    )
                result.append(arg_value)
                continue

            default_value = getattr(arg, "default_value", None)
            if default_value:
                if default_value.source == "literal":
                    value_raw = base64.b64decode(default_value.data)
                    value_type = default_value.type or str(arg.type)
                    result.append(get_abi_decoded_value(value_raw, value_type, self._app_spec.structs))
                else:
                    raise ValueError(
                        f"Can't provide default value for {default_value.source} for a contract creation call"
                    )
            else:
                raise ValueError(
                    f"No value provided for required argument "
                    f"{arg.name or f'arg{i+1}'} in call to method {method.name}"
                )

        return result
