# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._multisig_sig import MultisigSig
from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class SignProgramMultisigRequest:
    """
    APIV1POSTMultisigProgramSignRequest is the request for `POST /v1/multisig/signprogram`
    """

    address: str | None = field(
        default=None,
        metadata=wire("address"),
    )
    data: bytes | None = field(
        default=None,
        metadata=wire(
            "data",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    partial_multisig: MultisigSig | None = field(
        default=None,
        metadata=nested("partial_multisig", lambda: MultisigSig),
    )
    public_key: list[int] | None = field(
        default=None,
        metadata=wire("public_key"),
    )
    use_legacy_msig: bool | None = field(
        default=None,
        metadata=wire("use_legacy_msig"),
    )
    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
