from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar

from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.source_map import SourceMap
from typing_extensions import Self

from algokit_utils.models import SendParams

if TYPE_CHECKING:
    from algokit_utils.algorand import AlgorandClient
    from algokit_utils.applications.app_client import (
        AppClientBareCallCreateParams,
        AppClientBareCallParams,
        AppClientCompilationParams,
        BaseAppClientMethodCallParams,
    )
    from algokit_utils.applications.app_deployer import (
        ApplicationLookup,
        OnSchemaBreak,
        OnUpdate,
    )
    from algokit_utils.applications.app_factory import AppFactoryDeployResult

__all__ = [
    "TypedAppClientProtocol",
    "TypedAppFactoryProtocol",
]


class TypedAppClientProtocol(Protocol):
    @classmethod
    def from_creator_and_name(
        cls,
        *,
        creator_address: str,
        app_name: str,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: ApplicationLookup | None = None,
        algorand: AlgorandClient,
    ) -> Self: ...

    @classmethod
    def from_network(
        cls,
        *,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
        algorand: AlgorandClient,
    ) -> Self: ...

    def __init__(
        self,
        *,
        app_id: int,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        algorand: AlgorandClient,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> None: ...


CreateParamsT = TypeVar(  # noqa: PLC0105
    "CreateParamsT",
    bound="BaseAppClientMethodCallParams | AppClientBareCallCreateParams | None",
    contravariant=True,
)
UpdateParamsT = TypeVar(  # noqa: PLC0105
    "UpdateParamsT",
    bound="BaseAppClientMethodCallParams | AppClientBareCallParams | None",
    contravariant=True,
)
DeleteParamsT = TypeVar(  # noqa: PLC0105
    "DeleteParamsT",
    bound="BaseAppClientMethodCallParams | AppClientBareCallParams | None",
    contravariant=True,
)


class TypedAppFactoryProtocol(Protocol, Generic[CreateParamsT, UpdateParamsT, DeleteParamsT]):
    def __init__(
        self,
        algorand: AlgorandClient,
        **kwargs: Any,
    ) -> None: ...

    def deploy(
        self,
        *,
        on_update: OnUpdate | None = None,
        on_schema_break: OnSchemaBreak | None = None,
        create_params: CreateParamsT | None = None,
        update_params: UpdateParamsT | None = None,
        delete_params: DeleteParamsT | None = None,
        existing_deployments: ApplicationLookup | None = None,
        ignore_cache: bool = False,
        app_name: str | None = None,
        send_params: SendParams | None = None,
        compilation_params: AppClientCompilationParams | None = None,
    ) -> tuple[TypedAppClientProtocol, AppFactoryDeployResult]: ...
