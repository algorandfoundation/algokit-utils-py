# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class SignProgramRequest:
    """
    APIV1POSTProgramSignRequest is the request for `POST /v1/program/sign`
    """

    address: str | None = field(
        default=None,
        metadata=wire("address"),
    )
    data: bytes | None = field(
        default=None,
        metadata=wire("data"),
    )
    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
