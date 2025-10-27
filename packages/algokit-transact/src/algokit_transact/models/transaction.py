from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from algokit_common.constants import ZERO_ADDRESS

from algokit_transact.codec.serde import addr, enum_value, flatten, nested, wire
from algokit_transact.models.app_call import AppCallTransactionFields
from algokit_transact.models.asset_config import AssetConfigTransactionFields
from algokit_transact.models.asset_freeze import AssetFreezeTransactionFields
from algokit_transact.models.asset_transfer import AssetTransferTransactionFields
from algokit_transact.models.heartbeat import HeartbeatTransactionFields
from algokit_transact.models.key_registration import KeyRegistrationTransactionFields
from algokit_transact.models.payment import PaymentTransactionFields
from algokit_transact.models.state_proof import StateProofTransactionFields


class TransactionType(Enum):
    Payment = "pay"
    AssetTransfer = "axfer"
    AssetFreeze = "afrz"
    AssetConfig = "acfg"
    KeyRegistration = "keyreg"
    AppCall = "appl"
    StateProof = "stpf"
    Heartbeat = "hb"


@dataclass(slots=True, frozen=True)
class Transaction:
    transaction_type: TransactionType = field(metadata=enum_value("type", TransactionType))
    sender: str = field(default=ZERO_ADDRESS, metadata=addr("snd"))
    first_valid: int = field(default=0, metadata=wire("fv"))
    last_valid: int = field(default=0, metadata=wire("lv"))

    fee: int | None = field(default=None, metadata=wire("fee"))
    genesis_hash: bytes | None = field(default=None, metadata=wire("gh"))
    genesis_id: str | None = field(default=None, metadata=wire("gen"))
    note: bytes | None = field(default=None, metadata=wire("note"))
    rekey_to: str | None = field(default=None, metadata=addr("rekey"))
    lease: bytes | None = field(default=None, metadata=wire("lx"))
    group: bytes | None = field(default=None, metadata=wire("grp"))

    payment: PaymentTransactionFields | None = field(
        default=None, metadata=flatten(PaymentTransactionFields, present_if=lambda p: p.get("type") == "pay")
    )
    asset_transfer: AssetTransferTransactionFields | None = field(
        default=None, metadata=flatten(AssetTransferTransactionFields, present_if=lambda p: p.get("type") == "axfer")
    )
    asset_config: AssetConfigTransactionFields | None = field(
        default=None, metadata=flatten(AssetConfigTransactionFields, present_if=lambda p: p.get("type") == "acfg")
    )
    app_call: AppCallTransactionFields | None = field(
        default=None, metadata=flatten(AppCallTransactionFields, present_if=lambda p: p.get("type") == "appl")
    )
    key_registration: KeyRegistrationTransactionFields | None = field(
        default=None, metadata=flatten(KeyRegistrationTransactionFields, present_if=lambda p: p.get("type") == "keyreg")
    )
    asset_freeze: AssetFreezeTransactionFields | None = field(
        default=None, metadata=flatten(AssetFreezeTransactionFields, present_if=lambda p: p.get("type") == "afrz")
    )
    heartbeat: HeartbeatTransactionFields | None = field(
        default=None, metadata=nested("hb", HeartbeatTransactionFields)
    )
    state_proof: StateProofTransactionFields | None = field(
        default=None, metadata=flatten(StateProofTransactionFields, present_if=lambda p: p.get("type") == "stpf")
    )
