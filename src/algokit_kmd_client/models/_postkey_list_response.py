# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostkeyListResponse:
    """
    APIV1POSTKeyListResponse is the response to `POST /v1/key/list`
    friendly:ListKeysResponse
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
