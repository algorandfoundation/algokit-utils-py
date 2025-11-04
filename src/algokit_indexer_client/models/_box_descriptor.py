# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BoxDescriptor:
    """
    Box descriptor describes an app box without a value.
    """

    name: bytes = field(
        metadata=wire("name"),
    )
