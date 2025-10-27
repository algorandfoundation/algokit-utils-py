from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ListKeysRequest:
    """
    APIV1POSTKeyListRequest is the request for `POST /v1/key/list`
    """

    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
