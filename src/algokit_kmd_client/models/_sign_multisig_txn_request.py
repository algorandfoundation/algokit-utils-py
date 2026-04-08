# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._multisig_sig import MultisigSig
from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class SignMultisigTxnRequest:
    """
    The request for `POST /v1/multisig/sign`
    """

    public_key: bytes = field(
        default=b"",
        metadata=wire(
            "public_key",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    transaction: bytes = field(
        default=b"",
        metadata=wire(
            "transaction",
            encode=encode_bytes,
            decode=decode_bytes,
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
    signer: bytes | None = field(
        default=None,
        metadata=wire(
            "signer",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
