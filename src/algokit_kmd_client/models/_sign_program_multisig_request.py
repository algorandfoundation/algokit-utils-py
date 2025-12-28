# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_common.serde import nested, wire

from ._multisig_sig import MultisigSig
from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class SignProgramMultisigRequest:
    """
    The request for `POST /v1/multisig/signprogram`
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
    public_key: bytes = field(
        default=b"",
        metadata=wire(
            "public_key",
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
    use_legacy_msig: bool | None = field(
        default=None,
        metadata=wire("use_legacy_msig"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
