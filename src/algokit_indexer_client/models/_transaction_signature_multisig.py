# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from ._transaction_signature_multisig_subsignature import TransactionSignatureMultisigSubsignature


@dataclass(slots=True)
class TransactionSignatureMultisig:
    """
    structure holding multiple subsignatures.

    Definition:
    crypto/multisig.go : MultisigSig
    """

    subsignature: list[TransactionSignatureMultisigSubsignature] | None = field(
        default=None,
        metadata=wire(
            "subsignature",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: TransactionSignatureMultisigSubsignature, raw),
        ),
    )
    threshold: int | None = field(
        default=None,
        metadata=wire("threshold"),
    )
    version: int | None = field(
        default=None,
        metadata=wire("version"),
    )
