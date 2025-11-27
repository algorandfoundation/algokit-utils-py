# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._account_participation import AccountParticipation
from ._application import Application
from ._application_local_state import ApplicationLocalState
from ._application_state_schema import ApplicationStateSchema
from ._asset import Asset
from ._asset_holding import AssetHolding
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class Account:
    """
    Account information at a given round.

    Definition:
    data/basics/userBalance.go : AccountData
    """

    address: str = field(
        default="",
        metadata=wire("address"),
    )
    amount: int = field(
        default=0,
        metadata=wire("amount"),
    )
    amount_without_pending_rewards: int = field(
        default=0,
        metadata=wire("amount-without-pending-rewards"),
    )
    min_balance: int = field(
        default=0,
        metadata=wire("min-balance"),
    )
    pending_rewards: int = field(
        default=0,
        metadata=wire("pending-rewards"),
    )
    rewards: int = field(
        default=0,
        metadata=wire("rewards"),
    )
    round_: int = field(
        default=0,
        metadata=wire("round"),
    )
    status: str = field(
        default="",
        metadata=wire("status"),
    )
    total_apps_opted_in: int = field(
        default=0,
        metadata=wire("total-apps-opted-in"),
    )
    total_assets_opted_in: int = field(
        default=0,
        metadata=wire("total-assets-opted-in"),
    )
    total_box_bytes: int = field(
        default=0,
        metadata=wire("total-box-bytes"),
    )
    total_boxes: int = field(
        default=0,
        metadata=wire("total-boxes"),
    )
    total_created_apps: int = field(
        default=0,
        metadata=wire("total-created-apps"),
    )
    total_created_assets: int = field(
        default=0,
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
    closed_at_round: int | None = field(
        default=None,
        metadata=wire("closed-at-round"),
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
    created_at_round: int | None = field(
        default=None,
        metadata=wire("created-at-round"),
    )
    deleted: bool | None = field(
        default=None,
        metadata=wire("deleted"),
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
