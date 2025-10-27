from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ImportMultisigRequest:
    """
    APIV1POSTMultisigImportRequest is the request for `POST /v1/multisig/import`
    """

    multisig_version: int | None = field(
        default=None,
        metadata=wire("multisig_version"),
    )
    pks: list[list[int]] | None = field(
        default=None,
        metadata=wire("pks"),
    )
    threshold: int | None = field(
        default=None,
        metadata=wire("threshold"),
    )
    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
