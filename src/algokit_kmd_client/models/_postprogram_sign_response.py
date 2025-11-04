# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostprogramSignResponse:
    """
    APIV1POSTProgramSignResponse is the response to `POST /v1/data/sign`
    friendly:SignProgramResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
    sig: bytes | None = field(
        default=None,
        metadata=wire("sig"),
    )
