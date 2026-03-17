from pydantic import BaseModel, ConfigDict, Field


class EvalDeltaKeyValueSchema(BaseModel):
    """Key-value pairs for StateDelta."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    key: str = Field(alias="key")
    value: "EvalDeltaSchema" = Field(alias="value")
