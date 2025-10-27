from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class DeletekeyResponse:
    """
    APIV1DELETEKeyResponse is the response to `DELETE /v1/key`
    friendly:DeleteKeyResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
