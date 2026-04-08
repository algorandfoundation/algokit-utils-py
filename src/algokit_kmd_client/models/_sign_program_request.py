# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class SignProgramRequest:
    """
    The request for `POST /v1/program/sign`
    """

    address: str = field(
        default=ZERO_ADDRESS,
        metadata=wire("address"),
    )
    program: bytes = field(
        default=b"",
        metadata=wire(
            "data",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    wallet_handle_token: str = field(
        default="",
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
