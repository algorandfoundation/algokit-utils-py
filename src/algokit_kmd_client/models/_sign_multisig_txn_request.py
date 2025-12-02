# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._multisig_sig import MultisigSig
from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class SignMultisigTxnRequest:
    """
    The request for `POST /v1/multisig/sign`
    """

    public_key: list[int] = field(
        default_factory=list,
        metadata=wire("public_key"),
    )
    transaction: bytes = field(
        default=b"",
        metadata=wire(
            "transaction",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    wallet_handle_token: str = field(
        default="",
        metadata=wire("wallet_handle_token"),
    )
    partial_multisig: MultisigSig | None = field(
        default=None,
        metadata=nested("partial_multisig", lambda: MultisigSig),
    )
    signer: list[int] | None = field(
        default=None,
        metadata=wire("signer"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
