from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthCheckSchema(BaseModel):
    """A health check response."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    version: str = Field(default=None, alias="version")
    data: dict[str, Any] | None = Field(default=None, alias="data")
    round: int = Field(default=None, alias="round")
    is_migrating: bool = Field(default=None, alias="is-migrating")
    db_available: bool = Field(default=None, alias="db-available")
    message: str = Field(default=None, alias="message")
    errors: list[str] | None = Field(default=None, alias="errors")
