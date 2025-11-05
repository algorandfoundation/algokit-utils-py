# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._multisig_sig import MultisigSig
from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class SignMultisigRequest:
    """
    APIV1POSTMultisigTransactionSignRequest is the request for `POST /v1/multisig/sign`
    """

    partial_multisig: MultisigSig | None = field(
        default=None,
        metadata=nested("partial_multisig", lambda: MultisigSig),
    )
    public_key: list[int] | None = field(
        default=None,
        metadata=wire("public_key"),
    )
    signer: list[int] | None = field(
        default=None,
        metadata=wire("signer"),
    )
    transaction: bytes | None = field(
        default=None,
        metadata=wire(
            "transaction",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
