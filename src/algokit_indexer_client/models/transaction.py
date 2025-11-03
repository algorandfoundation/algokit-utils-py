# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .account_state_delta import AccountStateDelta
from .eval_delta_key_value import EvalDeltaKeyValue
from .transaction_application import TransactionApplication
from .transaction_asset_config import TransactionAssetConfig
from .transaction_asset_freeze import TransactionAssetFreeze
from .transaction_asset_transfer import TransactionAssetTransfer
from .transaction_heartbeat import TransactionHeartbeat
from .transaction_keyreg import TransactionKeyreg
from .transaction_payment import TransactionPayment
from .transaction_signature import TransactionSignature
from .transaction_state_proof import TransactionStateProof


@dataclass(slots=True)
class Transaction:
    """
    Contains all fields common to all transactions and serves as an envelope to all
    transactions type. Represents both regular and inner transactions.

    Definition:
    data/transactions/signedtxn.go : SignedTxn
    data/transactions/transaction.go : Transaction
    """

    fee: int = field(
        metadata=wire("fee"),
    )
    first_valid: int = field(
        metadata=wire("first-valid"),
    )
    last_valid: int = field(
        metadata=wire("last-valid"),
    )
    sender: str = field(
        metadata=wire("sender"),
    )
    tx_type: str = field(
        metadata=wire("tx-type"),
    )
    application_transaction: TransactionApplication | None = field(
        default=None,
        metadata=nested("application-transaction", lambda: TransactionApplication),
    )
    asset_config_transaction: TransactionAssetConfig | None = field(
        default=None,
        metadata=nested("asset-config-transaction", lambda: TransactionAssetConfig),
    )
    asset_freeze_transaction: TransactionAssetFreeze | None = field(
        default=None,
        metadata=nested("asset-freeze-transaction", lambda: TransactionAssetFreeze),
    )
    asset_transfer_transaction: TransactionAssetTransfer | None = field(
        default=None,
        metadata=nested("asset-transfer-transaction", lambda: TransactionAssetTransfer),
    )
    auth_addr: str | None = field(
        default=None,
        metadata=wire("auth-addr"),
    )
    close_rewards: int | None = field(
        default=None,
        metadata=wire("close-rewards"),
    )
    closing_amount: int | None = field(
        default=None,
        metadata=wire("closing-amount"),
    )
    confirmed_round: int | None = field(
        default=None,
        metadata=wire("confirmed-round"),
    )
    created_application_index: int | None = field(
        default=None,
        metadata=wire("created-application-index"),
    )
    created_asset_index: int | None = field(
        default=None,
        metadata=wire("created-asset-index"),
    )
    genesis_hash: bytes | None = field(
        default=None,
        metadata=wire("genesis-hash"),
    )
    genesis_id: str | None = field(
        default=None,
        metadata=wire("genesis-id"),
    )
    global_state_delta: list[EvalDeltaKeyValue] | None = field(
        default=None,
        metadata=wire(
            "global-state-delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: EvalDeltaKeyValue, raw),
        ),
    )
    group: bytes | None = field(
        default=None,
        metadata=wire("group"),
    )
    heartbeat_transaction: TransactionHeartbeat | None = field(
        default=None,
        metadata=nested("heartbeat-transaction", lambda: TransactionHeartbeat),
    )
    id_: str | None = field(
        default=None,
        metadata=wire("id"),
    )
    inner_txns: list["Transaction"] | None = field(
        default=None,
        metadata=wire(
            "inner-txns",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Transaction, raw),
        ),
    )
    intra_round_offset: int | None = field(
        default=None,
        metadata=wire("intra-round-offset"),
    )
    keyreg_transaction: TransactionKeyreg | None = field(
        default=None,
        metadata=nested("keyreg-transaction", lambda: TransactionKeyreg),
    )
    lease: bytes | None = field(
        default=None,
        metadata=wire("lease"),
    )
    local_state_delta: list[AccountStateDelta] | None = field(
        default=None,
        metadata=wire(
            "local-state-delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AccountStateDelta, raw),
        ),
    )
    logs: list[bytes] | None = field(
        default=None,
        metadata=wire("logs"),
    )
    note: bytes | None = field(
        default=None,
        metadata=wire("note"),
    )
    payment_transaction: TransactionPayment | None = field(
        default=None,
        metadata=nested("payment-transaction", lambda: TransactionPayment),
    )
    receiver_rewards: int | None = field(
        default=None,
        metadata=wire("receiver-rewards"),
    )
    rekey_to: str | None = field(
        default=None,
        metadata=wire("rekey-to"),
    )
    round_time: int | None = field(
        default=None,
        metadata=wire("round-time"),
    )
    sender_rewards: int | None = field(
        default=None,
        metadata=wire("sender-rewards"),
    )
    signature: TransactionSignature | None = field(
        default=None,
        metadata=nested("signature", lambda: TransactionSignature),
    )
    state_proof_transaction: TransactionStateProof | None = field(
        default=None,
        metadata=nested("state-proof-transaction", lambda: TransactionStateProof),
    )
