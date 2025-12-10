# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_bytes_base64, decode_bytes_sequence, encode_bytes_base64, encode_bytes_sequence
from ._transaction_signature_multisig import TransactionSignatureMultisig


@dataclass(slots=True)
class TransactionSignatureLogicsig:
    r"""
    \[lsig\] Programatic transaction signature.

    Definition:
    data/transactions/logicsig.go
    """

    logic: bytes = field(
        default=b"",
        metadata=wire(
            "logic",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    args: list[bytes] | None = field(
        default=None,
        metadata=wire(
            "args",
            encode=encode_bytes_sequence,
            decode=decode_bytes_sequence,
        ),
    )
    logic_multisig_signature: TransactionSignatureMultisig | None = field(
        default=None,
        metadata=nested("logic-multisig-signature", lambda: TransactionSignatureMultisig),
    )
    multisig_signature: TransactionSignatureMultisig | None = field(
        default=None,
        metadata=nested("multisig-signature", lambda: TransactionSignatureMultisig),
    )
    signature: bytes | None = field(
        default=None,
        metadata=wire(
            "signature",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
