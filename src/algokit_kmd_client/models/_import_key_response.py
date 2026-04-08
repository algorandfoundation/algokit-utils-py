# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_common.serde import wire


@dataclass(slots=True)
class ImportKeyResponse:
    """
    ImportKeyResponse is the response to `POST /v1/key/import`
    """

    address: str = field(
        default=ZERO_ADDRESS,
        metadata=wire("address"),
    )
