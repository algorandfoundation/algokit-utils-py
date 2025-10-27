from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class DeletemultisigResponse:
    """
    APIV1DELETEMultisigResponse is the response to POST /v1/multisig/delete`
    friendly:DeleteMultisigResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
