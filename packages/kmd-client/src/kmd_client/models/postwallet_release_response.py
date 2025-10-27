from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostwalletReleaseResponse:
    """
    APIV1POSTWalletReleaseResponse is the response to `POST /v1/wallet/release`
    friendly:ReleaseWalletHandleTokenResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
