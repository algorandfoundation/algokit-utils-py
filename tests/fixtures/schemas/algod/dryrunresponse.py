from pydantic import BaseModel, ConfigDict, Field


class DryrunResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txns: "list[DryrunTxnResultSchema]" = Field(alias="txns")
    error: str = Field(alias="error")
    protocol_version: str = Field(alias="protocol-version")
