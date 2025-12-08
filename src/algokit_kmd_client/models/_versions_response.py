# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class VersionsResponse:
    """
    VersionsResponse is the response to `GET /versions`
    friendly:VersionsResponse
    """

    versions: list[str] = field(
        default_factory=list,
        metadata=wire("versions"),
    )
