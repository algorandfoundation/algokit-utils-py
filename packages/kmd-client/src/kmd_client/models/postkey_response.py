from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostkeyResponse:
    """
    APIV1POSTKeyResponse is the response to `POST /v1/key`
    friendly:GenerateKeyResponse
    """

    address: str | None = field(
        default=None,
        metadata=wire("address"),
    )
    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
