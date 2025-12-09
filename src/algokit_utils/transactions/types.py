from dataclasses import dataclass
from typing import TypedDict, Union

from algokit_abi import arc56
from algokit_transact import OnApplicationComplete
from algokit_transact.signer import AddressWithTransactionSigner, TransactionSigner
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.models.state import BoxIdentifier, BoxReference

__all__ = [
    "AppCallMethodCallParams",
    "AppCallParams",
    "AppCreateMethodCallParams",
    "AppCreateParams",
    "AppCreateSchema",
    "AppDeleteMethodCallParams",
    "AppDeleteParams",
    "AppMethodCallParams",
    "AppUpdateMethodCallParams",
    "AppUpdateParams",
    "AssetConfigParams",
    "AssetCreateParams",
    "AssetDestroyParams",
    "AssetFreezeParams",
    "AssetOptInParams",
    "AssetOptOutParams",
    "AssetTransferParams",
    "CommonTxnParams",
    "MethodCallParams",
    "OfflineKeyRegistrationParams",
    "OnlineKeyRegistrationParams",
    "PaymentParams",
    "TxnParams",
]


@dataclass(kw_only=True, frozen=True)
class CommonTxnParams:
    sender: str
    signer: TransactionSigner | AddressWithTransactionSigner | None = None
    rekey_to: str | None = None
    note: bytes | None = None
    lease: bytes | None = None
    static_fee: AlgoAmount | None = None
    extra_fee: AlgoAmount | None = None
    max_fee: AlgoAmount | None = None
    validity_window: int | None = None
    first_valid_round: int | None = None
    last_valid_round: int | None = None


@dataclass(kw_only=True, frozen=True)
class PaymentParams(CommonTxnParams):
    receiver: str
    amount: AlgoAmount
    close_remainder_to: str | None = None


@dataclass(kw_only=True, frozen=True)
class AssetCreateParams(CommonTxnParams):
    total: int
    asset_name: str | None = None
    unit_name: str | None = None
    url: str | None = None
    decimals: int | None = None
    default_frozen: bool | None = None
    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None
    metadata_hash: bytes | None = None


@dataclass(kw_only=True, frozen=True)
class AssetConfigParams(CommonTxnParams):
    asset_id: int
    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None


@dataclass(kw_only=True, frozen=True)
class AssetFreezeParams(CommonTxnParams):
    asset_id: int
    account: str
    frozen: bool


@dataclass(kw_only=True, frozen=True)
class AssetDestroyParams(CommonTxnParams):
    asset_id: int


@dataclass(kw_only=True, frozen=True)
class OnlineKeyRegistrationParams(CommonTxnParams):
    vote_key: str
    selection_key: str
    state_proof_key: bytes | None = None
    vote_first: int = 0
    vote_last: int = 0
    vote_key_dilution: int = 0
    nonparticipation: bool | None = None


@dataclass(kw_only=True, frozen=True)
class OfflineKeyRegistrationParams(CommonTxnParams):
    prevent_account_from_ever_participating_again: bool = True


@dataclass(kw_only=True, frozen=True)
class AssetTransferParams(CommonTxnParams):
    asset_id: int
    amount: int
    receiver: str
    close_asset_to: str | None = None
    clawback_target: str | None = None


@dataclass(kw_only=True, frozen=True)
class AssetOptInParams(CommonTxnParams):
    asset_id: int


@dataclass(kw_only=True, frozen=True)
class AssetOptOutParams(CommonTxnParams):
    asset_id: int
    creator: str


@dataclass(kw_only=True, frozen=True)
class AppCallParams(CommonTxnParams):
    app_id: int
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None
    on_complete: OnApplicationComplete | None = None


class AppCreateSchema(TypedDict):
    global_ints: int
    global_byte_slices: int
    local_ints: int
    local_byte_slices: int


@dataclass(kw_only=True, frozen=True)
class AppCreateParams(CommonTxnParams):
    approval_program: str | bytes
    clear_state_program: str | bytes
    schema: AppCreateSchema | None = None
    on_complete: OnApplicationComplete | None = None
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None
    extra_program_pages: int | None = None


@dataclass(kw_only=True, frozen=True)
class AppUpdateParams(CommonTxnParams):
    app_id: int
    approval_program: str | bytes
    clear_state_program: str | bytes
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None
    on_complete: OnApplicationComplete = OnApplicationComplete.UpdateApplication


@dataclass(kw_only=True, frozen=True)
class AppDeleteParams(CommonTxnParams):
    app_id: int
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None
    on_complete: OnApplicationComplete | None = None


@dataclass(kw_only=True, frozen=True)
class _BaseAppMethodCall(CommonTxnParams):
    app_id: int | None = None
    method: arc56.Method
    args: list | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None
    schema: AppCreateSchema | None = None
    on_complete: OnApplicationComplete | None = None
    extra_program_pages: int | None = None


@dataclass(kw_only=True, frozen=True)
class AppMethodCallParams(CommonTxnParams):
    app_id: int
    method: arc56.Method
    args: list[bytes] | None = None
    on_complete: OnApplicationComplete | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference | BoxIdentifier] | None = None


@dataclass(kw_only=True, frozen=True)
class AppCallMethodCallParams(_BaseAppMethodCall):
    app_id: int
    on_complete: OnApplicationComplete | None = None


@dataclass(kw_only=True, frozen=True)
class AppCreateMethodCallParams(_BaseAppMethodCall):
    approval_program: str | bytes
    clear_state_program: str | bytes
    schema: AppCreateSchema | None = None
    on_complete: OnApplicationComplete | None = None


@dataclass(kw_only=True, frozen=True)
class AppUpdateMethodCallParams(_BaseAppMethodCall):
    app_id: int
    approval_program: str | bytes
    clear_state_program: str | bytes
    on_complete: OnApplicationComplete = OnApplicationComplete.UpdateApplication


@dataclass(kw_only=True, frozen=True)
class AppDeleteMethodCallParams(_BaseAppMethodCall):
    app_id: int
    on_complete: OnApplicationComplete = OnApplicationComplete.DeleteApplication


MethodCallParams = (
    AppCallMethodCallParams | AppCreateMethodCallParams | AppUpdateMethodCallParams | AppDeleteMethodCallParams
)


TxnParams = Union[  # noqa: UP007
    PaymentParams,
    AssetCreateParams,
    AssetConfigParams,
    AssetFreezeParams,
    AssetDestroyParams,
    OnlineKeyRegistrationParams,
    AssetTransferParams,
    AssetOptInParams,
    AssetOptOutParams,
    AppCallParams,
    AppCreateParams,
    AppUpdateParams,
    AppDeleteParams,
    MethodCallParams,
    OfflineKeyRegistrationParams,
]
