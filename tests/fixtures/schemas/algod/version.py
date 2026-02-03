from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class VersionSchema(BaseModel):
    """algod version information."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    build: "BuildVersionSchema" = Field(default=None, alias="build")
    genesis_hash_b64: str = Field(default=None, alias="genesis_hash_b64")
    genesis_id: str = Field(default=None, alias="genesis_id")
    versions: list[str] = Field(default=None, alias="versions")
