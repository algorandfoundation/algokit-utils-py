# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import (
    decode_bytes,
    decode_bytes_sequence,
    decode_fixed_bytes,
    encode_bytes,
    encode_bytes_sequence,
    encode_fixed_bytes,
)
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
            encode=encode_bytes,
            decode=decode_bytes,
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
            encode=lambda v: encode_fixed_bytes(v, 64),
            decode=lambda raw: decode_fixed_bytes(raw, 64),
        ),
    )
