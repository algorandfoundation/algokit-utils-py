# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .multisig_sig import MultisigSig


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
        metadata=wire("transaction"),
    )
    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
