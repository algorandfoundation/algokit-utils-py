# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._multisig_subsig import MultisigSubsig
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class MultisigSig:
    """
    MultisigSig is the structure that holds multiple Subsigs
    """

    subsigs: list[MultisigSubsig] | None = field(
        default=None,
        metadata=wire(
            "Subsigs",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: MultisigSubsig, raw),
        ),
    )
    threshold: int | None = field(
        default=None,
        metadata=wire("Threshold"),
    )
    version: int | None = field(
        default=None,
        metadata=wire("Version"),
    )
