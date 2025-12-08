# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class MultisigSubsig:
    """
    MultisigSubsig is a struct that holds a pair of public key and signatures
    signatures may be empty
    """

    public_key: list[int] = field(
        default_factory=list,
        metadata=wire("pk"),
    )
    signature: list[int] | None = field(
        default=None,
        metadata=wire("s"),
    )
