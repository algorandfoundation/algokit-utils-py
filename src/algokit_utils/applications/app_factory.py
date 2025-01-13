import base64
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, replace
from typing import Any, Generic, Protocol, TypeVar

from algosdk import transaction
from algosdk.abi import Method
from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.source_map import SourceMap
from algosdk.transaction import OnComplete, Transaction
from typing_extensions import Self

from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.applications.abi import (
    ABIReturn,
    Arc56ReturnValueType,
    get_abi_decoded_value,
    get_abi_tuple_from_abi_struct,
)
from algokit_utils.applications.app_client import (
    AppClient,
    AppClientBareCallParams,
    AppClientCompilationParams,
    AppClientCompilationResult,
    AppClientMethodCallParams,
    AppClientParams,
    TypedAppClientProtocol,
)
from algokit_utils.applications.app_deployer import (
    AppDeployMetaData,
    AppDeployParams,
    AppDeployResponse,
    AppLookup,
    AppMetaData,
    OnSchemaBreak,
    OnUpdate,
    OperationPerformed,
)
from algokit_utils.applications.app_manager import DELETABLE_TEMPLATE_NAME, UPDATABLE_TEMPLATE_NAME
from algokit_utils.applications.app_spec.arc56 import Arc56Contract
from algokit_utils.models.application import (
    AppSourceMaps,
)
from algokit_utils.models.state import TealTemplateParams
from algokit_utils.models.transaction import SendParams
from algokit_utils.protocols.client import AlgorandClientProtocol
from algokit_utils.transactions.transaction_composer import (
    AppCreateMethodCallParams,
    AppCreateParams,
    AppDeleteMethodCallParams,
    AppDeleteParams,
    AppUpdateMethodCallParams,
    AppUpdateParams,
    BuiltTransactions,
)
from algokit_utils.transactions.transaction_sender import (
    SendAppCreateTransactionResult,
    SendAppTransactionResult,
    SendAppUpdateTransactionResult,
    SendSingleTransactionResult,
)

T = TypeVar("T")

__all__ = [
    "AppFactory",
    "AppFactoryCreateMethodCallParams",
    "AppFactoryCreateMethodCallResult",
    "AppFactoryCreateMethodCallWithSendParams",
    "AppFactoryCreateParams",
    "AppFactoryCreateWithSendParams",
    "AppFactoryDeployResponse",
    "AppFactoryParams",
    "SendAppCreateFactoryTransactionResult",
    "SendAppFactoryTransactionResult",
    "SendAppUpdateFactoryTransactionResult",
    "TypedAppFactoryProtocol",
]


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


ABIReturnT = TypeVar(
    "ABIReturnT",
    bound=Arc56ReturnValueType,
)


@dataclass(frozen=True, kw_only=True)
class AppFactoryCreateMethodCallResult(SendSingleTransactionResult, Generic[ABIReturnT]):
    app_id: int
    app_address: str
    compiled_approval: Any | None = None
    compiled_clear: Any | None = None
    abi_return: ABIReturnT | None = None


@dataclass(kw_only=True, frozen=True)
class AppFactoryCreateMethodCallWithSendParams(AppFactoryCreateMethodCallParams, SendParams):
    pass


@dataclass(frozen=True)
class SendAppFactoryTransactionResult(SendAppTransactionResult):
    abi_value: Arc56ReturnValueType | None = None


@dataclass(frozen=True)
class SendAppUpdateFactoryTransactionResult(SendAppUpdateTransactionResult):
    abi_value: Arc56ReturnValueType | None = None


@dataclass(frozen=True, kw_only=True)
class SendAppCreateFactoryTransactionResult(SendAppCreateTransactionResult):
    abi_value: Arc56ReturnValueType | None = None


@dataclass(frozen=True)
class AppFactoryDeployResponse:
    """Result from deploying an application via AppFactory"""

    app: AppMetaData
    operation_performed: OperationPerformed
    create_response: SendAppCreateFactoryTransactionResult | None = None
    update_response: SendAppUpdateFactoryTransactionResult | None = None
    delete_response: SendAppFactoryTransactionResult | None = None

    @classmethod
    def from_deploy_response(
        cls,
        response: AppDeployResponse,
        deploy_params: AppDeployParams,
        app_spec: Arc56Contract,
        app_compilation_data: AppClientCompilationResult | None = None,
    ) -> Self:
        def to_factory_response(
            response_data: SendAppTransactionResult
            | SendAppCreateTransactionResult
            | SendAppUpdateTransactionResult
            | None,
            params: Any,  # noqa: ANN401
        ) -> Any | None:  # noqa: ANN401
            if not response_data:
                return None

            abi_value = None
            abi_return = response_data.abi_return
            if abi_return and abi_return.method:
                abi_value = abi_return.get_arc56_value(params.method, app_spec.structs)

            match response_data:
                case SendAppCreateTransactionResult():
                    return SendAppCreateFactoryTransactionResult(**asdict(response_data), abi_value=abi_value)
                case SendAppUpdateTransactionResult():
                    raw_response = asdict(response_data)
                    raw_response["compiled_approval"] = (
                        app_compilation_data.compiled_approval if app_compilation_data else None
                    )
                    raw_response["compiled_clear"] = (
                        app_compilation_data.compiled_clear if app_compilation_data else None
                    )
                    return SendAppUpdateFactoryTransactionResult(**raw_response, abi_value=abi_value)
                case SendAppTransactionResult():
                    return SendAppFactoryTransactionResult(**asdict(response_data), abi_value=abi_value)

        return cls(
            app=response.app,
            operation_performed=response.operation_performed,
            create_response=to_factory_response(
                response.create_response,
                deploy_params.create_params,
            ),
            update_response=to_factory_response(
                response.update_response,
                deploy_params.update_params,
            ),
            delete_response=to_factory_response(
                response.delete_response,
                deploy_params.delete_params,
            ),
        )


class _AppFactoryBareParamsAccessor:
    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._algorand = factory._algorand

    def create(self, params: AppFactoryCreateParams | None = None) -> AppCreateParams:
        base_params = params or AppFactoryCreateParams()

        compiled = self._factory.compile(base_params)

        return AppCreateParams(
            approval_program=compiled.approval_program,
            clear_state_program=compiled.clear_state_program,
            schema=base_params.schema
            or {
                "global_bytes": self._factory._app_spec.state.schema.global_state.bytes,
                "global_ints": self._factory._app_spec.state.schema.global_state.ints,
                "local_bytes": self._factory._app_spec.state.schema.local_state.bytes,
                "local_ints": self._factory._app_spec.state.schema.local_state.ints,
            },
            sender=self._factory._get_sender(base_params.sender),
            signer=self._factory._get_signer(base_params.sender, base_params.signer),
            on_complete=base_params.on_complete or OnComplete.NoOpOC,
            extra_program_pages=base_params.extra_program_pages,
        )

    def deploy_update(self, params: AppClientBareCallParams | None = None) -> AppUpdateParams:
        return AppUpdateParams(
            app_id=0,
            approval_program="",
            clear_state_program="",
            sender=self._factory._get_sender(params.sender if params else None),
            on_complete=OnComplete.UpdateApplicationOC,
            signer=self._factory._get_signer(params.sender if params else None, params.signer if params else None),
            note=params.note if params else None,
            lease=params.lease if params else None,
            rekey_to=params.rekey_to if params else None,
            account_references=params.account_references if params else None,
            app_references=params.app_references if params else None,
            asset_references=params.asset_references if params else None,
            box_references=params.box_references if params else None,
        )

    def deploy_delete(self, params: AppClientBareCallParams | None = None) -> AppDeleteParams:
        return AppDeleteParams(
            app_id=0,
            sender=self._factory._get_sender(params.sender if params else None),
            signer=self._factory._get_signer(params.sender if params else None, params.signer if params else None),
            on_complete=OnComplete.DeleteApplicationOC,
            note=params.note if params else None,
            lease=params.lease if params else None,
            rekey_to=params.rekey_to if params else None,
            account_references=params.account_references if params else None,
            app_references=params.app_references if params else None,
            asset_references=params.asset_references if params else None,
            box_references=params.box_references if params else None,
        )


class _AppFactoryParamsAccessor:
    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._bare = _AppFactoryBareParamsAccessor(factory)

    @property
    def bare(self) -> _AppFactoryBareParamsAccessor:
        return self._bare

    def create(self, params: AppFactoryCreateMethodCallParams) -> AppCreateMethodCallParams:
        compiled = self._factory.compile(params)

        return AppCreateMethodCallParams(
            app_id=0,
            approval_program=compiled.approval_program,
            clear_state_program=compiled.clear_state_program,
            schema=params.schema
            or {
                "global_bytes": self._factory._app_spec.state.schema.global_state.bytes,
                "global_ints": self._factory._app_spec.state.schema.global_state.ints,
                "local_bytes": self._factory._app_spec.state.schema.local_state.bytes,
                "local_ints": self._factory._app_spec.state.schema.local_state.ints,
            },
            sender=self._factory._get_sender(params.sender),
            signer=self._factory._get_signer(params.sender if params else None, params.signer if params else None),
            method=self._factory._app_spec.get_arc56_method(params.method).to_abi_method(),
            args=self._factory._get_create_abi_args_with_default_values(params.method, params.args),
            on_complete=params.on_complete or OnComplete.NoOpOC,
            note=params.note,
            lease=params.lease,
            rekey_to=params.rekey_to,
        )

    def deploy_update(self, params: AppClientMethodCallParams) -> AppUpdateMethodCallParams:
        return AppUpdateMethodCallParams(
            app_id=0,
            approval_program="",
            clear_state_program="",
            sender=self._factory._get_sender(params.sender),
            signer=self._factory._get_signer(params.sender if params else None, params.signer if params else None),
            method=self._factory._app_spec.get_arc56_method(params.method).to_abi_method(),
            args=self._factory._get_create_abi_args_with_default_values(params.method, params.args),
            on_complete=OnComplete.UpdateApplicationOC,
            note=params.note,
            lease=params.lease,
            rekey_to=params.rekey_to,
        )

    def deploy_delete(self, params: AppClientMethodCallParams) -> AppDeleteMethodCallParams:
        return AppDeleteMethodCallParams(
            app_id=0,
            sender=self._factory._get_sender(params.sender),
            signer=self._factory._get_signer(params.sender if params else None, params.signer if params else None),
            method=self._factory.app_spec.get_arc56_method(params.method).to_abi_method(),
            args=self._factory._get_create_abi_args_with_default_values(params.method, params.args),
            on_complete=OnComplete.DeleteApplicationOC,
            note=params.note,
            lease=params.lease,
            rekey_to=params.rekey_to,
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

    def create(
        self, params: AppFactoryCreateWithSendParams | None = None
    ) -> tuple[AppClient, SendAppCreateTransactionResult]:
        base_params = params or AppFactoryCreateWithSendParams()

        # Use replace() to create new instance with overridden values
        create_params = replace(
            base_params,
            updatable=base_params.updatable if base_params.updatable is not None else self._factory._updatable,
            deletable=base_params.deletable if base_params.deletable is not None else self._factory._deletable,
            deploy_time_params=(
                base_params.deploy_time_params
                if base_params.deploy_time_params is not None
                else self._factory._deploy_time_params
            ),
        )

        compiled = self._factory.compile(
            AppClientCompilationParams(
                deploy_time_params=create_params.deploy_time_params,
                updatable=create_params.updatable,
                deletable=create_params.deletable,
            )
        )

        result = self._factory._handle_call_errors(
            lambda: self._algorand.send.app_create(self._factory.params.bare.create(create_params))
        )

        return (
            self._factory.get_app_client_by_id(
                app_id=result.app_id,
            ),
            SendAppCreateTransactionResult[ABIReturn](
                transaction=result.transaction,
                confirmation=result.confirmation,
                app_id=result.app_id,
                app_address=result.app_address,
                compiled_approval=compiled.compiled_approval if compiled else None,
                compiled_clear=compiled.compiled_clear if compiled else None,
                group_id=result.group_id,
                tx_ids=result.tx_ids,
                transactions=result.transactions,
                confirmations=result.confirmations,
            ),
        )


class _AppFactorySendAccessor:
    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._algorand = factory._algorand
        self._bare = _AppFactoryBareSendAccessor(factory)

    @property
    def bare(self) -> _AppFactoryBareSendAccessor:
        return self._bare

    def create(
        self, params: AppFactoryCreateMethodCallParams
    ) -> tuple[AppClient, AppFactoryCreateMethodCallResult[Arc56ReturnValueType]]:
        create_params = replace(
            params,
            updatable=params.updatable if params.updatable is not None else self._factory._updatable,
            deletable=params.deletable if params.deletable is not None else self._factory._deletable,
            deploy_time_params=(
                params.deploy_time_params
                if params.deploy_time_params is not None
                else self._factory._deploy_time_params
            ),
        )

        compiled = self._factory.compile(
            AppClientCompilationParams(
                deploy_time_params=create_params.deploy_time_params,
                updatable=create_params.updatable,
                deletable=create_params.deletable,
            )
        )

        result = self._factory._handle_call_errors(
            lambda: self._factory._parse_method_call_return(
                lambda: self._algorand.send.app_create_method_call(self._factory.params.create(create_params)),
                self._factory._app_spec.get_arc56_method(params.method).to_abi_method(),
            )
        )

        return (
            self._factory.get_app_client_by_id(
                app_id=result.app_id,
            ),
            AppFactoryCreateMethodCallResult[Arc56ReturnValueType](
                transaction=result.transaction,
                confirmation=result.confirmation,
                tx_id=result.tx_id,
                app_id=result.app_id,
                app_address=result.app_address,
                abi_return=result.abi_return,
                compiled_approval=compiled.compiled_approval if compiled else None,
                compiled_clear=compiled.compiled_clear if compiled else None,
                group_id=result.group_id,
                tx_ids=result.tx_ids,
                transactions=result.transactions,
                confirmations=result.confirmations,
                returns=result.returns,
            ),
        )


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
        existing_deployments: AppLookup | None = None,
        ignore_cache: bool = False,
        updatable: bool | None = None,
        deletable: bool | None = None,
        app_name: str | None = None,
        max_rounds_to_wait: int | None = None,
        suppress_log: bool = False,
        populate_app_call_resources: bool = False,
    ) -> tuple[TypedAppClientProtocol, "AppFactoryDeployResponse"]: ...


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
    ) -> tuple[AppClient, AppFactoryDeployResponse]:
        """Deploy the application with the specified parameters."""

        # Resolve control parameters with factory defaults
        resolved_updatable = (
            updatable if updatable is not None else self._updatable or self._get_deploy_time_control("updatable")
        )
        resolved_deletable = (
            deletable if deletable is not None else self._deletable or self._get_deploy_time_control("deletable")
        )
        resolved_deploy_time_params = deploy_time_params or self._deploy_time_params

        def prepare_create_args() -> AppCreateMethodCallParams | AppCreateParams:
            """Prepare create arguments based on parameter type."""
            if create_params and isinstance(create_params, AppClientMethodCallParams):
                return self.params.create(
                    AppFactoryCreateMethodCallParams(
                        **asdict(create_params),
                        updatable=resolved_updatable,
                        deletable=resolved_deletable,
                        deploy_time_params=resolved_deploy_time_params,
                    )
                )

            base_params = create_params or AppClientBareCallParams()
            return self.params.bare.create(
                AppFactoryCreateParams(
                    **asdict(base_params) if base_params else {},
                    updatable=resolved_updatable,
                    deletable=resolved_deletable,
                    deploy_time_params=resolved_deploy_time_params,
                )
            )

        def prepare_update_args() -> AppUpdateMethodCallParams | AppUpdateParams:
            """Prepare update arguments based on parameter type."""
            return (
                self.params.deploy_update(update_params)
                if isinstance(update_params, AppClientMethodCallParams)
                else self.params.bare.deploy_update(update_params)
            )

        def prepare_delete_args() -> AppDeleteMethodCallParams | AppDeleteParams:
            """Prepare delete arguments based on parameter type."""
            return (
                self.params.deploy_delete(delete_params)
                if isinstance(delete_params, AppClientMethodCallParams)
                else self.params.bare.deploy_delete(delete_params)
            )

        # Execute deployment
        deploy_params = AppDeployParams(
            deploy_time_params=resolved_deploy_time_params,
            on_schema_break=on_schema_break,
            on_update=on_update,
            existing_deployments=existing_deployments,
            ignore_cache=ignore_cache,
            create_params=prepare_create_args(),
            update_params=prepare_update_args(),
            delete_params=prepare_delete_args(),
            metadata=AppDeployMetaData(
                name=app_name or self._app_name,
                version=self._version,
                updatable=resolved_updatable,
                deletable=resolved_deletable,
            ),
            suppress_log=suppress_log,
            max_rounds_to_wait=max_rounds_to_wait,
            populate_app_call_resources=populate_app_call_resources,
        )
        deploy_response = self._algorand.app_deployer.deploy(deploy_params)

        # Prepare app client and factory deploy response
        app_client = self.get_app_client_by_id(
            app_id=deploy_response.app.app_id,
            app_name=app_name,
            default_sender=self._default_sender,
            default_signer=self._default_signer,
        )
        factory_deploy_response = AppFactoryDeployResponse.from_deploy_response(
            response=deploy_response,
            deploy_params=deploy_params,
            app_spec=app_client.app_spec,
            app_compilation_data=self.compile(
                AppClientCompilationParams(
                    deploy_time_params=resolved_deploy_time_params,
                    updatable=resolved_updatable,
                    deletable=resolved_deletable,
                )
            ),
        )

        return app_client, factory_deploy_response

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

    def get_app_client_by_creator_and_name(
        self,
        creator_address: str,
        app_name: str,
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: AppLookup | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
        return AppClient.from_creator_and_name(
            creator_address=creator_address,
            app_name=app_name or self._app_name,
            default_sender=default_sender or self._default_sender,
            default_signer=default_signer or self._default_signer,
            approval_source_map=approval_source_map or self._approval_source_map,
            clear_source_map=clear_source_map or self._clear_source_map,
            ignore_cache=ignore_cache,
            app_lookup_cache=app_lookup_cache,
            app_spec=self._app_spec,
            algorand=self._algorand,
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
            app_spec=self._app_spec,
            app_manager=self._algorand.app,
            deploy_time_params=compilation.deploy_time_params if compilation else None,
            updatable=compilation.updatable if compilation else None,
            deletable=compilation.deletable if compilation else None,
        )

        if result.compiled_approval:
            self._approval_source_map = result.compiled_approval.source_map
        if result.compiled_clear:
            self._clear_source_map = result.compiled_clear.source_map

        return result

    def _expose_logic_error(self, e: Exception, is_clear_state_program: bool = False) -> Exception:  # noqa: FBT002 FBT001
        return AppClient._expose_logic_error_static(
            e=e,
            app_spec=self._app_spec,
            is_clear_state_program=is_clear_state_program,
            approval_source_map=self._approval_source_map,
            clear_source_map=self._clear_source_map,
            program=None,
            approval_source_info=(self._app_spec.source_info.approval if self._app_spec.source_info else None),
            clear_source_info=(self._app_spec.source_info.clear if self._app_spec.source_info else None),
        )

    def _get_deploy_time_control(self, control: str) -> bool | None:
        approval = self._app_spec.source.get_decoded_approval() if self._app_spec.source else None

        template_name = UPDATABLE_TEMPLATE_NAME if control == "updatable" else DELETABLE_TEMPLATE_NAME
        if not approval or template_name not in approval:
            return None

        on_complete = "UpdateApplication" if control == "updatable" else "DeleteApplication"
        return on_complete in self._app_spec.bare_actions.call or any(
            on_complete in m.actions.call for m in self._app_spec.methods if m.actions and m.actions.call
        )

    def _get_sender(self, sender: str | bytes | None) -> str:
        if not sender and not self._default_sender:
            raise Exception(
                f"No sender provided and no default sender present in app client for call to app {self._app_name}"
            )
        return str(sender or self._default_sender)

    def _get_signer(self, sender: str | None, signer: TransactionSigner | None) -> TransactionSigner | None:
        return signer or (self._default_signer if not sender or sender == self._default_sender else None)

    def _handle_call_errors(self, call: Callable[[], T]) -> T:
        try:
            return call()
        except Exception as e:
            raise self._expose_logic_error(e) from None

    def _parse_method_call_return(
        self,
        result: Callable[
            [], SendAppTransactionResult | SendAppCreateTransactionResult | SendAppUpdateTransactionResult
        ],
        method: Method,
    ) -> AppFactoryCreateMethodCallResult[Arc56ReturnValueType]:
        result_value = result()
        return AppFactoryCreateMethodCallResult[Arc56ReturnValueType](
            **{
                **result_value.__dict__,
                "abi_return": result_value.abi_return.get_arc56_value(method, self._app_spec.structs)
                if isinstance(result_value.abi_return, ABIReturn)
                else None,
            }
        )

    def _get_create_abi_args_with_default_values(
        self,
        method_name_or_signature: str,
        user_args: Sequence[Any] | None,
    ) -> list[Any]:
        """
        Builds a list of ABI argument values for creation calls, applying default
        argument values when not provided.
        """
        method = self._app_spec.get_arc56_method(method_name_or_signature)

        results: list[Any] = []

        for i, param in enumerate(method.args):
            if user_args and i < len(user_args):
                arg_value = user_args[i]
                if param.struct and isinstance(arg_value, dict):
                    arg_value = get_abi_tuple_from_abi_struct(
                        arg_value,
                        self._app_spec.structs[param.struct],
                        self._app_spec.structs,
                    )
                results.append(arg_value)
                continue

            default_value = getattr(param, "default_value", None)
            if default_value:
                if default_value.source == "literal":
                    raw_value = base64.b64decode(default_value.data)
                    value_type = default_value.type or str(param.type)
                    decoded_value = get_abi_decoded_value(raw_value, value_type, self._app_spec.structs)
                    results.append(decoded_value)
                else:
                    raise ValueError(
                        f"Cannot provide default value from source={default_value.source} "
                        "for a contract creation call."
                    )
            else:
                param_name = param.name or f"arg{i + 1}"
                raise ValueError(
                    f"No value provided for required argument {param_name} " f"in call to method {method.name}"
                )

        return results
