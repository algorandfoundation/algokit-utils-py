from pydantic import BaseModel, ConfigDict, Field


class VersionSchema(BaseModel):
    """algod version information."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    build: "BuildVersionSchema" = Field(alias="build")
    genesis_hash_b64: str = Field(alias="genesis_hash_b64")
    genesis_id: str = Field(alias="genesis_id")
    versions: list[str] = Field(alias="versions")
