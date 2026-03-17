from pydantic import BaseModel, ConfigDict, Field


class StateSchemaSchema(BaseModel):
    """Represents a \[apls\] local-state or \[apgs\] global-state schema. These schemas determine how much storage may be used in a local-state or global-state for an application. The more space used, the larger minimum balance must be maintained in the account holding the data."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    num_uint: int = Field(ge=0, le=64, alias="num-uint")
    num_byte_slice: int = Field(ge=0, le=64, alias="num-byte-slice")
