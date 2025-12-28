# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class CreateWalletRequest:
    """
    The request for `POST /v1/wallet`
    """

    wallet_name: str = field(
        default="",
        metadata=wire("wallet_name"),
    )
    wallet_password: str = field(
        default="",
        metadata=wire("wallet_password"),
    )
    master_derivation_key: bytes | None = field(
        default=None,
        metadata=wire(
            "master_derivation_key",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    wallet_driver_name: str | None = field(
        default="sqlite",
        metadata=wire("wallet_driver_name"),
    )
