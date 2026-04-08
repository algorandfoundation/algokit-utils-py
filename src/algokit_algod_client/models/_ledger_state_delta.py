# AUTO-GENERATED: oas_generator
from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import addr, flatten, nested, wire

from ._block import Block
from ._serde_helpers import (
    decode_bytes_map_key,
    decode_model_sequence,
    encode_bytes,
    encode_model_sequence,
    mapping_decoder,
    mapping_encoder,
)

__all__ = [
    "LedgerAccountBaseData",
    "LedgerAccountData",
    "LedgerAccountDeltas",
    "LedgerAccountTotals",
    "LedgerAlgoCount",
    "LedgerAppLocalState",
    "LedgerAppLocalStateDelta",
    "LedgerAppParams",
    "LedgerAppParamsDelta",
    "LedgerAppResourceRecord",
    "LedgerAssetHolding",
    "LedgerAssetHoldingDelta",
    "LedgerAssetParams",
    "LedgerAssetParamsDelta",
    "LedgerAssetResourceRecord",
    "LedgerBalanceRecord",
    "LedgerIncludedTransactions",
    "LedgerKvValueDelta",
    "LedgerModifiedCreatable",
    "LedgerStateDelta",
    "LedgerStateDeltaForTransactionGroup",
    "LedgerStateSchema",
    "LedgerTealValue",
    "LedgerVotingData",
    "TransactionGroupLedgerStateDeltasForRound",
]


def _encode_bytes_key(key: object) -> str:
    if isinstance(key, bytes):
        return encode_bytes(key)
    if isinstance(key, memoryview | bytearray):
        return encode_bytes(bytes(key))
    raise TypeError("Ledger map keys must be bytes-like")


def _encode_numeric_key(key: object) -> str:
    if isinstance(key, bool):
        return str(int(key))
    if isinstance(key, int):
        return str(key)
    if isinstance(key, str):
        return str(int(key))
    raise TypeError("Ledger map keys must be numeric")


def _decode_numeric_key(key: object) -> int:
    if isinstance(key, int):
        return key
    if isinstance(key, str):
        return int(key)
    raise TypeError("Ledger map keys must be numeric")


@dataclass(slots=True)
class LedgerTealValue:
    """Type and value for TEAL key-value entries."""

    type: int = field(metadata=wire("tt", required=True))
    bytes_: bytes | None = field(default=None, metadata=wire("tb"))
    uint: int | None = field(default=None, metadata=wire("ui"))


@dataclass(slots=True)
class LedgerStateSchema:
    """Maximum counts for values stored in state."""

    num_uints: int | None = field(default=None, metadata=wire("nui"))
    num_byte_slices: int | None = field(default=None, metadata=wire("nbs"))


@dataclass(slots=True)
class LedgerAppParams:
    """Application parameters in ledger deltas."""

    approval_program: bytes = field(metadata=wire("approv", required=True))
    clear_state_program: bytes = field(metadata=wire("clearp", required=True))
    extra_program_pages: int | None = field(default=None, metadata=wire("epp"))
    version: int | None = field(default=None, metadata=wire("v"))
    size_sponsor: str | None = field(default=None, metadata=addr("ss"))
    local_state_schema: LedgerStateSchema | None = field(
        default=None, metadata=nested("lsch", lambda: LedgerStateSchema)
    )
    global_state_schema: LedgerStateSchema | None = field(
        default=None, metadata=nested("gsch", lambda: LedgerStateSchema)
    )
    global_state: dict[bytes, LedgerTealValue] | None = field(
        default=None,
        metadata=wire(
            "gs",
            encode=mapping_encoder(lambda: LedgerTealValue, key_encoder=_encode_bytes_key),
            decode=mapping_decoder(lambda: LedgerTealValue, key_decoder=decode_bytes_map_key),
        ),
    )


@dataclass(slots=True)
class LedgerAppLocalState:
    """Local state information for an application."""

    schema: LedgerStateSchema | None = field(default=None, metadata=nested("hsch", lambda: LedgerStateSchema))
    key_value: dict[bytes, LedgerTealValue] | None = field(
        default=None,
        metadata=wire(
            "tkv",
            encode=mapping_encoder(lambda: LedgerTealValue, key_encoder=_encode_bytes_key),
            decode=mapping_decoder(lambda: LedgerTealValue, key_decoder=decode_bytes_map_key),
        ),
    )


@dataclass(slots=True)
class LedgerAppLocalStateDelta:
    """Tracks changes to an application's local state."""

    deleted: bool = field(metadata=wire("Deleted", required=True))
    local_state: LedgerAppLocalState | None = field(
        default=None,
        metadata=nested("LocalState", lambda: LedgerAppLocalState),
    )


@dataclass(slots=True)
class LedgerAppParamsDelta:
    """Tracks changes to application parameters."""

    deleted: bool = field(metadata=wire("Deleted", required=True))
    params: LedgerAppParams | None = field(default=None, metadata=nested("Params", lambda: LedgerAppParams))


@dataclass(slots=True)
class LedgerAppResourceRecord:
    """App params and local state changes keyed by app and address."""

    app_id: int = field(metadata=wire("Aidx", required=True))
    address: str = field(metadata=addr("Addr"))
    params: LedgerAppParamsDelta = field(metadata=nested("Params", lambda: LedgerAppParamsDelta))
    state: LedgerAppLocalStateDelta = field(metadata=nested("State", lambda: LedgerAppLocalStateDelta))


@dataclass(slots=True)
class LedgerAssetHolding:
    """Asset holding details in ledger deltas."""

    amount: int | None = field(default=None, metadata=wire("a"))
    frozen: bool | None = field(default=None, metadata=wire("f"))


@dataclass(slots=True)
class LedgerAssetHoldingDelta:
    """Tracks a changed asset holding."""

    deleted: bool = field(metadata=wire("Deleted", required=True))
    holding: LedgerAssetHolding | None = field(default=None, metadata=nested("Holding", lambda: LedgerAssetHolding))


@dataclass(slots=True)
class LedgerAssetParams:
    """Asset parameters reflected in ledger deltas."""

    total: int = field(metadata=wire("t", required=True))
    decimals: int = field(metadata=wire("dc", required=True))
    default_frozen: bool | None = field(default=None, metadata=wire("df"))
    unit_name: str | None = field(default=None, metadata=wire("un"))
    asset_name: str | None = field(default=None, metadata=wire("an"))
    url: str | None = field(default=None, metadata=wire("au"))
    metadata_hash: bytes | None = field(default=None, metadata=wire("am"))
    manager: str | None = field(default=None, metadata=addr("m"))
    reserve: str | None = field(default=None, metadata=addr("r"))
    freeze: str | None = field(default=None, metadata=addr("f"))
    clawback: str | None = field(default=None, metadata=addr("c"))


@dataclass(slots=True)
class LedgerAssetParamsDelta:
    """Tracks updates to asset parameters."""

    deleted: bool = field(metadata=wire("Deleted", required=True))
    params: LedgerAssetParams | None = field(default=None, metadata=nested("Params", lambda: LedgerAssetParams))


@dataclass(slots=True)
class LedgerAssetResourceRecord:
    """Asset params and holding changes keyed by asset and address."""

    asset_id: int = field(metadata=wire("Aidx", required=True))
    address: str = field(metadata=addr("Addr"))
    params: LedgerAssetParamsDelta = field(metadata=nested("Params", lambda: LedgerAssetParamsDelta))
    holding: LedgerAssetHoldingDelta = field(metadata=nested("Holding", lambda: LedgerAssetHoldingDelta))


@dataclass(slots=True)
class LedgerVotingData:
    """Participation-related voting data."""

    vote_id: bytes = field(metadata=wire("VoteID", required=True))
    selection_id: bytes = field(metadata=wire("SelectionID", required=True))
    state_proof_id: bytes = field(metadata=wire("StateProofID", required=True))
    vote_first_valid: int = field(metadata=wire("VoteFirstValid", required=True))
    vote_last_valid: int = field(metadata=wire("VoteLastValid", required=True))
    vote_key_dilution: int = field(metadata=wire("VoteKeyDilution", required=True))


@dataclass(slots=True)
class LedgerAccountBaseData:
    """Base account data captured in ledger deltas."""

    status: int = field(metadata=wire("Status", required=True))
    micro_algos: int = field(metadata=wire("MicroAlgos", required=True))
    rewards_base: int = field(metadata=wire("RewardsBase", required=True))
    rewarded_micro_algos: int = field(metadata=wire("RewardedMicroAlgos", required=True))
    auth_address: str = field(metadata=addr("AuthAddr"))
    incentive_eligible: bool = field(metadata=wire("IncentiveEligible", required=True))
    total_app_schema: LedgerStateSchema = field(metadata=nested("TotalAppSchema", lambda: LedgerStateSchema))
    total_extra_app_pages: int = field(metadata=wire("TotalExtraAppPages", required=True))
    total_app_params: int = field(metadata=wire("TotalAppParams", required=True))
    total_app_local_states: int = field(metadata=wire("TotalAppLocalStates", required=True))
    total_asset_params: int = field(metadata=wire("TotalAssetParams", required=True))
    total_assets: int = field(metadata=wire("TotalAssets", required=True))
    total_boxes: int = field(metadata=wire("TotalBoxes", required=True))
    total_box_bytes: int = field(metadata=wire("TotalBoxBytes", required=True))
    last_proposed: int = field(metadata=wire("LastProposed", required=True))
    last_heartbeat: int = field(metadata=wire("LastHeartbeat", required=True))


@dataclass(slots=True)
class LedgerAccountData:
    """Aggregates base and voting data for an account."""

    account_base_data: LedgerAccountBaseData = field(metadata=flatten(lambda: LedgerAccountBaseData))
    voting_data: LedgerVotingData = field(metadata=flatten(lambda: LedgerVotingData))


@dataclass(slots=True)
class LedgerBalanceRecord:
    """Account data keyed by address."""

    address: str = field(metadata=addr("Addr"))
    account_data: LedgerAccountData = field(metadata=flatten(lambda: LedgerAccountData))


@dataclass(slots=True)
class LedgerAccountDeltas:
    """Account/app/asset updates included in a ledger delta."""

    accounts: list[LedgerBalanceRecord] | None = field(
        default=None,
        metadata=wire(
            "Accts",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: LedgerBalanceRecord, raw),
        ),
    )
    app_resources: list[LedgerAppResourceRecord] | None = field(
        default=None,
        metadata=wire(
            "AppResources",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: LedgerAppResourceRecord, raw),
        ),
    )
    asset_resources: list[LedgerAssetResourceRecord] | None = field(
        default=None,
        metadata=wire(
            "AssetResources",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: LedgerAssetResourceRecord, raw),
        ),
    )


@dataclass(slots=True)
class LedgerKvValueDelta:
    """Delta for a single key/value entry in the KV store."""

    data: bytes | None = field(default=None, metadata=wire("Data"))
    old_data: bytes | None = field(default=None, metadata=wire("OldData"))


@dataclass(slots=True)
class LedgerIncludedTransactions:
    """Transaction placement information."""

    last_valid: int = field(metadata=wire("LastValid", required=True))
    intra: int = field(metadata=wire("Intra", required=True))


@dataclass(slots=True)
class LedgerModifiedCreatable:
    """Changes to a creatable resource."""

    creatable_type: int = field(metadata=wire("Ctype", required=True))
    created: bool = field(metadata=wire("Created", required=True))
    creator: str = field(metadata=addr("Creator"))
    ndeltas: int = field(metadata=wire("Ndeltas", required=True))


@dataclass(slots=True)
class LedgerAlgoCount:
    """Totals for groups of accounts."""

    money: int = field(metadata=wire("mon", required=True))
    reward_units: int = field(metadata=wire("rwd", required=True))


@dataclass(slots=True)
class LedgerAccountTotals:
    """Aggregate Algo totals grouped by account status."""

    online: LedgerAlgoCount = field(metadata=nested("online", lambda: LedgerAlgoCount))
    offline: LedgerAlgoCount = field(metadata=nested("offline", lambda: LedgerAlgoCount))
    not_participating: LedgerAlgoCount = field(metadata=nested("notpart", lambda: LedgerAlgoCount))
    rewards_level: int = field(metadata=wire("rwdlvl", required=True))


@dataclass(slots=True)
class LedgerStateDelta:
    """State delta between rounds."""

    accounts: LedgerAccountDeltas = field(metadata=nested("Accts", lambda: LedgerAccountDeltas))
    block: Block = field(metadata=nested("Hdr", lambda: Block))
    state_proof_next: int = field(metadata=wire("StateProofNext", required=True))
    prev_timestamp: int = field(metadata=wire("PrevTimestamp", required=True))
    totals: LedgerAccountTotals = field(metadata=nested("Totals", lambda: LedgerAccountTotals))
    kv_mods: dict[bytes, LedgerKvValueDelta] | None = field(
        default=None,
        metadata=wire(
            "KvMods",
            encode=mapping_encoder(lambda: LedgerKvValueDelta, key_encoder=_encode_bytes_key),
            decode=mapping_decoder(lambda: LedgerKvValueDelta, key_decoder=decode_bytes_map_key),
        ),
    )
    tx_ids: dict[bytes, LedgerIncludedTransactions] | None = field(
        default=None,
        metadata=wire(
            "Txids",
            encode=mapping_encoder(lambda: LedgerIncludedTransactions, key_encoder=_encode_bytes_key),
            decode=mapping_decoder(lambda: LedgerIncludedTransactions, key_decoder=decode_bytes_map_key),
        ),
    )
    # NOTE: tx_leases field is intentionally omitted - msgpack maps with object keys are not supported
    creatables: dict[int, LedgerModifiedCreatable] | None = field(
        default=None,
        metadata=wire(
            "Creatables",
            encode=mapping_encoder(lambda: LedgerModifiedCreatable, key_encoder=_encode_numeric_key),
            decode=mapping_decoder(lambda: LedgerModifiedCreatable, key_decoder=_decode_numeric_key),
        ),
    )


@dataclass(slots=True)
class LedgerStateDeltaForTransactionGroup:
    """Ledger delta for a single transaction group."""

    delta: LedgerStateDelta = field(metadata=nested("Delta", lambda: LedgerStateDelta))
    ids: list[str] = field(metadata=wire("Ids", required=True))


@dataclass(slots=True)
class TransactionGroupLedgerStateDeltasForRound:
    """All ledger deltas for transaction groups in a round."""

    deltas: list[LedgerStateDeltaForTransactionGroup] = field(
        metadata=wire(
            "Deltas",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: LedgerStateDeltaForTransactionGroup, raw),
            required=True,
        )
    )
