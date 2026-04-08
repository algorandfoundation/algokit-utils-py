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

    subsignatures: list[MultisigSubsig] = field(
        default_factory=list,
        metadata=wire(
            "subsig",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: MultisigSubsig, raw),
        ),
    )
    threshold: int = field(
        default=0,
        metadata=wire("thr"),
    )
    version: int = field(
        default=0,
        metadata=wire("v"),
    )
