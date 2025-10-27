from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ExportKeyRequest:
    """
    APIV1POSTKeyExportRequest is the request for `POST /v1/key/export`
    """

    address: str | None = field(
        default=None,
        metadata=wire("address"),
    )
    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
