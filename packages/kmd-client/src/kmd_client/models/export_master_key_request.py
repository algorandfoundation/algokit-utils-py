from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ExportMasterKeyRequest:
    """
    APIV1POSTMasterKeyExportRequest is the request for `POST /v1/master-key/export`
    """

    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
