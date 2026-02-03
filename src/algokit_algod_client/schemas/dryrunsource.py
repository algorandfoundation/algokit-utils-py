from pydantic import BaseModel, ConfigDict, Field


class DryrunSourceSchema(BaseModel):
    """DryrunSource is TEAL source text that gets uploaded, compiled, and inserted into transactions or application state."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    field_name: str = Field(default=None, alias="field-name")
    source: str = Field(default=None, alias="source")
    txn_index: int = Field(default=None, alias="txn-index")
    app_index: int = Field(default=None, alias="app-index")
