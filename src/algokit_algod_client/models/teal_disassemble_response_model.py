# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class TealDisassembleResponseModel:
    result: str = field(
        metadata=wire("result"),
    )
