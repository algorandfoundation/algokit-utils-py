# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostmultisigListResponse:
    """
    APIV1POSTMultisigListResponse is the response to `POST /v1/multisig/list`
    friendly:ListMultisigResponse
    """

    addresses: list[str] | None = field(
        default=None,
        metadata=wire("addresses"),
    )
    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
