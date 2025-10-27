from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class GenerateKeyRequest:
    """
    APIV1POSTKeyRequest is the request for `POST /v1/key`
    """

    display_mnemonic: bool | None = field(
        default=None,
        metadata=wire("display_mnemonic"),
    )
    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
