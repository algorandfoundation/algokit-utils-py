# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ListMultisigResponse:
    """
    ListMultisigResponse is the response to `POST /v1/multisig/list`
    """

    addresses: list[str] = field(
        default_factory=list,
        metadata=wire("addresses"),
    )
