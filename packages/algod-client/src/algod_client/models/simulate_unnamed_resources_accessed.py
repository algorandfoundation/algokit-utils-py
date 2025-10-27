from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .application_local_reference import ApplicationLocalReference
from .asset_holding_reference import AssetHoldingReference
from .box_reference import BoxReference


@dataclass(slots=True)
class SimulateUnnamedResourcesAccessed:
    """
    These are resources that were accessed by this group that would normally have caused
    failure, but were allowed in simulation. Depending on where this object is in the
    response, the unnamed resources it contains may or may not qualify for group resource
    sharing. If this is a field in SimulateTransactionGroupResult, the resources do qualify,
    but if this is a field in SimulateTransactionResult, they do not qualify. In order to
    make this group valid for actual submission, resources that qualify for group sharing
    can be made available by any transaction of the group; otherwise, resources must be
    placed in the same transaction which accessed them.
    """

    accounts: list[str] | None = field(
        default=None,
        metadata=wire("accounts"),
    )
    app_locals: list[ApplicationLocalReference] | None = field(
        default=None,
        metadata=wire(
            "app-locals",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ApplicationLocalReference, raw),
        ),
    )
    apps: list[int] | None = field(
        default=None,
        metadata=wire("apps"),
    )
    asset_holdings: list[AssetHoldingReference] | None = field(
        default=None,
        metadata=wire(
            "asset-holdings",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AssetHoldingReference, raw),
        ),
    )
    assets: list[int] | None = field(
        default=None,
        metadata=wire("assets"),
    )
    boxes: list[BoxReference] | None = field(
        default=None,
        metadata=wire(
            "boxes",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: BoxReference, raw),
        ),
    )
    extra_box_refs: int | None = field(
        default=None,
        metadata=wire("extra-box-refs"),
    )
