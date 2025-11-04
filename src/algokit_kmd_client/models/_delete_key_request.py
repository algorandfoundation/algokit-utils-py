# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class DeleteKeyRequest:
    """
    APIV1DELETEKeyRequest is the request for `DELETE /v1/key`
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
