# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_bytes, encode_bytes
from ._transaction_signature_logicsig import TransactionSignatureLogicsig
from ._transaction_signature_multisig import TransactionSignatureMultisig


@dataclass(slots=True)
class TransactionSignature:
    """
    Validation signature associated with some data. Only one of the signatures should be
    provided.
    """

    logicsig: TransactionSignatureLogicsig | None = field(
        default=None,
        metadata=nested("logicsig", lambda: TransactionSignatureLogicsig),
    )
    multisig: TransactionSignatureMultisig | None = field(
        default=None,
        metadata=nested("multisig", lambda: TransactionSignatureMultisig),
    )
    sig: bytes | None = field(
        default=None,
        metadata=wire(
            "sig",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
