from pydantic import BaseModel, ConfigDict, Field


class DryrunSourceSchema(BaseModel):
    """DryrunSource is TEAL source text that gets uploaded, compiled, and inserted into transactions or application state."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    field_name: str = Field(alias="field-name")
    source: str = Field(alias="source")
    txn_index: int = Field(alias="txn-index")
    app_id: int = Field(alias="app-index")
