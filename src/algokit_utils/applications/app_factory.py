import base64
import dataclasses
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Generic, TypeVar

from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.source_map import SourceMap
from algosdk.transaction import OnComplete, Transaction
from typing_extensions import Self

from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.algorand import AlgorandClient
from algokit_utils.applications.abi import (
    ABIReturn,
    Arc56ReturnValueType,
    get_abi_decoded_value,
    get_abi_tuple_from_abi_struct,
)
from algokit_utils.applications.app_client import (
    AppClient,
    AppClientBareCallCreateParams,
    AppClientBareCallParams,
    AppClientCompilationParams,
    AppClientCompilationResult,
    AppClientMethodCallCreateParams,
    AppClientMethodCallParams,
    AppClientParams,
    CreateOnComplete,
)
from algokit_utils.applications.app_deployer import (
    AppDeploymentMetaData,
    AppDeployParams,
    AppDeployResult,
    ApplicationLookup,
    ApplicationMetaData,
    OnSchemaBreak,
    OnUpdate,
    OperationPerformed,
)
from algokit_utils.applications.app_manager import DELETABLE_TEMPLATE_NAME, UPDATABLE_TEMPLATE_NAME
from algokit_utils.applications.app_spec.arc56 import Arc56Contract, Method
from algokit_utils.models.application import (
    AppSourceMaps,
)
from algokit_utils.models.transaction import SendParams
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
    "AppFactoryCreateParams",
    "AppFactoryDeployResult",
    "AppFactoryParams",
    "SendAppCreateFactoryTransactionResult",
    "SendAppFactoryTransactionResult",
    "SendAppUpdateFactoryTransactionResult",
]


@dataclass(kw_only=True, frozen=True)
class AppFactoryParams:
    algorand: AlgorandClient
    app_spec: Arc56Contract | ApplicationSpecification | str
    app_name: str | None = None
    default_sender: str | None = None
    default_signer: TransactionSigner | None = None
    version: str | None = None
    compilation_params: AppClientCompilationParams | None = None


@dataclass(kw_only=True, frozen=True)
class AppFactoryCreateParams(AppClientBareCallCreateParams):
    on_complete: CreateOnComplete | None = None


@dataclass(kw_only=True, frozen=True)
class AppFactoryCreateMethodCallParams(AppClientMethodCallCreateParams):
    pass


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


@dataclass(frozen=True)
class SendAppFactoryTransactionResult(SendAppTransactionResult[Arc56ReturnValueType]):
    pass


@dataclass(frozen=True)
class SendAppUpdateFactoryTransactionResult(SendAppUpdateTransactionResult[Arc56ReturnValueType]):
    pass


@dataclass(frozen=True, kw_only=True)
class SendAppCreateFactoryTransactionResult(SendAppCreateTransactionResult[Arc56ReturnValueType]):
    pass


@dataclass(frozen=True)
class AppFactoryDeployResult:
    """Result from deploying an application via AppFactory"""

    app: ApplicationMetaData
    """The application metadata"""
    operation_performed: OperationPerformed
    """The operation performed"""
    create_result: SendAppCreateFactoryTransactionResult | None = None
    """The create result"""
    update_result: SendAppUpdateFactoryTransactionResult | None = None
    """The update result"""
    delete_result: SendAppFactoryTransactionResult | None = None
    """The delete result"""

    @classmethod
    def from_deploy_result(
        cls,
        response: AppDeployResult,
        deploy_params: AppDeployParams,
        app_spec: Arc56Contract,
        app_compilation_data: AppClientCompilationResult | None = None,
    ) -> Self:
        """
        Construct an AppFactoryDeployResult from a deployment result.

        :param response: The deployment response.
        :param deploy_params: The deployment parameters.
        :param app_spec: The application specification.
        :param app_compilation_data: Optional app compilation data.
        :return: An instance of AppFactoryDeployResult.
        """

        def to_factory_result(
            response_data: SendAppTransactionResult[ABIReturn]
            | SendAppCreateTransactionResult
            | SendAppUpdateTransactionResult
            | None,
            params: Any,  # noqa: ANN401
        ) -> Any | None:  # noqa: ANN401
            if not response_data:
                return None

            response_data_dict = asdict(response_data)
            abi_return = response_data.abi_return
            if abi_return and abi_return.method:
                response_data_dict["abi_return"] = abi_return.get_arc56_value(params.method, app_spec.structs)

            match response_data:
                case SendAppCreateTransactionResult():
                    return SendAppCreateFactoryTransactionResult(**response_data_dict)
                case SendAppUpdateTransactionResult():
                    response_data_dict["compiled_approval"] = (
                        app_compilation_data.compiled_approval if app_compilation_data else None
                    )
                    response_data_dict["compiled_clear"] = (
                        app_compilation_data.compiled_clear if app_compilation_data else None
                    )
                    return SendAppUpdateFactoryTransactionResult(**response_data_dict)
                case SendAppTransactionResult():
                    return SendAppFactoryTransactionResult(**response_data_dict)

        return cls(
            app=response.app,
            operation_performed=response.operation_performed,
            create_result=to_factory_result(
                response.create_result,
                deploy_params.create_params,
            ),
            update_result=to_factory_result(
                response.update_result,
                deploy_params.update_params,
            ),
            delete_result=to_factory_result(
                response.delete_result,
                deploy_params.delete_params,
            ),
        )


class _BareParamsBuilder:
    """The bare params builder.

    :param factory: The AppFactory instance.
    """

    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._algorand = factory._algorand

    def create(
        self, params: AppFactoryCreateParams | None = None, compilation_params: AppClientCompilationParams | None = None
    ) -> AppCreateParams:
        """
        Create AppCreateParams using the provided parameters and compilation settings.

        :param params: Optional AppFactoryCreateParams instance.
        :param compilation_params: Optional AppClientCompilationParams instance.
        :return: An instance of AppCreateParams.
        """
        base_params = params or AppFactoryCreateParams()
        compiled = self._factory.compile(compilation_params)

        return AppCreateParams(
            **{
                **{
                    param: value
                    for param, value in asdict(base_params).items()
                    if param in {f.name for f in dataclasses.fields(AppCreateParams)}
                },
                "approval_program": compiled.approval_program,
                "clear_state_program": compiled.clear_state_program,
                "schema": base_params.schema
                or {
                    "global_byte_slices": self._factory._app_spec.state.schema.global_state.bytes,
                    "global_ints": self._factory._app_spec.state.schema.global_state.ints,
                    "local_byte_slices": self._factory._app_spec.state.schema.local_state.bytes,
                    "local_ints": self._factory._app_spec.state.schema.local_state.ints,
                },
                "sender": self._factory._get_sender(base_params.sender),
                "signer": self._factory._get_signer(base_params.sender, base_params.signer),
                "on_complete": base_params.on_complete or OnComplete.NoOpOC,
            }
        )

    def deploy_update(self, params: AppClientBareCallParams | None = None) -> AppUpdateParams:
        """
        Create AppUpdateParams for an update operation.

        :param params: Optional AppClientBareCallParams instance.
        :return: An instance of AppUpdateParams.
        """
        return AppUpdateParams(
            **{
                **{
                    param: value
                    for param, value in asdict(params or AppClientBareCallParams()).items()
                    if param in {f.name for f in dataclasses.fields(AppUpdateParams)}
                },
                "app_id": 0,
                "approval_program": "",
                "clear_state_program": "",
                "sender": self._factory._get_sender(params.sender if params else None),
                "on_complete": OnComplete.UpdateApplicationOC,
                "signer": self._factory._get_signer(
                    params.sender if params else None, params.signer if params else None
                ),
            }
        )

    def deploy_delete(self, params: AppClientBareCallParams | None = None) -> AppDeleteParams:
        """
        Create AppDeleteParams for a delete operation.

        :param params: Optional AppClientBareCallParams instance.
        :return: An instance of AppDeleteParams.
        """
        return AppDeleteParams(
            **{
                **{
                    param: value
                    for param, value in asdict(params or AppClientBareCallParams()).items()
                    if param in {f.name for f in dataclasses.fields(AppDeleteParams)}
                },
                "app_id": 0,
                "sender": self._factory._get_sender(params.sender if params else None),
                "signer": self._factory._get_signer(
                    params.sender if params else None, params.signer if params else None
                ),
                "on_complete": OnComplete.DeleteApplicationOC,
            }
        )


class _MethodParamsBuilder:
    """The method params builder.

    :param factory: The AppFactory instance.
    """

    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._bare = _BareParamsBuilder(factory)

    @property
    def bare(self) -> _BareParamsBuilder:
        """
        Get the bare parameters builder.

        :return: The _BareParamsBuilder instance.
        """
        return self._bare

    def create(
        self, params: AppFactoryCreateMethodCallParams, compilation_params: AppClientCompilationParams | None = None
    ) -> AppCreateMethodCallParams:
        """
        Create AppCreateMethodCallParams using the provided parameters and compilation settings.

        :param params: AppFactoryCreateMethodCallParams instance.
        :param compilation_params: Optional AppClientCompilationParams instance.
        :return: An instance of AppCreateMethodCallParams.
        """
        compiled = self._factory.compile(compilation_params)

        return AppCreateMethodCallParams(
            **{
                **{
                    param: value
                    for param, value in asdict(params).items()
                    if param in {f.name for f in dataclasses.fields(AppCreateMethodCallParams)}
                },
                "app_id": 0,
                "approval_program": compiled.approval_program,
                "clear_state_program": compiled.clear_state_program,
                "schema": params.schema
                or {
                    "global_byte_slices": self._factory._app_spec.state.schema.global_state.bytes,
                    "global_ints": self._factory._app_spec.state.schema.global_state.ints,
                    "local_byte_slices": self._factory._app_spec.state.schema.local_state.bytes,
                    "local_ints": self._factory._app_spec.state.schema.local_state.ints,
                },
                "sender": self._factory._get_sender(params.sender),
                "signer": self._factory._get_signer(
                    params.sender if params else None, params.signer if params else None
                ),
                "method": self._factory._app_spec.get_arc56_method(params.method).to_abi_method(),
                "args": self._factory._get_create_abi_args_with_default_values(params.method, params.args),
                "on_complete": params.on_complete or OnComplete.NoOpOC,
            }
        )

    def deploy_update(self, params: AppClientMethodCallParams) -> AppUpdateMethodCallParams:
        """
        Create AppUpdateMethodCallParams for an update operation.

        :param params: AppClientMethodCallParams instance.
        :return: An instance of AppUpdateMethodCallParams.
        """
        return AppUpdateMethodCallParams(
            **{
                **{
                    param: value
                    for param, value in asdict(params).items()
                    if param in {f.name for f in dataclasses.fields(AppUpdateMethodCallParams)}
                },
                "app_id": 0,
                "approval_program": "",
                "clear_state_program": "",
                "sender": self._factory._get_sender(params.sender),
                "signer": self._factory._get_signer(
                    params.sender if params else None, params.signer if params else None
                ),
                "method": self._factory._app_spec.get_arc56_method(params.method).to_abi_method(),
                "args": self._factory._get_create_abi_args_with_default_values(params.method, params.args),
                "on_complete": OnComplete.UpdateApplicationOC,
            }
        )

    def deploy_delete(self, params: AppClientMethodCallParams) -> AppDeleteMethodCallParams:
        """
        Create AppDeleteMethodCallParams for a delete operation.

        :param params: AppClientMethodCallParams instance.
        :return: An instance of AppDeleteMethodCallParams.
        """
        return AppDeleteMethodCallParams(
            **{
                **{
                    param: value
                    for param, value in asdict(params).items()
                    if param in {f.name for f in dataclasses.fields(AppDeleteMethodCallParams)}
                },
                "app_id": 0,
                "sender": self._factory._get_sender(params.sender),
                "signer": self._factory._get_signer(
                    params.sender if params else None, params.signer if params else None
                ),
                "method": self._factory.app_spec.get_arc56_method(params.method).to_abi_method(),
                "args": self._factory._get_create_abi_args_with_default_values(params.method, params.args),
                "on_complete": OnComplete.DeleteApplicationOC,
            }
        )


class _AppFactoryBareCreateTransactionAccessor:
    """Initialize the bare create transaction accessor.

    :param factory: The AppFactory instance.
    """

    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory

    def create(self, params: AppFactoryCreateParams | None = None) -> Transaction:
        """
        Create a transaction for app creation.

        :param params: Optional AppFactoryCreateParams instance.
        :return: A Transaction instance.
        """
        return self._factory._algorand.create_transaction.app_create(self._factory.params.bare.create(params))


class _TransactionCreator:
    """
    The transaction creator.

    :param factory: The AppFactory instance.
    """

    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._bare = _AppFactoryBareCreateTransactionAccessor(factory)

    @property
    def bare(self) -> _AppFactoryBareCreateTransactionAccessor:
        """
        Get the bare create transaction accessor.

        :return: The _AppFactoryBareCreateTransactionAccessor instance.
        """
        return self._bare

    def create(self, params: AppFactoryCreateMethodCallParams) -> BuiltTransactions:
        """
        Create built transactions for an app method call.

        :param params: AppFactoryCreateMethodCallParams instance.
        :return: A BuiltTransactions instance.
        """
        return self._factory._algorand.create_transaction.app_create_method_call(self._factory.params.create(params))


class _AppFactoryBareSendAccessor:
    """
    The bare send accessor.

    :param factory: The AppFactory instance.
    """

    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._algorand = factory._algorand

    def create(
        self,
        params: AppFactoryCreateParams | None = None,
        send_params: SendParams | None = None,
        compilation_params: AppClientCompilationParams | None = None,
    ) -> tuple[AppClient, SendAppCreateTransactionResult]:
        """
        Send an app creation transaction and return the app client along with the transaction result.

        :param params: Optional AppFactoryCreateParams instance.
        :param send_params: Optional SendParams instance.
        :param compilation_params: Optional AppClientCompilationParams instance.
        :return: A tuple containing the AppClient and SendAppCreateTransactionResult.
        """
        compilation_params = compilation_params or AppClientCompilationParams()
        compilation_params["updatable"] = (
            compilation_params.get("updatable")
            if compilation_params.get("updatable") is not None
            else self._factory._updatable
        )
        compilation_params["deletable"] = (
            compilation_params.get("deletable")
            if compilation_params.get("deletable") is not None
            else self._factory._deletable
        )
        compilation_params["deploy_time_params"] = (
            compilation_params.get("deploy_time_params")
            if compilation_params.get("deploy_time_params") is not None
            else self._factory._deploy_time_params
        )

        compiled = self._factory.compile(compilation_params)

        result = self._factory._handle_call_errors(
            lambda: self._algorand.send.app_create(
                self._factory.params.bare.create(params, compilation_params), send_params
            )
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


class _TransactionSender:
    """
    The transaction sender.

    :param factory: The AppFactory instance.
    """

    def __init__(self, factory: "AppFactory") -> None:
        self._factory = factory
        self._algorand = factory._algorand
        self._bare = _AppFactoryBareSendAccessor(factory)

    @property
    def bare(self) -> _AppFactoryBareSendAccessor:
        """
        Get the bare send accessor.

        :return: The _AppFactoryBareSendAccessor instance.
        """
        return self._bare

    def create(
        self,
        params: AppFactoryCreateMethodCallParams,
        send_params: SendParams | None = None,
        compilation_params: AppClientCompilationParams | None = None,
    ) -> tuple[AppClient, AppFactoryCreateMethodCallResult[Arc56ReturnValueType]]:
        """
        Send an app creation method call and return the app client along with the method call result.

        :param params: AppFactoryCreateMethodCallParams instance.
        :param send_params: Optional SendParams instance.
        :param compilation_params: Optional AppClientCompilationParams instance.
        :return: A tuple containing the AppClient and AppFactoryCreateMethodCallResult.
        """
        compilation_params = compilation_params or AppClientCompilationParams()
        compilation_params["updatable"] = (
            compilation_params.get("updatable")
            if compilation_params.get("updatable") is not None
            else self._factory._updatable
        )
        compilation_params["deletable"] = (
            compilation_params.get("deletable")
            if compilation_params.get("deletable") is not None
            else self._factory._deletable
        )
        compilation_params["deploy_time_params"] = (
            compilation_params.get("deploy_time_params")
            if compilation_params.get("deploy_time_params") is not None
            else self._factory._deploy_time_params
        )

        compiled = self._factory.compile(compilation_params)
        result = self._factory._handle_call_errors(
            lambda: self._factory._parse_method_call_return(
                lambda: self._algorand.send.app_create_method_call(
                    self._factory.params.create(params, compilation_params), send_params
                ),
                self._factory._app_spec.get_arc56_method(params.method),
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


class AppFactory:
    """ARC-56/ARC-32 app factory that, for a given app spec, allows you to create
    and deploy one or more app instances and to create one or more app clients
    to interact with those (or other) app instances.

    :param params: The parameters for the factory

    :example:
        >>> factory = AppFactory(AppFactoryParams(
        >>>        algorand=AlgorandClient.mainnet(),
        >>>        app_spec=app_spec,
        >>>    )
        >>> )
    """

    def __init__(self, params: AppFactoryParams) -> None:
        self._app_spec = AppClient.normalise_app_spec(params.app_spec)
        self._app_name = params.app_name or self._app_spec.name
        self._algorand = params.algorand
        self._version = params.version or "1.0"
        self._default_sender = params.default_sender
        self._default_signer = params.default_signer
        self._approval_source_map: SourceMap | None = None
        self._clear_source_map: SourceMap | None = None
        self._params_accessor = _MethodParamsBuilder(self)
        self._send_accessor = _TransactionSender(self)
        self._create_transaction_accessor = _TransactionCreator(self)

        compilation_params = params.compilation_params or AppClientCompilationParams()
        self._deploy_time_params = compilation_params.get("deploy_time_params")
        self._updatable = compilation_params.get("updatable")
        self._deletable = compilation_params.get("deletable")

    @property
    def app_name(self) -> str:
        """The name of the app"""
        return self._app_name

    @property
    def app_spec(self) -> Arc56Contract:
        """The app spec"""
        return self._app_spec

    @property
    def algorand(self) -> AlgorandClient:
        """The algorand client"""
        return self._algorand

    @property
    def params(self) -> _MethodParamsBuilder:
        """Get parameters to create transactions (create and deploy related calls) for the current app.

        A good mental model for this is that these parameters represent a deferred transaction creation.

        :example: Create a transaction in the future using Algorand Client
            >>> create_app_params = app_factory.params.create(
            ...     AppFactoryCreateMethodCallParams(
            ...         method='create_method',
            ...         args=[123, 'hello']
            ...     )
            ... )
            >>> # ...
            >>> algorand.send.app_create_method_call(create_app_params)

        :example: Define a nested transaction as an ABI argument
            >>> create_app_params = appFactory.params.create(
            ...     AppFactoryCreateMethodCallParams(
            ...         method='create_method',
            ...         args=[123, 'hello']
            ...     )
            ... )
            >>> app_client.send.call(
            ...     AppClientMethodCallParams(
            ...         method='my_method',
            ...         args=[create_app_params]
            ...     )
            ... )
        """
        return self._params_accessor

    @property
    def send(self) -> _TransactionSender:
        """
        Get the transaction sender.

        :return: The _TransactionSender instance.
        """
        return self._send_accessor

    @property
    def create_transaction(self) -> _TransactionCreator:
        """
        Get the transaction creator.

        :return: The _TransactionCreator instance.
        """
        return self._create_transaction_accessor

    def deploy(
        self,
        *,
        on_update: OnUpdate | None = None,
        on_schema_break: OnSchemaBreak | None = None,
        create_params: AppClientMethodCallCreateParams | AppClientBareCallCreateParams | None = None,
        update_params: AppClientMethodCallParams | AppClientBareCallParams | None = None,
        delete_params: AppClientMethodCallParams | AppClientBareCallParams | None = None,
        existing_deployments: ApplicationLookup | None = None,
        ignore_cache: bool = False,
        app_name: str | None = None,
        send_params: SendParams | None = None,
        compilation_params: AppClientCompilationParams | None = None,
    ) -> tuple[AppClient, AppFactoryDeployResult]:
        """Idempotently deploy (create if not exists, update if changed) an app against the given name for the given
        creator account, including deploy-time TEAL template placeholder substitutions (if specified).

        **Note:** When using the return from this function be sure to check `operationPerformed` to get access to
        various return properties like `transaction`, `confirmation` and `deleteResult`.

        **Note:** if there is a breaking state schema change to an existing app (and `onSchemaBreak` is set to
        `'replace'`) the existing app will be deleted and re-created.

        **Note:** if there is an update (different TEAL code) to an existing app (and `onUpdate` is set to
        `'replace'`) the existing app will be deleted and re-created.

        :param on_update: The action to take if there is an update to the app
        :param on_schema_break: The action to take if there is a breaking state schema change to the app
        :param create_params: The arguments to create the app
        :param update_params: The arguments to update the app
        :param delete_params: The arguments to delete the app
        :param existing_deployments: The existing deployments to use
        :param ignore_cache: Whether to ignore the cache
        :param app_name: The name of the app
        :param send_params: The parameters for the send call
        :param compilation_params: The parameters for the compilation
        :returns: The app client and the result of the deployment

        :example:
            >>> app_client, result = factory.deploy({
            >>>   create_params=AppClientMethodCallCreateParams(
            >>>     sender='SENDER_ADDRESS',
            >>>     approval_program='APPROVAL PROGRAM',
            >>>     clear_state_program='CLEAR PROGRAM',
            >>>     schema={
            >>>       "global_byte_slices": 0,
            >>>       "global_ints": 0,
            >>>       "local_byte_slices": 0,
            >>>       "local_ints": 0
            >>>     }
            >>>   ),
            >>>   update_params=AppClientMethodCallParams(
            >>>     sender='SENDER_ADDRESS'
            >>>   ),
            >>>   delete_params=AppClientMethodCallParams(
            >>>     sender='SENDER_ADDRESS'
            >>>   ),
            >>>   compilation_params=AppClientCompilationParams(
            >>>     updatable=False,
            >>>     deletable=False
            >>>   ),
            >>>   app_name='my_app',
            >>>   on_schema_break=OnSchemaBreak.AppendApp,
            >>>   on_update=OnUpdate.AppendApp
            >>> })
        """
        # Resolve control parameters with factory defaults
        send_params = send_params or SendParams()
        compilation_params = compilation_params or AppClientCompilationParams()
        resolved_updatable = (
            upd
            if (upd := compilation_params.get("updatable")) is not None
            else self._updatable or self._get_deploy_time_control("updatable")
        )
        resolved_deletable = (
            dlb
            if (dlb := compilation_params.get("deletable")) is not None
            else self._deletable or self._get_deploy_time_control("deletable")
        )
        resolved_deploy_time_params = compilation_params.get("deploy_time_params") or self._deploy_time_params

        def prepare_create_args() -> AppCreateMethodCallParams | AppCreateParams:
            """Prepare create arguments based on parameter type."""
            if create_params and isinstance(create_params, AppClientMethodCallCreateParams):
                return self.params.create(
                    AppFactoryCreateMethodCallParams(
                        **asdict(create_params),
                    ),
                    compilation_params={
                        "updatable": resolved_updatable,
                        "deletable": resolved_deletable,
                        "deploy_time_params": resolved_deploy_time_params,
                    },
                )

            base_params = create_params or AppClientBareCallCreateParams()
            return self.params.bare.create(
                AppFactoryCreateParams(
                    **asdict(base_params) if base_params else {},
                ),
                compilation_params={
                    "updatable": resolved_updatable,
                    "deletable": resolved_deletable,
                    "deploy_time_params": resolved_deploy_time_params,
                },
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
            metadata=AppDeploymentMetaData(
                name=app_name or self._app_name,
                version=self._version,
                updatable=resolved_updatable,
                deletable=resolved_deletable,
            ),
            send_params=send_params,
        )
        deploy_result = self._algorand.app_deployer.deploy(deploy_params)

        # Prepare app client and factory deploy response
        app_client = self.get_app_client_by_id(
            app_id=deploy_result.app.app_id,
            app_name=app_name,
            default_sender=self._default_sender,
            default_signer=self._default_signer,
        )
        factory_deploy_result = AppFactoryDeployResult.from_deploy_result(
            response=deploy_result,
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

        return app_client, factory_deploy_result

    def get_app_client_by_id(
        self,
        app_id: int,
        app_name: str | None = None,
        default_sender: str | None = None,  # Address can be string or bytes
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
        """Returns a new `AppClient` client for an app instance of the given ID.

        :param app_id: The id of the app
        :param app_name: The name of the app
        :param default_sender: The default sender address
        :param default_signer: The default signer
        :param approval_source_map: The approval source map
        :param clear_source_map: The clear source map
        :return AppClient: The app client

        :example:
            >>> app_client = factory.get_app_client_by_id(app_id=123)
        """
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
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: ApplicationLookup | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> AppClient:
        """Returns a new `AppClient` client, resolving the app by creator address and name
        using AlgoKit app deployment semantics (i.e. looking for the app creation transaction note).

        :param creator_address: The creator address
        :param app_name: The name of the app
        :param default_sender: The default sender address
        :param default_signer: The default signer
        :param ignore_cache: Whether to ignore the cache and force a lookup
        :param app_lookup_cache: Optional cache of existing app deployments to use instead of querying the indexer
        :param approval_source_map: Optional source map for the approval program
        :param clear_source_map: Optional source map for the clear state program
        :return: An AppClient instance configured for the resolved application

        :example:
            >>> app_client = factory.get_app_client_by_creator_and_name(
            ...     creator_address='SENDER_ADDRESS',
            ...     app_name='my_app'
            ... )
        """
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
        """
        Import the provided source maps into the factory.

        :param source_maps: An AppSourceMaps instance containing the approval and clear source maps.
        """
        self._approval_source_map = source_maps.approval_source_map
        self._clear_source_map = source_maps.clear_source_map

    def compile(self, compilation_params: AppClientCompilationParams | None = None) -> AppClientCompilationResult:
        """Compile the app's TEAL code.

        :param compilation_params: The compilation parameters
        :return AppClientCompilationResult: The compilation result

        :example:
            >>> compilation_result = factory.compile()
        """
        compilation = compilation_params or AppClientCompilationParams()
        result = AppClient.compile(
            app_spec=self._app_spec,
            app_manager=self._algorand.app,
            compilation_params=compilation,
        )

        if result.compiled_approval:
            self._approval_source_map = result.compiled_approval.source_map
        if result.compiled_clear:
            self._clear_source_map = result.compiled_clear.source_map

        return result

    def _expose_logic_error(self, e: Exception, is_clear_state_program: bool = False) -> Exception:  # noqa: FBT002 FBT001
        """
        Convert a low-level exception into a descriptive logic error.

        :param e: The original exception.
        :param is_clear_state_program: Flag indicating if the error is related to the clear state program.
        :return: The transformed exception.
        """
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
        """
        Determine the deploy time control flag for the specified control type.

        :param control: The control type ('updatable' or 'deletable').
        :return: A boolean flag or None if not determinable.
        """
        approval = self._app_spec.source.get_decoded_approval() if self._app_spec.source else None

        template_name = UPDATABLE_TEMPLATE_NAME if control == "updatable" else DELETABLE_TEMPLATE_NAME
        if not approval or template_name not in approval:
            return None

        on_complete = "UpdateApplication" if control == "updatable" else "DeleteApplication"
        return on_complete in self._app_spec.bare_actions.call or any(
            on_complete in m.actions.call for m in self._app_spec.methods if m.actions and m.actions.call
        )

    def _get_sender(self, sender: str | None) -> str:
        """
        Retrieve the sender address.

        :param sender: The specified sender address.
        :return: The sender address.
        :raises Exception: If no sender is provided and no default sender is set.
        """
        if not sender and not self._default_sender:
            raise Exception(
                f"No sender provided and no default sender present in app client for call to app {self._app_name}"
            )
        return str(sender or self._default_sender)

    def _get_signer(self, sender: str | None, signer: TransactionSigner | None) -> TransactionSigner | None:
        """
        Retrieve the transaction signer.

        :param sender: The sender address.
        :param signer: The provided signer.
        :return: The transaction signer if available.
        """
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
        """
        Parse the method call return value and convert the ABI return.

        :param result: A callable that returns the transaction result.
        :param method: The ABI method associated with the call.
        :return: An AppFactoryCreateMethodCallResult with the parsed ABI return.
        """
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
                        f"Cannot provide default value from source={default_value.source} for a contract creation call."
                    )
            else:
                param_name = param.name or f"arg{i + 1}"
                raise ValueError(
                    f"No value provided for required argument {param_name} in call to method {method.name}"
                )

        return results
