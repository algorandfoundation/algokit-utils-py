from collections.abc import Mapping
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
    # Unknown transaction type - used when decoding transactions with unrecognized type values.
    # This should not be used when creating new transactions.
    Unknown = "unknown"


def _get_tx_type(payload: Mapping[str, object]) -> str | None:
    """Helper to extract transaction type from payload, normalizing bytes to str."""
    type_val = payload.get("type")
    if type_val is None:
        return None
    if isinstance(type_val, bytes | bytearray | memoryview):
        return bytes(type_val).decode("utf-8")
    return str(type_val)


@dataclass(slots=True, frozen=True)
class Transaction:
    transaction_type: TransactionType = field(
        metadata=enum_value("type", TransactionType, fallback=TransactionType.Unknown)
    )
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
        default=None, metadata=flatten(PaymentTransactionFields, present_if=lambda p: _get_tx_type(p) == "pay")
    )
    asset_transfer: AssetTransferTransactionFields | None = field(
        default=None, metadata=flatten(AssetTransferTransactionFields, present_if=lambda p: _get_tx_type(p) == "axfer")
    )
    asset_config: AssetConfigTransactionFields | None = field(
        default=None, metadata=flatten(AssetConfigTransactionFields, present_if=lambda p: _get_tx_type(p) == "acfg")
    )
    application_call: AppCallTransactionFields | None = field(
        default=None, metadata=flatten(AppCallTransactionFields, present_if=lambda p: _get_tx_type(p) == "appl")
    )
    key_registration: KeyRegistrationTransactionFields | None = field(
        default=None,
        metadata=flatten(KeyRegistrationTransactionFields, present_if=lambda p: _get_tx_type(p) == "keyreg"),
    )
    asset_freeze: AssetFreezeTransactionFields | None = field(
        default=None, metadata=flatten(AssetFreezeTransactionFields, present_if=lambda p: _get_tx_type(p) == "afrz")
    )
    heartbeat: HeartbeatTransactionFields | None = field(
        default=None, metadata=nested("hb", HeartbeatTransactionFields)
    )
    state_proof: StateProofTransactionFields | None = field(
        default=None, metadata=flatten(StateProofTransactionFields, present_if=lambda p: _get_tx_type(p) == "stpf")
    )

    def tx_id(self) -> str:
        """Return the transaction ID."""
        from algokit_transact.ops.ids import get_transaction_id

        return get_transaction_id(self)
