# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostmultisigTransactionSignResponse:
    """
    APIV1POSTMultisigTransactionSignResponse is the response to `POST /v1/multisig/sign`
    friendly:SignMultisigResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
    multisig: bytes | None = field(
        default=None,
        metadata=wire("multisig"),
    )
