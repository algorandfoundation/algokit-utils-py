# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .transaction_signature_logicsig import TransactionSignatureLogicsig
from .transaction_signature_multisig import TransactionSignatureMultisig


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
        metadata=wire("sig"),
    )
