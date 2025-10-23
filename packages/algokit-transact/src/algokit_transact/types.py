from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TransactionType(Enum):
    Payment = "pay"
    AssetTransfer = "axfer"
    AssetFreeze = "afrz"
    AssetConfig = "acfg"
    KeyRegistration = "keyreg"
    AppCall = "appl"
    StateProof = "stpf"
    Heartbeat = "hb"


class OnApplicationComplete(Enum):
    NoOp = 0
    OptIn = 1
    CloseOut = 2
    ClearState = 3
    UpdateApplication = 4
    DeleteApplication = 5


@dataclass(slots=True, frozen=True)
class StateSchema:
    num_uints: int
    num_byte_slices: int


@dataclass(slots=True, frozen=True)
class PaymentFields:
    amount: int
    receiver: str
    close_remainder_to: str | None = None


@dataclass(slots=True, frozen=True)
class AssetTransferFields:
    asset_id: int
    amount: int
    receiver: str
    close_remainder_to: str | None = None
    asset_sender: str | None = None


@dataclass(slots=True, frozen=True)
class AssetConfigFields:
    asset_id: int
    total: int | None = None
    decimals: int | None = None
    default_frozen: bool | None = None
    unit_name: str | None = None
    asset_name: str | None = None
    url: str | None = None
    metadata_hash: bytes | None = None
    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None


@dataclass(slots=True, frozen=True)
class AppCallFields:
    app_id: int
    on_complete: OnApplicationComplete = OnApplicationComplete.NoOp
    approval_program: bytes | None = None
    clear_state_program: bytes | None = None
    global_state_schema: StateSchema | None = None
    local_state_schema: StateSchema | None = None
    args: tuple[bytes, ...] | None = None
    account_references: tuple[str, ...] | None = None
    app_references: tuple[int, ...] | None = None
    asset_references: tuple[int, ...] | None = None
    extra_program_pages: int | None = None


@dataclass(slots=True, frozen=True)
class KeyRegistrationFields:
    vote_key: bytes | None = None
    selection_key: bytes | None = None
    vote_first: int | None = None
    vote_last: int | None = None
    vote_key_dilution: int | None = None
    state_proof_key: bytes | None = None
    non_participation: bool | None = None


@dataclass(slots=True, frozen=True)
class AssetFreezeFields:
    asset_id: int
    freeze_target: str
    frozen: bool


@dataclass(slots=True, frozen=True)
class Transaction:
    transaction_type: TransactionType
    sender: str
    first_valid: int
    last_valid: int
    fee: int | None = None
    genesis_hash: bytes | None = None
    genesis_id: str | None = None
    note: bytes | None = None
    rekey_to: str | None = None
    lease: bytes | None = None
    group: bytes | None = None

    # one-of type-specific fields
    payment: PaymentFields | None = None
    asset_transfer: AssetTransferFields | None = None
    asset_config: AssetConfigFields | None = None
    app_call: AppCallFields | None = None
    key_registration: KeyRegistrationFields | None = None
    asset_freeze: AssetFreezeFields | None = None
    # StateProof / Heartbeat can be added later for full parity


@dataclass(slots=True, frozen=True)
class SignedTransaction:
    transaction: Transaction
    signature: bytes
