# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ExportMasterKeyRequest:
    """
    The request for `POST /v1/master-key/export`
    """

    wallet_handle_token: str = field(
        default="",
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
