from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .account_participation import AccountParticipation
from .application import Application
from .application_local_state import ApplicationLocalState
from .application_state_schema import ApplicationStateSchema
from .asset import Asset
from .asset_holding import AssetHolding


@dataclass(slots=True)
class Account:
    """
    Account information at a given round.

    Definition:
    data/basics/userBalance.go : AccountData
    """

    address: str = field(
        metadata=wire("address"),
    )
    amount: int = field(
        metadata=wire("amount"),
    )
    amount_without_pending_rewards: int = field(
        metadata=wire("amount-without-pending-rewards"),
    )
    min_balance: int = field(
        metadata=wire("min-balance"),
    )
    pending_rewards: int = field(
        metadata=wire("pending-rewards"),
    )
    rewards: int = field(
        metadata=wire("rewards"),
    )
    round_: int = field(
        metadata=wire("round"),
    )
    status: str = field(
        metadata=wire("status"),
    )
    total_apps_opted_in: int = field(
        metadata=wire("total-apps-opted-in"),
    )
    total_assets_opted_in: int = field(
        metadata=wire("total-assets-opted-in"),
    )
    total_created_apps: int = field(
        metadata=wire("total-created-apps"),
    )
    total_created_assets: int = field(
        metadata=wire("total-created-assets"),
    )
    apps_local_state: list[ApplicationLocalState] | None = field(
        default=None,
        metadata=wire(
            "apps-local-state",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationLocalState, raw),
        ),
    )
    apps_total_extra_pages: int | None = field(
        default=None,
        metadata=wire("apps-total-extra-pages"),
    )
    apps_total_schema: ApplicationStateSchema | None = field(
        default=None,
        metadata=nested("apps-total-schema", lambda: ApplicationStateSchema),
    )
    assets: list[AssetHolding] | None = field(
        default=None,
        metadata=wire(
            "assets",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AssetHolding, raw),
        ),
    )
    auth_addr: str | None = field(
        default=None,
        metadata=wire("auth-addr"),
    )
    created_apps: list[Application] | None = field(
        default=None,
        metadata=wire(
            "created-apps",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Application, raw),
        ),
    )
    created_assets: list[Asset] | None = field(
        default=None,
        metadata=wire(
            "created-assets",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Asset, raw),
        ),
    )
    incentive_eligible: bool | None = field(
        default=None,
        metadata=wire("incentive-eligible"),
    )
    last_heartbeat: int | None = field(
        default=None,
        metadata=wire("last-heartbeat"),
    )
    last_proposed: int | None = field(
        default=None,
        metadata=wire("last-proposed"),
    )
    participation: AccountParticipation | None = field(
        default=None,
        metadata=nested("participation", lambda: AccountParticipation),
    )
    reward_base: int | None = field(
        default=None,
        metadata=wire("reward-base"),
    )
    sig_type: str | None = field(
        default=None,
        metadata=wire("sig-type"),
    )
    total_box_bytes: int | None = field(
        default=None,
        metadata=wire("total-box-bytes"),
    )
    total_boxes: int | None = field(
        default=None,
        metadata=wire("total-boxes"),
    )
