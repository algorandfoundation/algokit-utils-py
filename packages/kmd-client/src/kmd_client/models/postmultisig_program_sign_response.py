from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostmultisigProgramSignResponse:
    """
    APIV1POSTMultisigProgramSignResponse is the response to `POST /v1/multisig/signdata`
    friendly:SignProgramMultisigResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
    multisig: bytes | None = field(
        default=None,
        metadata=wire("multisig"),
    )
